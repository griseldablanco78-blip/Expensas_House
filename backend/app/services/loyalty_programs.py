"""Informational loyalty links, separate from observed prices and ranking."""
import re
import unicodedata

PROGRAMS = {
    'dia': ('Club Día', 'https://diaonline.supermercadosdia.com.ar/clubdia'),
    'coto': ('Comunidad Coto', 'https://www.comunidadcoto.com.ar/static/preguntas.html'),
    'carrefour': ('Mi Carrefour', 'https://www.micarrefour.com.ar/terminos-condiciones'),
    'vea': ('Vea Ahorro', 'https://www.vea.com.ar/faq-frecuentes'),
    'jumbo': ('Jumbo Más', 'https://www.jumbomas.com.ar/preguntas-frecuentes-jumbo-mas'),
}


def loyalty_information(store):
    key = ''.join(c for c in unicodedata.normalize('NFKD', str(store or '')) if not unicodedata.combining(c)).lower()
    for name, (program, url) in PROGRAMS.items():
        if re.search(r'\b' + name + r'\b', key):
            return {'loyalty_program': program, 'loyalty_url': url,
                    'loyalty_notice': f'Si sos miembro de {program}, podrías acceder a cupones o beneficios adicionales. Revisá vigencia, sucursal, medio de pago y condiciones. No se calculan beneficios personales en el precio mostrado; verificá si la promoción es acumulable.'}
    return {}
