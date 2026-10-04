"""Shared helpers for property keys and values."""


def strip_property_kv(k, v):
    """Strip surrounding whitespace from a property key and its optional value."""
    k = k.strip()
    v = v.strip() if v else v
    return k, v


def build_property_filter(owner: str, k: str, v: str):
    """Build a SQL condition on a property, filtering by owner and eventually key and value"""
    conditions = ["owner=%s"]
    params = [owner]
    if k != "":
        conditions.append("k=%s")
        params.append(k)
        if v != "":
            conditions.append("v=%s")
            params.append(v)
    where = " AND ".join(conditions)
    return where, params
