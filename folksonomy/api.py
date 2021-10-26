#! /usr/bin/python3

from .dependencies import *

app = FastAPI(title="Open Food Facts folksonomy REST API")
# define route for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth", auto_error=False)


@app.on_event("startup")
async def startup():
    global db, cur
    db = psycopg2.connect("dbname=folksonomy")
    db.set_session(autocommit=True)
    cur = db.cursor()


@app.on_event("shutdown")
async def shutdown():
    db.close()


@app.get("/", status_code=status.HTTP_200_OK)
async def hello():
    return {"message": "Hello folksonomy World"}


async def db_exec(query, params = ()):
    """
    Execute postgresql query and collect timing
    """
    t = time.time()
    cur.execute(cur.mogrify(query, params))
    return str(round(time.time()-t, 4)*1000)+"ms"


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get current user and check token validity if present
    """
    if token and '__U' in token:
        query = cur.mogrify(
            "UPDATE auth SET last_use = current_timestamp AT TIME ZONE 'GMT' WHERE token = %s", (token,))
        cur.execute(query)
        if cur.rowcount == 1:
            return token.split('__U')[0]


def check_owner_user(user, owner, allow_anonymous=False):
    """
    Check authentication depending on current user and 'owner' of the data
    """
    if user is None and allow_anonymous == False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if owner != '':
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for '%s'" % owner,
                headers={"WWW-Authenticate": "Bearer"},
            )
        if owner != user:
            raise HTTPException(
                status_code=422,
                detail="owner should be '%s' or '' for public, but '%s' is authenticated" % (
                    owner, user),
            )
    return


@app.post("/auth")
async def authentication(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authentication: provide user/password and get a bearer token in return

    - **username** : Open Food Facts user_id (not email)
    - **password** : user password (clear text, but HTTPS encrypted)

    token is returned, to be used in later requests with usual "Authorization: bearer token" headers
    """

    user_id = form_data.username
    password = form_data.password
    token = user_id+'__U'+str(uuid.uuid4())
    r = requests.post("https://world.openfoodfacts.org/cgi/auth.pl",
                      data={'user_id': user_id, 'password': password})
    if r.status_code == 200:
        timing = await db_exec("""
DELETE FROM auth WHERE user_id = %s;
INSERT INTO auth (user_id, token, last_use) VALUES (%s,%s,current_timestamp AT TIME ZONE 'GMT');
        """, (user_id, user_id, token))
        if cur.rowcount == 1:
            return {"access_token": token, "token_type": "bearer"}
    elif r.status_code == 403:
        time.sleep(2)   # prevents brute-force
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(
        status_code=500, detail="Server error")


@app.post("/auth_by_cookie")
async def authentication(response: Response, session: Optional[str] = Cookie(None)):
    """
    Authentication: provide Open Food Facts session cookie and get a bearer token in return

    - **session cookie** : Open Food Facts session cookie

    token is returned, to be used in later requests with usual "Authorization: bearer token" headers
    """

    if not session or session =='':
        raise HTTPException(
            status_code=422, detail="Mission 'session' cookie")

    try:
        user_id = session.split('&')[-1]
        token = user_id+'__U'+str(uuid.uuid4())
    except:
        raise HTTPException(
            status_code=422, detail="Malformed 'session' cookie")

    r = requests.post("https://world.openfoodfacts.org/cgi/auth.pl",
                      cookies={'session': session})
    if r.status_code == 200:
        timing = await db_exec("""
DELETE FROM auth WHERE user_id = %s;
INSERT INTO auth (user_id, token, last_use) VALUES (%s,%s,current_timestamp AT TIME ZONE 'GMT');
        """, (user_id, user_id, token))
        if cur.rowcount == 1:
            return {"access_token": token, "token_type": "bearer"}
    elif r.status_code == 403:
        time.sleep(2)   # prevents brute-force
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(
        status_code=500, detail="Server error")


