"""Receipts HTTP routes."""
from fastapi import APIRouter
from fastapi import HTTPException, UploadFile, File
from backend.app.api.schemas import ReceiptText, ReceiptCommit
from backend.app.services.receipt_scanning import parse_receipt, scan_receipt
from backend.app.services.receipt_registration import register_receipt, ReceiptValidationError

router = APIRouter(tags=["receipts"])


@router.post("/api/receipts/parse")
def api_parse_receipt(payload: ReceiptText):
    return parse_receipt(payload.text)



@router.post("/api/receipts/scan")
async def api_scan_receipt(image: UploadFile = File(...)):
    from starlette.concurrency import run_in_threadpool
    content = await image.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "La foto debe pesar menos de 10 MB.")
    try:
        return await run_in_threadpool(scan_receipt, content)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc



@router.post("/api/receipts/confirm")
def api_confirm_receipt(payload: ReceiptCommit):
    try:
        return register_receipt(payload.model_dump())
    except ReceiptValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
