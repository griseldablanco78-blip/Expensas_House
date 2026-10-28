"""Validate and register a reviewed ticket without coupling to HTTP."""
from backend.app.infrastructure.json_store import load_db, add_expense, locked
from backend.app.services.receipt_scanning import cents


class ReceiptValidationError(ValueError):
    pass


@locked
def register_receipt(payload):
    db = load_db()
    existing = next((e for e in db['expenses'] if e['id'] == payload["id"]), None)
    if existing:
        return {"status": "success", "expense": existing, "duplicate": True}
    for item in payload["items"]:
        if abs(cents(item["quantity"] * item["unit_price"]) - cents(item["line_total"])) > .02:
            raise ReceiptValidationError("Revisá cantidad, precio unitario y subtotal de cada producto.")
    subtotal = cents(sum(i['line_total'] for i in payload['items']))
    if abs(subtotal - payload["total"]) > .02 and not payload["adjustment_note"].strip():
        raise ReceiptValidationError("El total difiere de los productos. Indicá el descuento, impuesto o ajuste del ticket.")
    image = payload.get('receipt_image', '')
    if image:
        from backend.app.services.receipt_archive import image_path
        if not image_path(image).is_file():
            raise ReceiptValidationError('No se encontró la imagen del comprobante. Volvé a subirla.')
    expense = add_expense({"id": payload["id"], "amount": cents(payload["total"]),
        "category": payload["category"], "note": payload["store"],
        "items": payload["items"], "store": payload['store'],
        "purchase_date": str(payload['purchase_date']) if payload.get('purchase_date') else None,
        "raw_text": payload.get('raw_text', ''), "receipt_image": image,
        "adjustment_note": payload["adjustment_note"], "subtotal": subtotal, "source": "receipt"})
    return {"status": "success", "expense": expense, "duplicate": False}