@app.get("/products/stats", response_model=List[ProductStats])
async def product_stat(response: Response,
                       owner='', k='', v='',
                       user: User = Depends(get_current_user)):
    """
    Get the list of products with tags statistics

    The products list can be limited to some tags (k or k=v)
    """

    check_owner_user(user, owner, allow_anonymous=True)
    where = cur.mogrify(' owner=%s ', (owner,))
    if k != '':
        where = where + cur.mogrify(' AND k=%s ', (k,))
        if v != '':
            where = where + cur.mogrify(' AND v=%s ', (v,))
    timing = await db_exec("""
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
""" % where.decode(), None)
    out = cur.fetchone()
    return JSONResponse(status_code=200, content=out[0], headers={"x-pg-timing":timing})


@app.get("/products", response_model=List[ProductStats])
async def product_list(response: Response,
                       owner='', k='', v='',
                       user: User = Depends(get_current_user)):
    """
    Get the list of products matching k or k=v
    """

    check_owner_user(user, owner, allow_anonymous=True)
    where = cur.mogrify(' owner=%s ', (owner,))
    if k != '':
        where = where + cur.mogrify(' AND k=%s ', (k,))
        if v != '':
            where = where + cur.mogrify(' AND v=%s ', (v,))
    timing = await db_exec("""
SELECT json_agg(j.j)::json FROM(
    SELECT json_build_object(
        'product',product,
        'keys',k,
        'value',v
        ) as j
    FROM folksonomy 
    WHERE %s
    ) as j;
""" % where.decode(), None)
    out = cur.fetchone()
    return JSONResponse(status_code=200, content=out[0], headers={"x-pg-timing":timing})


@app.get("/product/{product}", response_model=List[ProductTag])
async def product_tags_list(response: Response,
                            product: str, owner='',
                            user: User = Depends(get_current_user)):
    """
    Get a list of existing tags for a product
    """

    check_owner_user(user, owner, allow_anonymous=True)
    timing = await db_exec("""
SELECT json_agg(j)::json FROM(
    SELECT * FROM folksonomy WHERE product = %s AND owner = %s ORDER BY k
    ) as j;
""", (product, owner))
    out = cur.fetchone()
    return JSONResponse(status_code=200, content=out[0], headers={"x-pg-timing": timing})


@app.get("/product/{product}/{k}", response_model=ProductTag)
async def product_tag(response: Response,
                      product: str, k: str, owner='',
                      user: User = Depends(get_current_user)):
    """
    Get a specific tag or tag hierarchy on a product

    - /product/xxx/key returns only the requested key
    - /product/xxx/key* returns the key and subkeys (key:subkey)
    """

    key = re.sub(r'[^a-z0-9_\:]', '', k)
    check_owner_user(user, owner, allow_anonymous=True)
    if k[-1:] == '*':
        timing = await db_exec("""
SELECT json_agg(j)::json FROM(
    SELECT *
    FROM folksonomy
    WHERE product = %s AND owner = %s AND k ~ %s
    ORDER BY k) as j;
""", (product, owner, '^%s(:.|$)' % key))
    else:
        timing = await db_exec("""
SELECT row_to_json(j) FROM(
    SELECT *
    FROM folksonomy
    WHERE product = %s AND owner = %s AND k = %s
    ) as j;
""", (product, owner, key))

    out = cur.fetchone()
    if out:
        return JSONResponse(status_code=200, content=out[0], headers={"x-pg-timing": timing})
    else:
        return


@app.get("/product/{product}/{k}/versions", response_model=List[ProductTag])
async def product_tag_list_versions(response: Response,
                                    product: str, k: str, owner='',
                                    user: User = Depends(get_current_user)):
    """
    Get a list of all versions of a tag for a product
    """

    check_owner_user(user, owner, allow_anonymous=True)
    timing = await db_exec("""
SELECT json_agg(j)::json FROM(
    SELECT *
    FROM folksonomy_versions
    WHERE product = %s AND owner = %s AND k = %s
    ORDER BY version DESC
    ) as j;
""", (product, owner, k))
    out = cur.fetchone()
    return JSONResponse(status_code=200, content=out[0], headers={"x-pg-timing": timing})


