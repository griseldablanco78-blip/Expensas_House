"""Offers HTTP routes."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from backend.app.infrastructure import json_store as store
from backend.app.core.paths import PROJECT_ROOT
from PIL import Image, ImageOps, UnidentifiedImageError
from io import BytesIO
import secrets
import re
from backend.app.services.offers import compare_supermarket_offers

router = APIRouter(tags=["offers"])
IMAGE_DIR = PROJECT_ROOT / 'data' / 'product_images'


class SavedOfferEdit(BaseModel):
    product: str = Field(min_length=1, max_length=200)
    price: float = Field(gt=0, allow_inf_nan=False)
    store: str | None = Field(default=None, min_length=1, max_length=150)


@router.get('/api/offers/saved')
def saved_offers():
    return store.get_offers()


@router.post('/api/offers/saved')
def create_saved_offer(payload: SavedOfferEdit):
    if not payload.product.strip() or not payload.store or not payload.store.strip():
        raise HTTPException(422, 'Completá producto y supermercado.')
    return store.add_offer({'product': payload.product.strip(), 'store': payload.store.strip(),
                            'price': str(payload.price), 'saving': '', 'source': 'Oferta guardada'})


@router.patch('/api/offers/saved/{offer_id}')
def edit_saved_offer(offer_id: str, payload: SavedOfferEdit):
    if not payload.product.strip():
        raise HTTPException(422, 'Ingresá el nombre del producto.')
    with store.DB_LOCK:
        data = store.load_db()
        item = next((o for o in data['offers'] if o.get('id') == offer_id), None)
        if item is None:
            raise HTTPException(404, 'La oferta ya no está disponible.')
        item.update(product=payload.product.strip(), price=str(payload.price))
        if payload.store is not None:
            if not payload.store.strip():
                raise HTTPException(422, 'Ingresá el supermercado.')
            item['store'] = payload.store.strip()
        store.save_db(data)
    return {'message': 'Oferta actualizada.'}


@router.post('/api/offers/saved/{offer_id}/image')
async def upload_offer_image(offer_id: str, image: UploadFile = File(...)):
    raw = await image.read(6 * 1024 * 1024 + 1)
    if len(raw) > 6 * 1024 * 1024:
        raise HTTPException(413, 'La imagen debe pesar menos de 6 MB.')
    try:
        with Image.open(BytesIO(raw)) as original:
            if original.width * original.height > 20_000_000:
                raise ValueError('Imagen demasiado grande')
            photo = ImageOps.exif_transpose(original).convert('RGB')
            photo.thumbnail((1200, 1200))
            content = BytesIO()
            photo.save(content, format='JPEG', quality=88)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(422, 'Elegí una fotografía JPG, PNG o WebP válida.')
    with store.DB_LOCK:
        data = store.load_db()
        item = next((o for o in data['offers'] if o.get('id') == offer_id), None)
        if item is None:
            raise HTTPException(404, 'La oferta ya no está disponible.')
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        filename = secrets.token_hex(16) + '.jpg'
        (IMAGE_DIR / filename).write_bytes(content.getvalue())
        item['image_url'] = '/api/offers/images/' + filename
        store.save_db(data)
    return {'message': 'Fotografía guardada.', 'image_url': item['image_url']}


@router.get('/api/offers/images/{filename}')
def offer_image(filename: str):
    if not re.fullmatch(r'[a-f0-9]{32}\.jpg', filename) or not (IMAGE_DIR / filename).is_file():
        raise HTTPException(404, 'Imagen no disponible.')
    return FileResponse(IMAGE_DIR / filename, media_type='image/jpeg')


@router.get("/api/offers/compare")
def api_compare_offers(q: str = "leche", sort: str = "discount"):
    """Busca ofertas guardadas y del proveedor configurado, usando reglas y unidades equivalentes."""
    return compare_supermarket_offers(q, sort)



@router.get("/offers")
def api_android_remote_offers(q: str = ""):
    """
    Endpoint compatible directo con la interfaz Android Retrofit:
    SupermarketApi.kt -> @GET("offers") suspend fun getOffers(@Query("q") query: String): List<RemoteOffer>
    """
    comparison = compare_supermarket_offers(q or "leche")
    remote_offers = []
    for off in comparison.get("offers", []):
        remote_offers.append({
            "store": off.get("store", "Supermercado"),
            "name": off.get("product", q),
            "imageUrl": off.get("image_url", ""),
            "link": off.get("direct_link", ""),
            "brand": off.get("brand", "Genérica"),
            "price": f"${off.get('promo_price', 0):,.2f}",
            "discount": off.get("promo_text", "Oferta")
        })
    return remote_offers
