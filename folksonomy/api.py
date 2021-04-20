#! /usr/bin/python3
 
from .dependencies import *

app = FastAPI(title="Open Food Facts folksonomy REST API")
# define route for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth", auto_error=False)


@app.on_event("startup")
async def startup():
    global db, cur
    db = psycopg2.connect("dbname=folksonomy")
    cur = db.cursor()


@app.on_event("shutdown")
async def shutdown():
    await db.close()


@app.get("/", status_code=status.HTTP_200_OK)
async def hello():
    return {"message": "Hello folksonomy World"}


async def db_exec(response, query, params):
    """
    Execute postgresql query and collect timing
    """
    t = time.time()
    cur.execute(cur.mogrify(query, params))
    response.headers['x-pg-timing'] = str(round(time.time()-t, 4)*1000)+"ms"


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get current user and check token validity if present
    """
    if token and '__U' in token:
        query = cur.mogrify(
            "UPDATE auth SET last_use = current_timestamp AT TIME ZONE 'GMT' WHERE token = %s", (token,))
        cur.execute(query)
        if cur.rowcount == 1:
            db.commit()
            return token.split('__U')[0]


def check_owner_user(user, owner, allow_anonymous = False):
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

    - **username** : OpenFoodFacts user_id (not email)
    - **password** : user password (clear text, but HTTPS encrypted)

    token is returned, to be used in later requests with usual "Authorization: bearer token" headers
    """

    user_id = form_data.username
    password = form_data.password
    token = user_id+'__U'+str(uuid.uuid4())
    r = requests.post("https://world.openfoodfacts.org/cgi/auth.pl",
                      data={'user_id': user_id, 'password': password})
    if r.status_code == 200:
        await db_exec(response, """
DELETE FROM auth WHERE user_id = %s;
INSERT INTO auth (user_id, token, last_use) VALUES (%s,%s,current_timestamp AT TIME ZONE 'GMT');
        """, (user_id, user_id, token))
        if cur.rowcount == 1:
            db.commit()
            return {"access_token": token, "token_type": "bearer"}
    elif r.status_code == 403:
        time.sleep(5)   # prevents brute-force
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(
        status_code=500, detail="Server error")


@app.get("/products", response_model=List[ProductStats])
async def product_list(response: Response,
            owner='',
            user: User = Depends(get_current_user)):
    """
    Get the list of products with tags statistics
    """

    check_owner_user(user, owner, allow_anonymous=True)
    await db_exec(response, """
SELECT json_agg(j.j)::json FROM(
    SELECT json_build_object(
        'product',product,
        'keys',count(*),
        'last_edit',max(last_edit),
        'editors',count(distinct(editor))
        ) as j
    FROM folksonomy 
    WHERE owner=%s
    GROUP BY product) as j;
""", (owner,))
    out = cur.fetchone()
    return out[0]


@app.get("/product/{product}", response_model=List[ProductTag])
async def product_tags_list(response: Response,
            product: str, owner='',
            user: User = Depends(get_current_user)):
    """
    Get a list of existing tags for a product
    """

    check_owner_user(user, owner, allow_anonymous=True)
    await db_exec(response, """
SELECT json_agg(j)::json FROM(
    SELECT *
    FROM folksonomy 
    WHERE product = %s AND owner = %s
    ORDER BY k
    ) as j;
""", (product, owner))
    out = cur.fetchone()
    if out:
        return out[0]
    else:
        return


@app.get("/product/{product}/{k}", response_model=ProductTag)
async def product_tag(response: Response,
            product: str, k: str, owner='',
            user: User = Depends(get_current_user)):
    """
    Get a specific tag on a product
    """

    check_owner_user(user, owner, allow_anonymous=True)
    await db_exec(response, """
SELECT row_to_json(j) FROM(
    SELECT *
    FROM folksonomy
    WHERE product = %s AND owner = %s AND k = %s
    ) as j;
""", (product, owner, k))
    out = cur.fetchone()
    if out:
        return out[0]
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
    await db_exec(response, """
SELECT json_agg(j)::json FROM(
    SELECT *
    FROM folksonomy_versions
    WHERE product = %s AND owner = %s AND k = %s
    ORDER BY version DESC
    ) as j;
""", (product, owner, k))
    out = cur.fetchone()
    if out:
        return out[0]
    else:
        return


@app.get("/product/{product}/{k}/version/{version}", response_model=ProductTag)
async def product_tag_version(response: Response,
            product: str, k: str, version: int, owner='',
            user: User = Depends(get_current_user)):
    """
    Get a specific version of a tag for a product
    """

    check_owner_user(user, owner, allow_anonymous=True)
    await db_exec(response, """
SELECT row_to_json(j) FROM (
    SELECT *
    FROM folksonomy_versions
    WHERE product = %s AND owner = %s AND k = %s and version = %s
    ) as j;
""", (product, owner, k, version))
    out = cur.fetchone()
    return out[0]


@app.post("/product")
async def product_tag_add(response: Response,
            product_tag: ProductTag,
            user: User = Depends(get_current_user)):
    """
    Create a new product tag (version=1)
    """

    check_owner_user(user, product_tag.owner, allow_anonymous=False)
    try:
        await db_exec(response, """
INSERT INTO folksonomy (product,k,v,owner,version,editor,comment)
    VALUES (%s,%s,%s,%s, %s,%s,%s)
    """, ( product_tag.product, product_tag.k, product_tag.v, product_tag.owner,
            product_tag.version, user, product_tag.comment
          ))
    except psycopg2.Error as e:
        error_msg = re.sub(r'.*@@ (.*) @@\n.*$', r'\1', e.pgerror)[:-1]
        return JSONResponse(status_code=422, content={"detail": {"msg": error_msg}})

    db.commit()
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
        await db_exec(response, """
UPDATE folksonomy SET v = %s, version = %s, editor = %s, comment = %s
    WHERE product = %s AND owner = %s AND k = %s
    """, ( product_tag.v, product_tag.version, user["user_id"], product_tag.comment,
            product_tag.product, product_tag.owner, product_tag.k))
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=422,
            detail=re.sub(r'.*@@ (.*) @@\n.*$', r'\1', e.pgerror)[:-1],
        )

    db.commit()
    if cur.rowcount == 1:
        return "ok"
    return


@app.delete("/product")
async def product_tag_delete(response: Response,
            product: str, k: str, version: int, owner = '',
            user: User = Depends(get_current_user)):

    check_owner_user(user, product_tag.owner, allow_anonymous=False)
    await db_exec(response, """
DELETE FROM folksonomy WHERE product = %s AND owner = %s AND k = %s AND version = %s
    """, (product, owner, k, version))
    db.commit()
    if cur.rowcount == 1:
        return "ok"
    return