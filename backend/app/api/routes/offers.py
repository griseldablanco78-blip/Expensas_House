"""Offers HTTP routes."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, Response
from backend.app.infrastructure import cloud_storage
from pydantic import BaseModel, Field
from backend.app.infrastructure import json_store as store
from backend.app.core.paths import PROJECT_ROOT
from PIL import Image, ImageOps, UnidentifiedImageError
from io import BytesIO
import secrets
import re
from backend.app.services.offers import compare_supermarket_offers
from backend.app.services.product_image_similarity import catalog_image_previews, rank_catalog_images

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
        filename = secrets.token_hex(16) + '.jpg'
        if cloud_storage.enabled():
            cloud_storage.put('products/'+filename,content.getvalue())
        else:
            IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            (IMAGE_DIR / filename).write_bytes(content.getvalue())
        item['image_url'] = '/api/offers/images/' + filename
        store.save_db(data)
    return {'message': 'Fotografía guardada.', 'image_url': item['image_url']}


@router.get('/api/offers/images/{filename}')
def offer_image(filename: str):
    if not re.fullmatch(r'[a-f0-9]{32}\.jpg', filename):
        raise HTTPException(404, 'Imagen no disponible.')
    if cloud_storage.enabled():
        try:
            return Response(cloud_storage.get('products/'+filename), media_type='image/jpeg')
        except FileNotFoundError:
            raise HTTPException(404,'Imagen no disponible.')
    if not (IMAGE_DIR / filename).is_file():
        raise HTTPException(404,'Imagen no disponible.')
    return FileResponse(IMAGE_DIR / filename, media_type='image/jpeg')


@router.get("/api/offers/compare")
def api_compare_offers(q: str = "leche", sort: str = "price"):
    """Busca ofertas guardadas y del proveedor configurado, usando reglas y unidades equivalentes."""
    return compare_supermarket_offers(q, sort)


@router.post('/api/offers/compare-image')
async def api_compare_offers_by_image(q: str = Form(...), sort: str = Form('price'), image: UploadFile = File(...)):
    """Search catalogs by the OCR description, then compare their public product photos."""
    raw = await image.read(10 * 1024 * 1024 + 1)
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(413, 'La foto debe pesar menos de 10 MB.')
    try:
        comparison = compare_supermarket_offers(q, sort)
        warning = rank_catalog_images(raw, comparison['offers'])
        previews = catalog_image_previews(comparison['offers'])
        for index, preview in previews.items():
            comparison['offers'][index]['catalog_image_preview'] = preview
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    comparison['warning'] = ' '.join(filter(None, [comparison.get('warning'), warning]))
    comparison['visual_search'] = True
    # The winning offer remains the cheapest item among the text-matched catalog entries.
    return comparison



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
