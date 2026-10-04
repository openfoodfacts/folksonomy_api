import contextlib
import logging
import logging.handlers

import psycopg2  # interface with postgresql
from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import db, settings
from .dependencies import (
    CurrentUser,
    check_moderator_permission,
    check_owner_user,
)
from .models import (
    HelloResponse,
    KeyStats,
    PingResponse,
    PropertyClashCheck,
    PropertyClashCheckRequest,
    PropertyDeleteRequest,
    PropertyRenameRequest,
    ValueCount,
    ValueDeleteRequest,
    ValueRenameRequest,
)
from .routes import auth, products
from .utils import strip_property_kv

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
    servers=settings.API_SERVERS,
    openapi_tags=[
        {"name": "System", "description": "System health and general API information"},
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints",
        },
        {"name": "Products", "description": "Product discovery and statistics"},
        {
            "name": "Product Tags",
            "description": "CRUD operations for product tags and properties",
        },
        {
            "name": "Keys & Values",
            "description": "Browse available keys and their possible values",
        },
    ],
)

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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


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


@app.get(
    "/", status_code=status.HTTP_200_OK, response_model=HelloResponse, tags=["System"]
)
async def hello():
    return {"message": "Hello folksonomy World! Tip: open /docs for documentation"}


app.include_router(auth.router)


app.include_router(products.router)


@app.get("/keys", response_model=list[KeyStats], tags=["Keys & Values"])
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


@app.get("/values/{k}", response_model=list[ValueCount], tags=["Keys & Values"])
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


@app.get("/values", tags=["Keys & Values"])
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


@app.get("/ping", response_model=PingResponse, tags=["System"])
async def pong(response: Response):
    """
    Check server health
    """
    cur, _timing = await db.db_exec("SELECT current_timestamp AT TIME ZONE 'GMT'", ())
    pong = await cur.fetchone()
    return {"ping": f"pong @ {pong[0]}"}


@app.post(
    "/admin/property/check-clash",
    response_model=PropertyClashCheck,
    tags=["Admin - Property Management"],
)
async def check_property_clash(user: CurrentUser, request: PropertyClashCheckRequest):
    """
    Check for potential clashes when renaming a property

    Returns information about products that would be affected by the rename:
    - **old_property**: The current property name
    - **new_property**: The target property name

    Returns counts and list of conflicting products where both properties exist
    """
    await check_moderator_permission(user)

    # Check if old_property exists
    cur, timing = await db.db_exec(
        """
        SELECT COUNT(*) FROM folksonomy
        WHERE k = %s AND owner = ''
        """,
        (request.old_property,),
    )
    old_property_count = (await cur.fetchone())[0]
    if old_property_count == 0:
        raise HTTPException(
            status_code=404, detail=f"Property '{request.old_property}' not found"
        )

    # Find products that have both properties
    cur, timing = await db.db_exec(
        """
        SELECT
            old_prop.product,
            old_prop.v as old_value,
            new_prop.v as new_value
        FROM
            (SELECT product, v FROM folksonomy WHERE k = %s AND owner = '') as old_prop
        INNER JOIN
            (SELECT product, v FROM folksonomy WHERE k = %s AND owner = '') as new_prop
        ON old_prop.product = new_prop.product
        """,
        (request.old_property, request.new_property),
    )
    conflicting_products = await cur.fetchall()

    # Count products with only old property
    cur, timing = await db.db_exec(
        """
        SELECT COUNT(*) FROM folksonomy
        WHERE k = %s AND owner = ''
        AND product NOT IN (
            SELECT product FROM folksonomy WHERE k = %s AND owner = ''
        )
        """,
        (request.old_property, request.new_property),
    )
    old_only_count = (await cur.fetchone())[0]

    # Count products with only new property
    cur, timing = await db.db_exec(
        """
        SELECT COUNT(*) FROM folksonomy
        WHERE k = %s AND owner = ''
        AND product NOT IN (
            SELECT product FROM folksonomy WHERE k = %s AND owner = ''
        )
        """,
        (request.new_property, request.old_property),
    )
    new_only_count = (await cur.fetchone())[0]

    # Format conflicting products list
    conflicts = []
    for conflict in conflicting_products:
        conflicts.append(
            {
                "product": conflict[0],
                "old_value": conflict[1],
                "new_value": conflict[2],
            }
        )

    return JSONResponse(
        status_code=200,
        content=PropertyClashCheck(
            products_with_both=len(conflicting_products),
            products_with_old_only=old_only_count,
            products_with_new_only=new_only_count,
            conflicting_products=conflicts,
        ).model_dump(),
        headers={"x-pg-timing": timing},
    )


