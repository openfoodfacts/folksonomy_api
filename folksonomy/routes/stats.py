from fastapi import APIRouter, Response, Depends
from fastapi.responses import JSONResponse
from typing import List

from folksonomy import db
from folksonomy.models import KeyStats, ProductStats, User
from folksonomy.utils.auth import check_owner_user, get_current_user
from folksonomy.utils.query import property_where, sanitize_data

router = APIRouter()


@router.get("/products/stats", response_model=List[ProductStats])
async def product_stats(response: Response,
                        owner='', k='', v='',
                        user: User = Depends(get_current_user)):
    """
    Get the list of products with tags statistics

    The products list can be limited to some tags (k or k=v)
    """
    check_owner_user(user, owner, allow_anonymous=True)
    k, v = sanitize_data(k, v)
    where, params = property_where(owner, k, v)
    cur, timing = await db.db_exec("""
        SELECT json_agg(j.j)::json FROM(
            SELECT json_build_object(
                'product',product,
                'keys',count(*),
                'last_edit',max(last_edit),
                'editors',count(distinct(editor))
                ) as j
            FROM folksonomy
            WHERE %s
            GROUP BY product) as j;
        """ % where,
                                   params
                                   )
    out = await cur.fetchone()
    # cur, timing = await db.db_exec("""
    #     SELECT count(*)
    #         FROM folksonomy;
    #     """
    # )
    # out2 = await cur.fetchone()
    # import pdb;pdb.set_trace()
    return JSONResponse(status_code=200, content=out[0], headers={"x-pg-timing": timing})


@router.get("/keys", response_model=List[KeyStats])
async def keys_list(response: Response,
                    owner='',
                    user: User = Depends(get_current_user)):
    """
    Get the list of keys with statistics

    The keys list can be restricted to private tags from some owner
    """
    check_owner_user(user, owner, allow_anonymous=True)
    cur, timing = await db.db_exec(
        """
        SELECT json_agg(j.j)::json FROM(
            SELECT json_build_object(
                'k',k,
                'count',count(*),
                'values',count(distinct(v))
                ) as j
            FROM folksonomy
            WHERE owner=%s
            GROUP BY k
            ORDER BY count(*) DESC) as j;
        """,
        (owner,)
    )
    out = await cur.fetchone()
    return JSONResponse(status_code=200, content=out[0], headers={"x-pg-timing": timing})


@router.get("/values/{k}")
async def get_unique_values(response: Response,
                            k: str,
                            owner: str = '',
                            q: str = '',
                            limit: int = '',
                            user: User = Depends(get_current_user)):
    """
    Get the unique values of a given property and the corresponding number of products

    - **k**: The property key to get unique values for
    - **owner**: None or empty for public tags, or your own user_id
    - **q**: Filter values by a query string
    - **limit**: Maximum number of values to return (default: 50; max: 1000)
    """
    check_owner_user(user, owner, allow_anonymous=True)
    k, _ = sanitize_data(k, None)
    if not limit:
        limit = 50
    if limit > 1000:
        limit = 1000

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
    data = out[0] if out and out[0] else []
    return JSONResponse(status_code=200, content=data, headers={"x-pg-timing": timing})

