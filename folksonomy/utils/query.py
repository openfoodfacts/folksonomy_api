"""Shared helpers for property keys and values."""


def strip_property_kv(k, v):
    """Strip surrounding whitespace from a property key and its optional value."""
    k = k.strip()
    v = v.strip() if v else v
    return k, v


def build_substring_pattern(q: str) -> str:
    """Build an ILIKE pattern matching ``q`` as a literal substring.

    ``%`` and ``_`` are wildcards in LIKE patterns and ``\\`` is the escape
    character, so escape all three in the user-supplied search string;
    the pattern is meant to be used with an explicit ``ESCAPE '\\'`` clause.
    """
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


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
