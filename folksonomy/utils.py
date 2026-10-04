"""Shared helpers for property keys and values."""


def strip_property_kv(k, v):
    """Strip surrounding whitespace from a property key and its optional value."""
    k = k.strip()
    v = v.strip() if v else v
    return k, v