@app.post("/product")
async def product_tag_add(response: Response,
                          product_tag: ProductTag,
                          user: User = Depends(get_current_user)):
    """
    Create a new product tag (version=1)
    """

    check_owner_user(user, product_tag.owner, allow_anonymous=False)
    try:
        timing = await db_exec("""
INSERT INTO folksonomy (product,k,v,owner,version,editor,comment)
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (product_tag.product, product_tag.k.lower(), product_tag.v, product_tag.owner,
            product_tag.version, user, product_tag.comment
          ))
    except psycopg2.Error as e:
        error_msg = re.sub(r'.*@@ (.*) @@\n.*$', r'\1', e.pgerror)[:-1]
        return JSONResponse(status_code=422, content={"detail": {"msg": error_msg}})

    if cur.rowcount == 1:
        return "ok"
    return


@app.put("/product")
async def product_tag_update(response: Response,
                             product_tag: ProductTag,
                             user: User = Depends(get_current_user)):
    """
    Update a product tag

    - **product** : which product
    - **k** : which key for the tag
    - **v** : which value to set for the tag
    - **version** : must be equal to previous version + 1
    - **owner** : None or empty for public tags, or your own user_id
    """

    check_owner_user(user, product_tag.owner, allow_anonymous=False)
    try:
        timing = await db_exec("""
UPDATE folksonomy SET v = %s, version = %s, editor = %s, comment = %s
    WHERE product = %s AND owner = %s AND k = %s
    """, (product_tag.v, product_tag.version, user, product_tag.comment,
            product_tag.product, product_tag.owner, product_tag.k.lower()))
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=422,
            detail=re.sub(r'.*@@ (.*) @@\n.*$', r'\1', e.pgerror)[:-1],
        )

    if cur.rowcount == 1:
        return "ok"
    return


@app.delete("/product/{product}/{k}")
async def product_tag_delete(response: Response,
                             product: str, k: str, version: int, owner='',
                             user: User = Depends(get_current_user)):
    """
    Delete a product tag
    """

    check_owner_user(user, owner, allow_anonymous=False)

    try:
        await db_exec("""
BEGIN;
UPDATE folksonomy SET version = 0, editor = %s, comment = 'DELETE'
    WHERE product = %s AND owner = %s AND k = %s AND version = %s;
    """, (user, product, owner, k, version))
    except psycopg2.Error as e:
        await db_exec("ROLLBACK")
        raise HTTPException(
            status_code=422,
            detail=re.sub(r'.*@@ (.*) @@\n.*$', r'\1', e.pgerror)[:-1],
        )
    if cur.rowcount != 1:
        raise HTTPException(
            status_code=422,
            detail="Unknown product/k/version for this owner",
        )

    await db_exec("""
DELETE FROM folksonomy WHERE product = %s AND owner = %s AND k = %s AND version = 0;
    """, (product, owner, k.lower()))
    if cur.rowcount == 1:
        await db_exec("COMMIT")
        return "ok"
    else:
        await db_exec("""
SELECT version FROM folksonomy WHERE product = %s AND owner = %s AND k = %s
    """, (product, owner, k))
        if cur.rowcount == 1:
            out = cur.fetchone()
            raise HTTPException(
                status_code=422,
                detail="version mismatch, last version for this product/k is %s" % out[0],
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Unknown product/k for this owner",
            )


@app.get("/keys")
async def keys_list(response: Response,
                    owner='',
                    user: User = Depends(get_current_user)):
    """
    Get the list of keys with statistics

    The keys list can be restricted to private tags from some owner
    """

    check_owner_user(user, owner, allow_anonymous=True)
    timing = await db_exec("""
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
""", (owner,))
    out = cur.fetchone()
    return JSONResponse(status_code=200, content=out[0], headers={"x-pg-timing": timing})


@app.get("/ping")
async def pong(response: Response):
    """
    Check server health
    """
    await db_exec("SELECT current_timestamp AT TIME ZONE 'GMT'",())
    pong = cur.fetchone()
    return {"ping": "pong @ %s" % pong[0]}
