"""Conservative lexical relevance: product family, requested words and packaging."""
import re

SIZE = re.compile(r"\d+(?:\.\d+)?(?:ml|g)$")
ALIASES = {"leches":"leche", "galletas":"galletita", "galletitas":"galletita", "galleta":"galletita",
           "yogures":"yogur", "yogurt":"yogur", "yoghurt":"yogur", "fideos":"fideo",
           "quesos":"queso", "panes":"pan", "postres":"postre", "jabon":"jabon", "jabones":"jabon"}
FAMILIES = {"leche", "galletita", "arroz", "fideo", "queso", "yogur", "dulce", "postre", "flan",
            "helado", "chocolate", "bebida", "gaseosa", "jugo", "agua", "cafe", "yerba", "te", "pan",
            "manteca", "crema", "aceite", "detergente", "jabon", "lavandina", "shampoo", "acondicionador"}
MILK_VARIANTS = {"condensada", "polvo", "chocolatada", "saborizada", "infantil", "formula"}


def words(value):
    return [ALIASES.get(word, word) for word in value.split()]


def is_multipack(value):
    return bool(re.search(r"\b(?:pack|combo|fardo)\b|\bcaja\s+(?:de\s+)?[2-9]\d*\b|\b[2-9]\d*\s*[x×]\s*\d", value))


def matches_product(query, product, brand=""):
    requested = [w for w in words(query) if not SIZE.fullmatch(w)]
    product_words = words(product)
    if not requested or not set(requested).issubset(set(product_words) | set(words(brand))):
        return False
    family = next((w for w in requested if w in FAMILIES), None)
    product_family = next((w for w in product_words if w in FAMILIES), None)
    if family and product_family != family:
        return False
    if family:
        before = product_words[:product_words.index(family)]
        allowed_prefix = set(requested) | {"uat", "uht", "larga", "vida", "fresca", "entera", "descremada", "liviana"}
        if any(w not in allowed_prefix and not w.isdigit() and not SIZE.fullmatch(w) for w in before):
            return False
    # Plain milk must not become condensed milk, powder or a flavoured dessert.
    if family == "leche" and (set(product_words) & MILK_VARIANTS) - set(requested):
        return False
    if is_multipack(product) and not is_multipack(query):
        return False
    return True
