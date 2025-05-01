#! /usr/bin/python3

import asyncio
import contextlib
import logging
import logging.handlers
import re
import uuid
from typing import List, Optional

import aiohttp  # async requests to call OFF for login/password check
import psycopg2  # interface with postgresql
from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from . import db
from . import settings
from .models import (
    HelloResponse,
    KeyStats,
    PingResponse,
    ProductList,
    ProductStats,
    ProductTag,
    TokenResponse,
    User,
    ValueCount,
)
from .utils import *
from .knowledge_panels import router as knowledge_panels_router


description = """
Folksonomy Engine API allows you to add free property/value pairs to Open Food Facts products.

The API use the main following variables:
* **product**: the product number
* **k**: "key", meaning the property or tag
* **v**: "value", the value for a related key

## See also

* [Project page](https://wiki.openfoodfacts.org/Folksonomy_Engine)
* [Folksonomy Engine github repository](https://github.com/openfoodfacts/folksonomy_engine)
* [Documented properties](https://wiki.openfoodfacts.org/Folksonomy/Property)
"""


# Setup FastAPI app lifespan
@contextlib.asynccontextmanager
async def app_lifespan(app: FastAPI):
    async with app_logging():
        try:
            yield
        finally:
            await db.terminate()


app = FastAPI(
    title="Open Food Facts folksonomy REST API",
    description=description,
    lifespan=app_lifespan,
)

app.include_router(knowledge_panels_router)

# Allow anyone to call the API from their own apps
app.add_middleware(
    CORSMiddleware,
    # FastAPI doc related to allow_origin (to avoid CORS issues):
    # "It's also possible to declare the list as "*" (a "wildcard") to say that all are allowed.
    # But that will only allow certain types of communication, excluding everything that involves
    # credentials: Cookies, Authorization headers like those used with Bearer Tokens, etc.
    # So, for everything to work correctly, it's better to specify explicitly the allowed origins."
    # => Workarround: use allow_origin_regex
    # Source: https://github.com/tiangolo/fastapi/issues/133#issuecomment-646985050
    allow_origin_regex="https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# define route for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth", auto_error=False)


@contextlib.asynccontextmanager
async def app_logging():
    logger = logging.getLogger("uvicorn.access")
    handler = logging.handlers.RotatingFileHandler(
        "api.log", mode="a", maxBytes=100 * 1024, backupCount=3
    )
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    yield


@app.middleware("http")
async def initialize_transactions(request: Request, call_next):
    """middleware that enclose request processing in a transaction"""
    # eventually log user
    async with db.transaction():
        response = await call_next(request)
        return response


@app.get("/", status_code=status.HTTP_200_OK, response_model=HelloResponse)
async def hello():
    return {"message": "Hello folksonomy World! Tip: open /docs for documentation"}


def sanitize_data(k, v):
    """Some sanitization of data"""
    k = k.strip()
    v = v.strip() if v else v
    return k, v


def get_auth_server(request: Request):
    """
    Get auth server URL from request

    We deduce it by changing part of the request base URL
    according to FOLKSONOMY_PREFIX and AUTH_PREFIX settings
    """
    # For dev purposes, we can use a static auth server with AUTH_SERVER_STATIC
    # which can be specified in local_settings.py
    if hasattr(settings, "AUTH_SERVER_STATIC") and settings.AUTH_SERVER_STATIC:
        return settings.AUTH_SERVER_STATIC
    base_url = f"{request.base_url.scheme}://{request.base_url.netloc}"
    # remove folksonomy prefix and add AUTH prefix
    base_url = base_url.replace(
        settings.FOLKSONOMY_PREFIX or "", settings.AUTH_PREFIX or ""
    )
    return base_url


