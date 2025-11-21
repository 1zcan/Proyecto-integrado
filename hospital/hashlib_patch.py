# hospital/hashlib_patch.py
import hashlib

# Guardar la referencia original
_real_md5 = hashlib.md5

def safe_md5(*args, **kwargs):
    # Eliminar el parámetro 'usedforsecurity' si viene
    kwargs.pop('usedforsecurity', None)
    return _real_md5(*args, **kwargs)

# Reemplazar hashlib.md5 por la versión "segura"
hashlib.md5 = safe_md5
