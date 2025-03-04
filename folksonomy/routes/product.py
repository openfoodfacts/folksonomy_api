

import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
import psycopg2

from folksonomy import db
from folksonomy.models import ProductList, ProductTag, User
from folksonomy.utils.auth import check_owner_user, get_current_user
from folksonomy.utils.query import property_where, sanitize_data

router = APIRouter()


@router.get("/products", response_model=List[ProductList])
async def product_list(response: Response,
                       owner='', k='', v='',
                       user: User = Depends(get_current_user)):
    """
    Get the list of products matching k or k=v
    """
    if k == '':
        return JSONResponse(status_code=422, content={"detail": {"msg": "missing value for k"}})
    check_owner_user(user, owner, allow_anonymous=True)
    k, v = sanitize_data(k, v)
    where, params = property_where(owner, k, v)
    cur, timing = await db.db_exec("""
        SELECT coalesce(json_agg(j.j)::json, '[]'::json) FROM(
            SELECT json_build_object(
                'product',product,
                'k',k,
                'v',v
                ) as j
            FROM folksonomy
            WHERE %s
            ) as j;
        """ % where,
                                   params
                                   )
    out = await cur.fetchone()
    return JSONResponse(status_code=200, content=out[0], headers={"x-pg-timing": timing})


@router.get("/product/{product}", response_model=List[ProductTag])
async def product_tags_list(response: Response,
                            product: str, owner='',
                            user: User = Depends(get_current_user)):
    """
    Get a list of existing tags for a product
    """

    check_owner_user(user, owner, allow_anonymous=True)
    cur, timing = await db.db_exec("""
        SELECT json_agg(j)::json FROM(
            SELECT * FROM folksonomy WHERE product = %s AND owner = %s ORDER BY k
            ) as j;
        """,
                                   (product, owner),
                                   )
    out = await cur.fetchone()
    return JSONResponse(status_code=200, content=out[0], headers={"x-pg-timing": timing})


@router.get("/product/{product}/{k}", response_model=ProductTag)
async def product_tag(response: Response,
                      product: str, k: str, owner='',
                      user: User = Depends(get_current_user)):
    """
    Get a specific tag or tag hierarchy on a product

    - /product/xxx/key returns only the requested key
    - /product/xxx/key* returns the key and subkeys (key:subkey)
    """
    k, v = sanitize_data(k, None)
    key = re.sub(r'[^a-z0-9_\:]', '', k)
    check_owner_user(user, owner, allow_anonymous=True)
    if k[-1:] == '*':
        cur, timing = await db.db_exec(
            """
            SELECT json_agg(j)::json FROM(
                SELECT *
                FROM folksonomy
                WHERE product = %s AND owner = %s AND k ~ %s
                ORDER BY k) as j;
            """,
            (product, owner, '^%s(:.|$)' % key),
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
    if out:
        return JSONResponse(status_code=200, content=out[0], headers={"x-pg-timing": timing})
    else:
        return JSONResponse(status_code=404, content=None)


@router.get("/product/{product}/{k}/versions", response_model=List[ProductTag])
async def product_tag_list_versions(response: Response,
                                    product: str, k: str, owner='',
                                    user: User = Depends(get_current_user)):
    """
    Get a list of all versions of a tag for a product
    """

    check_owner_user(user, owner, allow_anonymous=True)
    k, v = sanitize_data(k, None)
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
    return JSONResponse(status_code=200, content=out[0], headers={"x-pg-timing": timing})


@router.post("/product")
async def product_tag_add(response: Response,
                          product_tag: ProductTag,
                          user: User = Depends(get_current_user)):
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
        cur, timing = await db.db_exec(query, params)
    except psycopg2.Error as e:
        error_msg = re.sub(r'.*@@ (.*) @@\n.*$', r'\1', e.pgerror)[:-1]
        return JSONResponse(status_code=422, content={"detail": {"msg": error_msg}})

    if cur.rowcount == 1:
        return "ok"
    return


@router.put("/product")
async def product_tag_update(response: Response,
                             product_tag: ProductTag,
                             user: User = Depends(get_current_user)):
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
        req, params = db.update_product_tag_req(product_tag)
        cur, timing = await db.db_exec(req, params)
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=422,
            detail=re.sub(r'.*@@ (.*) @@\n.*$', r'\1', e.pgerror)[:-1],
        )
    if cur.rowcount == 1:
        return "ok"
    elif cur.rowcount == 0:  # non existing key
        raise HTTPException(
            status_code=404,
            detail="Key was not found",
        )
    else:
        raise HTTPException(
            status_code=503,
            detail="Doubious update - more than one row udpated",
        )


@router.delete("/product/{product}/{k}")
async def product_tag_delete(response: Response,
                             product: str, k: str, version: int, owner='',
                             user: User = Depends(get_current_user)):
    """
    Delete a product tag
    """
    check_owner_user(user, owner, allow_anonymous=False)
    k, v = sanitize_data(k, None)
    try:
        # Setting version to 0, this is seen as a reset,
        # while maintaining history in folksonomy_versions
        cur, timing = await db.db_exec(
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
            detail=re.sub(r'.*@@ (.*) @@\n.*$', r'\1', e.pgerror)[:-1],
        )
    if cur.rowcount != 1:
        raise HTTPException(
            status_code=422,
            detail="Unknown product/k/version for this owner",
        )
    cur, timing = await db.db_exec(
        """
        DELETE FROM folksonomy WHERE product = %s AND owner = %s AND k = %s AND version = 0;
        """,
        (product, owner, k.lower()),
    )
    if cur.rowcount == 1:
        return "ok"
    else:
        # we have a conflict, return an error explaining conflict
        cur, timing = await db.db_exec(
            """
            SELECT version FROM folksonomy WHERE product = %s AND owner = %s AND k = %s
            """,
            (product, owner, k)
        )
        if cur.rowcount == 1:
            out = await cur.fetchone()
            raise HTTPException(
                status_code=422,
                detail="version mismatch, last version for this product/k is %s" % out[0],
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Unknown product/k for this owner",
            )
