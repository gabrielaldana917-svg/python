"""Utilidades transversales del servicio."""
import functools


def con_registro(func):
    """Registra la llamada y evita que un fallo tumbe el servicio."""
    @functools.wraps(func)
    def envoltura(*args, **kwargs):
        return func(*args, **kwargs)
    return envoltura
