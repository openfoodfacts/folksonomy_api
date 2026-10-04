"""Product statistics and key/value discovery routes."""

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from .. import db
from ..models import KeyStats, ProductStats, ValueCount
from ..utils.auth import CurrentUser, check_owner_user
from ..utils.query import build_property_filter, strip_property_kv

router = APIRouter()


@router.get("/products/stats", response_model=list[ProductStats], tags=["Products"])
async def product_stats(user: CurrentUser, response: Response, owner="", k="", v=""):
    """
    Get the list of products with tags statistics

    The products list can be limited to some tags (k or k=v)
    """
    check_owner_user(user, owner, allow_anonymous=True)
    k, v = strip_property_kv(k, v)
    where, params = build_property_filter(owner, k, v)
    cur, timing = await db.db_exec(
        f"""
        SELECT json_agg(j.j)::json FROM(
            SELECT json_build_object(
                'product',product,
                'keys',count(*),
                'last_edit',max(last_edit),
                'editors',count(distinct(editor))
                ) as j
            FROM folksonomy
            WHERE {where}
            GROUP BY product) as j;
        """,
        params,
    )
    out = await cur.fetchone()
    # cur, timing = await db.db_exec("""
    #     SELECT count(*)
    #         FROM folksonomy;
    #     """
    # )
    # out2 = await cur.fetchone()
    # import pdb;pdb.set_trace()

    return JSONResponse(
        status_code=200,
        content=out[0] if out and out[0] is not None else [],
        headers={"x-pg-timing": timing},
    )


@router.get("/keys", response_model=list[KeyStats], tags=["Keys & Values"])
async def keys_list(
    user: CurrentUser,
    response: Response,
    q: str | None = "",
    owner: str = "",
):
    """
    Get the list of keys with statistics, with an optional search filter.

    The keys list can be restricted to private tags from some owner
    """
    check_owner_user(user, owner, allow_anonymous=True)

    search_filter = "AND k ILIKE %s" if q else ""
    query = f"""
        SELECT json_agg(j)::json FROM (
            SELECT json_build_object(
                'k', k,
                'count', COUNT(*),
                'values', COUNT(distinct v)
            ) AS j
            FROM folksonomy
            WHERE owner = %s
            {search_filter}
            GROUP BY k
            ORDER BY count(*) DESC
        ) AS j;
    """

    query_params = [owner] + ([f"%{q}%"] if q else [])

    cur, timing = await db.db_exec(query, tuple(query_params))
    out = await cur.fetchone()

    return JSONResponse(
        status_code=200,
        content=out[0] if out and out[0] is not None else [],
        headers={"x-pg-timing": timing},
    )


@router.get("/values/{k}", response_model=list[ValueCount], tags=["Keys & Values"])
async def get_unique_values(
    user: CurrentUser,
    response: Response,
    k: str,
    owner: str = "",
    q: str = "",
    limit: int = 50,
):
    """
    Get the unique values of a given property and the corresponding number of products

    - **k**: The property key to get unique values for
    - **owner**: None or empty for public tags, or your own user_id
    - **q**: Filter values by a query string
    - **limit**: Maximum number of values to return (default: 50; max: 1000)
    """
    check_owner_user(user, owner, allow_anonymous=True)
    k, _ = strip_property_kv(k, None)

    limit = min(limit, 1000)

    sql = """
        SELECT json_agg(j.j)::json
        FROM (
            SELECT json_build_object(
                'v', v,
                'product_count', count(*)
            ) AS j
            FROM folksonomy
            WHERE owner=%s AND k=%s
    """
    params = [owner, k]

    if q:
        sql += " AND v ILIKE %s"
        params.append(f"%{q}%")

    sql += """
            GROUP BY v
            ORDER BY count(*) DESC
            LIMIT %s
        ) AS j;
    """
    params.append(limit)

    cur, timing = await db.db_exec(sql, params)
    out = await cur.fetchone()
    data = out[0] if out and out[0] is not None else []
    return JSONResponse(status_code=200, content=data, headers={"x-pg-timing": timing})


@router.get("/values", tags=["Keys & Values"])
async def get_values_by_codes_and_keys(
    user: CurrentUser,
    response: Response,
    codes: str | None = Query(
        None, description="Comma-separated list of product codes (barcodes)"
    ),
    keys: str | None = Query(None, description="Comma-separated list of property keys"),
    owner: str = "",
):
    """
    Get values for specified products and/or keys

    - **codes**: Comma-separated list of product codes (barcodes) to filter by
    - **keys**: Comma-separated list of property keys to filter by
    - **owner**: None or empty for public tags, or your own user_id

    At least one of 'code' or 'keys' must be provided. Maximum 1000 products and 1000 keys.
    """
    check_owner_user(user, owner, allow_anonymous=True)

    if not codes and not keys:
        raise HTTPException(
            status_code=422,
            detail="At least one of 'code' or 'keys' parameters must be provided",
        )

    codes_list = [c.strip() for c in codes.split(",")] if codes else None
    keys_list = [k.strip() for k in keys.split(",")] if keys else None

    if codes_list and len(codes_list) > 1000:
        raise HTTPException(status_code=422, detail="Maximum 1000 products allowed")

    if keys_list and len(keys_list) > 1000:
        raise HTTPException(status_code=422, detail="Maximum 1000 keys allowed")

    sql = """
        SELECT json_agg(j)::json FROM (
            SELECT json_build_object(
                'product', product,
                'k', k,
                'v', v,
                'owner', owner,
                'version', version,
                'editor', editor,
                'last_edit', last_edit
            ) AS j
            FROM folksonomy
            WHERE owner = %s
    """
    params = [owner]

    if codes_list:
        placeholders = ", ".join(["%s"] * len(codes_list))
        sql += f" AND product IN ({placeholders})"
        params.extend(codes_list)

    if keys_list:
        placeholders = ", ".join(["%s"] * len(keys_list))
        sql += f" AND k IN ({placeholders})"
        params.extend(keys_list)

    sql += " ORDER BY product, k) AS j;"

    cur, timing = await db.db_exec(sql, tuple(params))
    out = await cur.fetchone()

    return JSONResponse(
        status_code=200,
        content=out[0] if out and out[0] is not None else [],
        headers={"x-pg-timing": timing},
    )
