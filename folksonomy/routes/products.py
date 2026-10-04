"""Product discovery and product tag routes."""

import re

import psycopg2
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import JSONResponse

from .. import db
from ..dependencies import CurrentUser, check_owner_user
from ..models import ProductList, ProductStats, ProductTag
from ..utils import strip_property_kv

router = APIRouter()


def _property_where(owner: str, k: str, v: str):
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


@router.get("/products/stats", response_model=list[ProductStats], tags=["Products"])
async def product_stats(user: CurrentUser, response: Response, owner="", k="", v=""):
    """
    Get the list of products with tags statistics

    The products list can be limited to some tags (k or k=v)
    """
    check_owner_user(user, owner, allow_anonymous=True)
    k, v = strip_property_kv(k, v)
    where, params = _property_where(owner, k, v)
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


@router.get("/products", response_model=list[ProductList], tags=["Products"])
async def product_list(
    user: CurrentUser,
    response: Response,
    k: str,
    owner: str = "",
    v: str = "",
    code: str = Query(
        None, description="Comma-separated list of product code to filter by"
    ),
):
    """
    Get the list of products matching k or k=v, optionally filtered by specific product code

    - **k**: Property name (required)
    - **owner**: Owner filter (optional, default empty for public)
    - **v**: Property value filter (optional)
    - **code**: Comma-separated list of product code to filter by (optional)
    """
    check_owner_user(user, owner, allow_anonymous=True)
    k, v = strip_property_kv(k, v)
    where, params = _property_where(owner, k, v)

    # Add product ID filter if code is provided
    if code:
        product_code = [pid.strip() for pid in code.split(",") if pid.strip()]
        if product_code:
            placeholders = ", ".join(["%s"] * len(product_code))
            where += f" AND product IN ({placeholders})"
            params.extend(product_code)

    cur, timing = await db.db_exec(
        f"""
        SELECT coalesce(json_agg(j.j)::json, '[]'::json) FROM(
            SELECT json_build_object(
                'product',product,
                'k',k,
                'v',v
                ) as j
            FROM folksonomy
            WHERE {where}
            ) as j;
        """,
        params,
    )
    out = await cur.fetchone()

    return JSONResponse(
        status_code=200,
        content=out[0] if out and out[0] is not None else [],
        headers={"x-pg-timing": timing},
    )


@router.get(
    "/product/{product}", response_model=list[ProductTag], tags=["Product Tags"]
)
async def product_tags_list(
    user: CurrentUser,
    response: Response,
    product: str,
    owner: str = "",
    keys: str = Query(
        None,
        description="Comma-separated list of keys to filter by. If not provided, all keys are returned.",
    ),
):
    """
    Get a list of existing tags for a product, optionally filtering by specific keys.
    """

    check_owner_user(user, owner, allow_anonymous=True)
    keys_list = [key.strip() for key in keys.split(",")] if keys else None

    placeholders = ", ".join(["%s"] * len(keys_list)) if keys_list else ""

    query = f"""
        SELECT json_agg(j)::json FROM (
            SELECT * FROM folksonomy
            WHERE product = %s AND owner = %s
            {f"AND k IN ({placeholders})" if keys_list else ""}
            ORDER BY k
        ) as j;
    """

    params = [product, owner] + (keys_list if keys_list else [])

    cur, timing = await db.db_exec(query, tuple(params))
    out = await cur.fetchone()

    return JSONResponse(
        status_code=200,
        content=out[0] if out and out[0] is not None else [],
        headers={"x-pg-timing": timing},
    )


@router.get("/product/{product}/{k}", response_model=ProductTag, tags=["Product Tags"])
async def product_tag(
    user: CurrentUser,
    response: Response,
    product: str,
    k: str,
    owner="",
):
    """
    Get a specific tag or tag hierarchy on a product

    - /product/xxx/key returns only the requested key
    - /product/xxx/key* returns the key and subkeys (key:subkey)
    """
    k, _v = strip_property_kv(k, None)
    key = re.sub(r"[^a-z0-9_\:]", "", k)
    check_owner_user(user, owner, allow_anonymous=True)
    if k[-1:] == "*":
        cur, timing = await db.db_exec(
            """
            SELECT json_agg(j)::json FROM(
                SELECT *
                FROM folksonomy
                WHERE product = %s AND owner = %s AND k ~ %s
                ORDER BY k) as j;
            """,
            (product, owner, f"^{key}(:.|$)"),
        )
    else:
        cur, timing = await db.db_exec(
            """
            SELECT row_to_json(j) FROM(
                SELECT *
                FROM folksonomy
                WHERE product = %s AND owner = %s AND k = %s
                ) as j;
            """,
            (product, owner, key),
        )
    out = await cur.fetchone()

    return JSONResponse(
        status_code=200,
        content=out[0] if out and out[0] is not None else [],
        headers={"x-pg-timing": timing},
    )


@router.get(
    "/product/{product}/{k}/versions",
    response_model=list[ProductTag],
    tags=["Product Tags"],
)
async def product_tag_list_versions(
    user: CurrentUser,
    response: Response,
    product: str,
    k: str,
    owner="",
):
    """
    Get a list of all versions of a tag for a product
    """

    check_owner_user(user, owner, allow_anonymous=True)
    k, _v = strip_property_kv(k, None)
    cur, timing = await db.db_exec(
        """
        SELECT json_agg(j)::json FROM(
            SELECT *
            FROM folksonomy_versions
            WHERE product = %s AND owner = %s AND k = %s
            ORDER BY version DESC
            ) as j;
        """,
        (product, owner, k),
    )
    out = await cur.fetchone()

    return JSONResponse(
        status_code=200,
        content=out[0] if out and out[0] is not None else [],
        headers={"x-pg-timing": timing},
    )


