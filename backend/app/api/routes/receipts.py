"""Receipts HTTP routes."""
from typing import Literal
from fastapi import APIRouter
from fastapi.responses import FileResponse, Response
from backend.app.infrastructure.json_store import get_expenses
from backend.app.services.receipt_archive import archive_image, image_path, image_exists, read_image
from backend.app.infrastructure import cloud_storage
from fastapi import HTTPException, UploadFile, File, Form
from backend.app.api.schemas import ReceiptText, ReceiptCommit
from backend.app.services.receipt_scanning import parse_receipt, scan_receipt
from backend.app.services.receipt_registration import register_receipt, ReceiptValidationError

router = APIRouter(tags=["receipts"])


@router.post("/api/receipts/parse")
def api_parse_receipt(payload: ReceiptText):
    return parse_receipt(payload.text)



@router.post("/api/receipts/scan")
async def api_scan_receipt(image: UploadFile = File(...), preprocessing: Literal["standard", "adaptive"] = "standard"):
    if cloud_storage.enabled():
        raise HTTPException(409, 'Esta versión requiere leer la foto en el dispositivo. Usá el escáner web actualizado o pegá el texto del ticket.')
    from starlette.concurrency import run_in_threadpool
    content = await image.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "La foto debe pesar menos de 10 MB.")
    try:
        result = await run_in_threadpool(scan_receipt, content, preprocessing)
        result['receipt_image'] = await run_in_threadpool(archive_image, content)
        return result
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except OSError as exc:
        raise HTTPException(503, "No se pudo archivar el comprobante. Revisá el almacenamiento del servidor.") from exc



@router.post('/api/receipts/draft')
async def api_receipt_draft(text: str = Form(...), image: UploadFile | None = File(default=None)):
    from starlette.concurrency import run_in_threadpool
    if len(text) > 100000:
        raise HTTPException(413, 'Texto demasiado largo.')
    result = parse_receipt(text)
    if image:
        raw = await image.read(3_500_001)
        if len(raw) > 3_500_000:
            raise HTTPException(413, 'La imagen preparada supera 3,5 MB.')
        try:
            result['receipt_image'] = await run_in_threadpool(archive_image,raw)
        except (ValueError,OSError) as error:
            raise HTTPException(400,'La fotografía no es válida.') from error
    result['ocr'] = {'location':'device','review_required':True}
    return result


@router.post("/api/receipts/confirm")
def api_confirm_receipt(payload: ReceiptCommit):
    try:
        return register_receipt(payload.model_dump())
    except ReceiptValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def registered_receipt(expense_id):
    expense = next((e for e in get_expenses() if e['id'] == expense_id), None)
    if expense is None:
        raise HTTPException(404, 'Comprobante no encontrado.')
    return expense


@router.get('/api/receipts/{expense_id}/text')
def download_receipt_text(expense_id: str):
    expense = registered_receipt(expense_id)
    lines = ['Expensa House - Comprobante de gasto',
             'Supermercado: ' + (expense.get('store') or expense.get('note', '')),
             'Fecha: ' + str(expense.get('purchase_date') or ''),
             'Total: ' + str(expense['amount']),
             'IVA informado: ' + str(expense.get('vat_amount') if expense.get('vat_amount') is not None else 'No informado'),
             'IVA incluido: ' + ('Sí' if expense.get('vat_included', True) else 'No'), '', 'Detalle revisado:']
    lines.extend(f"{i['description']} | {i['quantity']} x {i['unit_price']} - descuento {i.get('discount', 0)} = neto {i['line_total']} | {i.get('detail', '')}" for i in expense.get('items', []))
    lines.extend(['', 'Texto reconocido (puede contener errores):', expense.get('raw_text', '')])
    return Response('\n'.join(lines), media_type='text/plain; charset=utf-8',
                    headers={'Content-Disposition': 'attachment; filename="comprobante.txt"'})


@router.get('/api/receipts/{expense_id}/image')
def download_receipt_image(expense_id: str):
    expense = registered_receipt(expense_id)
    identity = expense.get('receipt_image')
    if not identity or not image_exists(identity):
        raise HTTPException(404, 'Este gasto no tiene imagen archivada.')
    return Response(read_image(identity), media_type='image/jpeg', headers={'Content-Disposition':'attachment; filename="comprobante.jpg"'})