@app.post("/auth", response_model=TokenResponse)
@app.post("/auth_by_cookie", response_model=TokenResponse)
async def authentication_by_cookie(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Optional[str] = Cookie(None),
):
    """
    Authentication: provide user/password and get a bearer token in return

    - **username**: Open Food Facts user_id (not email)
    - **password**: user password (clear text, but HTTPS encrypted)

    token is returned, to be used in later requests with usual "Authorization: bearer token" headers
    """

    user_id = form_data.username
    password = form_data.password
    token = user_id + "__U" + str(uuid.uuid4())
    auth_url = get_auth_server(request) + "/cgi/auth.pl"
    auth_data = {"user_id": user_id, "password": password}
    async with aiohttp.ClientSession() as http_session:
        async with http_session.post(auth_url, data=auth_data) as resp:
            status_code = resp.status
    if status_code == 200:
        cur, timing = await db.db_exec(
            """
            DELETE FROM auth WHERE user_id = %s;
            INSERT INTO auth (user_id, token, last_use) VALUES (%s,%s,current_timestamp AT TIME ZONE 'GMT');
        """,
            (user_id, user_id, token),
        )
        if cur.rowcount == 1:
            return {"access_token": token, "token_type": "bearer"}
    elif status_code == 403:
        await asyncio.sleep(settings.FAILED_AUTH_WAIT_TIME)  # prevents brute-force
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer", "x-auth-url": auth_url},
        )
    elif status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid auth server: 404",
            headers={"WWW-Authenticate": "Bearer", "x-auth-url": auth_url},
        )
    raise HTTPException(status_code=500, detail="Server error")


@app.post("/auth_by_cookie", response_model=TokenResponse)
async def authentication(
    request: Request, response: Response, session: Optional[str] = Cookie(None)
):
    """
    Authentication: provide Open Food Facts session cookie and get a bearer token in return

    - **session cookie**: Open Food Facts session cookie

    token is returned, to be used in later requests with usual "Authorization: bearer token" headers
    """
    if not session or session == "":
        raise HTTPException(status_code=422, detail="Missing 'session' cookie")

    try:
        session_data = session.split("&")
        user_id = session_data[session_data.index("user_id") + 1]
        token = user_id + "__U" + str(uuid.uuid4())
    except (ValueError, IndexError):
        raise HTTPException(status_code=422, detail="Malformed 'session' cookie")

    auth_url = get_auth_server(request) + "/cgi/auth.pl"
    async with aiohttp.ClientSession() as http_session:
        async with http_session.post(auth_url, cookies={"session": session}) as resp:
            status_code = resp.status

    if status_code == 200:
        cur, timing = await db.db_exec(
            """
            DELETE FROM auth WHERE user_id = %s;
            INSERT INTO auth (user_id, token, last_use) VALUES (%s,%s,current_timestamp AT TIME ZONE 'GMT');
            """,
            (user_id, user_id, token),
        )
        if cur.rowcount == 1:
            return {"access_token": token, "token_type": "bearer"}
    elif status_code == 403:
        await asyncio.sleep(settings.FAILED_AUTH_WAIT_TIME)  # prevents brute-force
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(status_code=500, detail="Server error")


def property_where(owner: str, k: str, v: str):
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