@router.post("/product", tags=["Product Tags"])
async def product_tag_add(
    user: CurrentUser, response: Response, product_tag: ProductTag
):
    """
    Create a new product tag (version=1)

    - **product**: which product
    - **k**: which key for the tag
    - **v**: which value to set for the tag
    - **version**: none or empty or 1
    - **owner**: none or empty for public tags, or your own user_id

    Be aware it's not possible to create the same tag twice. Though, you can update
    a tag and add multiple values the way you want (don't forget to document how); comma
    separated list is a good option.
    """
    check_owner_user(user, product_tag.owner, allow_anonymous=False)
    # enforce user
    product_tag.editor = user.user_id
    # note: version is checked by postgres routine
    try:
        query, params = db.create_product_tag_req(product_tag)
        cur, _timing = await db.db_exec(query, params)
    except psycopg2.Error as e:
        error_msg = re.sub(r".*@@ (.*) @@\n.*$", r"\1", e.pgerror)[:-1]
        if "duplicate key value violates unique constraint" in e.pgerror:
            return JSONResponse(
                status_code=422,
                content={
                    "detail": {
                        "msg": "Version conflict for this product (might result from a concurrent edit)"
                    }
                },
            )
        return JSONResponse(status_code=422, content={"detail": {"msg": error_msg}})

    if cur.rowcount == 1:
        return "ok"
    return


def _create_version_error(expected_version: int, received_version: int):
    return HTTPException(
        status_code=422,
        detail=[
            {
                "type": "value_error",
                "loc": ["body", "version"],
                "msg": f"Value error, version must be exactly {expected_version}",
                "input": received_version,
            }
        ],
    )


@router.put("/product", tags=["Product Tags"])
async def product_tag_update(
    user: CurrentUser, response: Response, product_tag: ProductTag
):
    """
    Update a product tag

    - **product**: which product
    - **k**: which key for the tag
    - **v**: which value to set for the tag
    - **version**: must be equal to previous version + 1
    - **owner**: None or empty for public tags, or your own user_id
    """
    check_owner_user(user, product_tag.owner, allow_anonymous=False)
    # enforce user
    product_tag.editor = user.user_id
    try:
        # Fetch the latest version directly from the database
        cur, _timing = await db.db_exec(
            """
            SELECT version FROM folksonomy
            WHERE product = %s AND owner = %s AND k = %s;
            """,
            (product_tag.product, product_tag.owner, product_tag.k),
        )
        latest_version_row = await cur.fetchone()

        if not latest_version_row:
            raise HTTPException(status_code=404, detail="Key was not found")

        latest_version = latest_version_row[0]  # Extract version from row

        # Validate version increment
        if product_tag.version != latest_version + 1:
            raise _create_version_error(latest_version + 1, product_tag.version)

        req, params = db.update_product_tag_req(product_tag)
        cur, _timing = await db.db_exec(req, params)
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=422,
            detail=re.sub(r".*@@ (.*) @@\n.*$", r"\1", e.pgerror)[:-1],
        )
    # Check if exactly one row was updated
    # Atlease one row will be updated, as version is checked
    if cur.rowcount == 1:
        return "ok"
    else:
        raise HTTPException(
            status_code=503,
            detail="Dubious update - more than one row udpated",
        )


@router.delete("/product/{product}/{k}", tags=["Product Tags"])
async def product_tag_delete(
    user: CurrentUser,
    response: Response,
    product: str,
    k: str,
    version: int,
    owner="",
):
    """
    Delete a product tag
    """
    check_owner_user(user, owner, allow_anonymous=False)
    k, _v = strip_property_kv(k, None)
    try:
        # Setting version to 0, this is seen as a reset,
        # while maintaining history in folksonomy_versions
        cur, _timing = await db.db_exec(
            """
            UPDATE folksonomy SET version = 0, editor = %s, comment = 'DELETE'
                WHERE product = %s AND owner = %s AND k = %s AND version = %s;
            """,
            (user.user_id, product, owner, k, version),
        )
    except psycopg2.Error as e:
        # note: transaction will be rolled back by the middleware
        raise HTTPException(
            status_code=422,
            detail=re.sub(r".*@@ (.*) @@\n.*$", r"\1", e.pgerror)[:-1],
        )
    if cur.rowcount != 1:
        raise HTTPException(
            status_code=422,
            detail="Unknown product/k/version for this owner",
        )
    cur, _timing = await db.db_exec(
        """
        DELETE FROM folksonomy WHERE product = %s AND owner = %s AND k = %s AND version = 0;
        """,
        (product, owner, k.lower()),
    )
    if cur.rowcount == 1:
        return "ok"
    else:
        # we have a conflict, return an error explaining conflict
        cur, _timing = await db.db_exec(
            """
            SELECT version FROM folksonomy WHERE product = %s AND owner = %s AND k = %s
            """,
            (product, owner, k),
        )
        if cur.rowcount == 1:
            out = await cur.fetchone()
            raise HTTPException(
                status_code=422,
                detail=f"version mismatch, last version for this product/k is {out[0]}",
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Unknown product/k for this owner",
            )
