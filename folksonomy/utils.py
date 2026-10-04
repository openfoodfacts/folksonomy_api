"""Shared helpers for property keys and values."""


def sanitize_data(k, v):
    """Some sanitization of data"""
    k = k.strip()
    v = v.strip() if v else v
    return k, v