@app.get("/products/stats", response_model=List[ProductStats])
async def product_stats(
    response: Response, owner="", k="", v="", user: User = Depends(get_current_user)
):
    """
    Get the list of products with tags statistics

    The products list can be limited to some tags (k or k=v)
    """
    check_owner_user(user, owner, allow_anonymous=True)
    k, v = sanitize_data(k, v)
    where, params = property_where(owner, k, v)
    cur, timing = await db.db_exec(
        """
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
        """
        % where,
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


@app.get("/products", response_model=List[ProductList])
async def product_list(
    response: Response, owner="", k="", v="", user: User = Depends(get_current_user)
):
    """
    Get the list of products matching k or k=v
    """
    if k == "":
        return JSONResponse(
            status_code=422, content={"detail": {"msg": "missing value for k"}}
        )
    check_owner_user(user, owner, allow_anonymous=True)
    k, v = sanitize_data(k, v)
    where, params = property_where(owner, k, v)
    cur, timing = await db.db_exec(
        """
        SELECT coalesce(json_agg(j.j)::json, '[]'::json) FROM(
            SELECT json_build_object(
                'product',product,
                'k',k,
                'v',v
                ) as j
            FROM folksonomy
            WHERE %s
            ) as j;
        """
        % where,
        params,
    )
    out = await cur.fetchone()

    return JSONResponse(
        status_code=200,
        content=out[0] if out and out[0] is not None else [],
        headers={"x-pg-timing": timing},
    )


@app.get("/product/{product}", response_model=List[ProductTag])
async def product_tags_list(
    response: Response,
    product: str,
    owner: str = "",
    keys: str = Query(
        None,
        description="Comma-separated list of keys to filter by. If not provided, all keys are returned.",
    ),
    user: User = Depends(get_current_user),
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


@app.get("/product/{product}/{k}", response_model=ProductTag)
async def product_tag(
    response: Response,
    product: str,
    k: str,
    owner="",
    user: User = Depends(get_current_user),
):
    """
    Get a specific tag or tag hierarchy on a product

    - /product/xxx/key returns only the requested key
    - /product/xxx/key* returns the key and subkeys (key:subkey)
    """
    k, v = sanitize_data(k, None)
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
            (product, owner, "^%s(:.|$)" % key),
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


@app.get("/product/{product}/{k}/versions", response_model=List[ProductTag])
async def product_tag_list_versions(
    response: Response,
    product: str,
    k: str,
    owner="",
    user: User = Depends(get_current_user),
):
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

    return JSONResponse(
        status_code=200,
        content=out[0] if out and out[0] is not None else [],
        headers={"x-pg-timing": timing},
    )



@app.post("/product")
async def product_tag_add(
    response: Response, product_tag: ProductTag, user: User = Depends(get_current_user)
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
        cur, timing = await db.db_exec(query, params)
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


@app.put("/product")
async def product_tag_update(
    response: Response, product_tag: ProductTag, user: User = Depends(get_current_user)
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
        cur, timing = await db.db_exec(
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
        cur, timing = await db.db_exec(req, params)
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


@app.delete("/product/{product}/{k}")
async def product_tag_delete(
    response: Response,
    product: str,
    k: str,
    version: int,
    owner="",
    user: User = Depends(get_current_user),
):
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
            detail=re.sub(r".*@@ (.*) @@\n.*$", r"\1", e.pgerror)[:-1],
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
            (product, owner, k),
        )
        if cur.rowcount == 1:
            out = await cur.fetchone()
            raise HTTPException(
                status_code=422,
                detail="version mismatch, last version for this product/k is %s"
                % out[0],
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Unknown product/k for this owner",
            )


@app.get("/keys", response_model=List[KeyStats])
async def keys_list(
    response: Response,
    q: Optional[str] = "",
    owner: str = "",
    user: User = Depends(get_current_user),
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


@app.get("/values/{k}", response_model=List[ValueCount])
async def get_unique_values(
    response: Response,
    k: str,
    owner: str = "",
    q: str = "",
    limit: int = 50,
    user: User = Depends(get_current_user),
):
    """
    Get the unique values of a given property and the corresponding number of products

    - **k**: The property key to get unique values for
    - **owner**: None or empty for public tags, or your own user_id
    - **q**: Filter values by a query string
    - **limit**: Maximum number of values to return (default: 50; max: 1000)
    """
    check_owner_user(user, owner, allow_anonymous=True)
    k, _ = sanitize_data(k, None)

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
    data = out[0] if out and out[0] is not None else []
    return JSONResponse(status_code=200, content=data, headers={"x-pg-timing": timing})


@app.get("/ping", response_model=PingResponse)
async def pong(response: Response):
    """
    Check server health
    """
    cur, timing = await db.db_exec("SELECT current_timestamp AT TIME ZONE 'GMT'", ())
    pong = await cur.fetchone()
    return {"ping": "pong @ %s" % pong[0]}