@app.post("/admin/property/rename", tags=["Admin - Property Management"])
async def rename_property(user: CurrentUser, request: PropertyRenameRequest):
    """
    Rename a property across all products

    When renaming a property that already exists:
    - If both properties have the same value: keep one entry
    - If both properties have different values: keep the original property's value

    - **old_property**: The current property name
    - **new_property**: The target property name
    """
    await check_moderator_permission(user)

    try:
        # Check if old_property exists
        cur, timing = await db.db_exec(
            """
            SELECT COUNT(*) FROM folksonomy
            WHERE k = %s AND owner = ''
            """,
            (request.old_property,),
        )
        old_property_count = (await cur.fetchone())[0]
        if old_property_count == 0:
            raise HTTPException(
                status_code=404, detail=f"Property '{request.old_property}' not found"
            )

        # Start transaction for all operations
        # First, handle products that have both properties
        cur, timing = await db.db_exec(
            """
            DELETE FROM folksonomy
            WHERE k = %s AND owner = ''
            AND product IN (
                SELECT product FROM folksonomy WHERE k = %s AND owner = ''
            )
            """,
            (request.old_property, request.new_property),
        )
        deleted_conflicting = cur.rowcount

        # Now rename all remaining instances of old_property to new_property
        # Need to increment version as required by the trigger
        cur, timing = await db.db_exec(
            """
            UPDATE folksonomy
            SET k = %s, editor = %s, version = version + 1
            WHERE k = %s AND owner = ''
            """,
            (request.new_property, user.user_id, request.old_property),
        )
        renamed_count = cur.rowcount

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "renamed_products": renamed_count,
                "conflicting_products_resolved": deleted_conflicting,
                "message": f"Renamed property '{request.old_property}' to '{request.new_property}'",
            },
            headers={"x-pg-timing": timing},
        )

    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Database error during property rename: {e!s}"
        ) from e


@app.delete("/admin/property", tags=["Admin - Property Management"])
async def delete_property(
    user: CurrentUser,
    response: Response,
    request: PropertyDeleteRequest,
):
    """
    Delete a property from all products

    - **property**: The property name to delete
    """
    await check_moderator_permission(user)

    property_name, _ = strip_property_kv(request.property, None)

    try:
        # Delete all instances of the property
        cur, timing = await db.db_exec(
            """
            DELETE FROM folksonomy
            WHERE k = %s AND owner = ''
            """,
            (property_name,),
        )
        deleted_count = cur.rowcount

        if deleted_count == 0:
            raise HTTPException(
                status_code=404, detail=f"Property '{property_name}' not found"
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "deleted_entries": deleted_count,
                "message": f"Deleted property '{property_name}' from {deleted_count} products",
            },
            headers={"x-pg-timing": timing},
        )

    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Database error during property deletion: {e!s}"
        ) from e


@app.post("/admin/value/replace", tags=["Admin - Value Management"])
async def replace_value(user: CurrentUser, request: ValueRenameRequest):
    """
    Replace a value for a specific property across all products

    - **property**: The property name
    - **old_value**: The value to replace
    - **new_value**: The new value
    """
    await check_moderator_permission(user)

    try:
        cur, timing = await db.db_exec(
            """
            UPDATE folksonomy
            SET v = %s, editor = %s, version = version + 1
            WHERE k = %s AND v = %s AND owner = ''
            """,
            (request.new_value, user.user_id, request.property, request.old_value),
        )
        renamed_count = cur.rowcount

        if renamed_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Value '{request.old_value}' not found for property '{request.property}'",
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "renamed_products": renamed_count,
                "message": f"Renamed value '{request.old_value}' to '{request.new_value}' for property '{request.property}' ({renamed_count} changes)",
            },
            headers={"x-pg-timing": timing},
        )

    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Database error during value rename: {e!s}"
        ) from e


@app.delete("/admin/value", tags=["Admin - Value Management"])
async def delete_value(user: CurrentUser, request: ValueDeleteRequest):
    """
    Delete a specific value for a property from all products

    - **property**: The property name
    - **value**: The value to delete
    """
    await check_moderator_permission(user)

    try:
        # Delete all instances of the specific value for this property
        cur, timing = await db.db_exec(
            """
            DELETE FROM folksonomy
            WHERE k = %s AND v = %s AND owner = ''
            """,
            (request.property, request.value),
        )
        deleted_count = cur.rowcount

        if deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Value '{request.value}' not found for property '{request.property}'",
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "deleted_entries": deleted_count,
                "message": f"Deleted value '{request.value}' for property '{request.property}' from {deleted_count} products",
            },
            headers={"x-pg-timing": timing},
        )

    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Database error during value deletion: {e!s}"
        ) from e
