#! /usr/bin/python3
 
import json, time, re, uuid
from datetime import datetime
from typing import List, Optional

# interface with postgresql
import psycopg2

# requests to call OFF for login/password check
import requests

# FastAPI
from fastapi import FastAPI, status, Response, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# pydantic: define data schema
from pydantic import BaseModel, ValidationError, validator

# folksonomy imports...
from folksonomy.models import ProductTag, ProductStats, User


app = FastAPI(title="Open Food Facts folksonomy REST API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# define route for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")


async def check_current_user(token: str = Depends(oauth2_scheme)):
    """ Get current user and check for required authentication credentials """
    if '__U' in token:
        (db, cur) = await db_connect()
        query = cur.mogrify("UPDATE auth SET last_use = current_timestamp AT TIME ZONE 'GMT' WHERE token = %s", (token,))
        cur.execute(query)
        if cur.rowcount == 1:
            db.commit()
            user = token.split('__U')[0]
        db.close()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        return { "user_id": user }


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """ Get current user if present (nor required) """
    if '__U' in token:
        (db, cur) = await db_connect()
        query = cur.mogrify(
            "UPDATE auth SET last_use = current_timestamp AT TIME ZONE 'GMT' WHERE token = %s", (token,))
        cur.execute(query)
        if cur.rowcount == 1:
            db.commit()
            user = token.split('__U')[0]
        db.close()
    return user

@app.post("/auth")
async def authentication(form_data: OAuth2PasswordRequestForm = Depends()):
    user_id = form_data.username
    password = form_data.password
    token = user_id+'__U'+str(uuid.uuid4())
    r = requests.post("https://world.openfoodfacts.org/cgi/auth.pl",
                      data={'user_id': user_id, 'password': password})
    if r.status_code == 200:
        (db, cur) = await db_connect()
        query = cur.mogrify("""
DELETE FROM auth WHERE user_id = '%s';
INSERT INTO auth (user_id, token, last_use) VALUES ('%s','%s',current_timestamp AT TIME ZONE 'GMT');
        """ % (user_id, user_id, token))
        cur.execute(query)
        if cur.rowcount == 1:
            db.commit()
            return {"access_token": token, "token_type": "bearer"}
        db.close()
    elif r.status_code == 403:
        time.sleep(5)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(
        status_code=500, detail="Server error")




async def db_connect():
    db = psycopg2.connect("dbname=folksonomy")
    return (db, db.cursor())

@app.on_event("startup")
async def startup():
    await db_connect()


@app.on_event("shutdown")
async def shutdown():
    await db.close()

@app.get("/", status_code=status.HTTP_200_OK)
async def hello():
    return {"message": "Hello folksonomy World"}


@app.get("/products/", response_model=List[ProductStats])
    # product list by owner + number of keys,, editors and last_edit
async def product_list(response: Response, owner='', user: User = Depends(get_current_user)):
    if owner != '':
        if owner != user:
            return JSONResponse(status_code=422, content={"detail": {"msg": "owner should be '%s' or '' for public, was '%s'" % (user, owner)}})
    t = time.time()
    (db, cur) = await db_connect()
    query = cur.mogrify("""
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
    cur.execute(query)
    out = cur.fetchone()
    db.close()
    response.headers['x-pg-timing'] = str(round(time.time()-t,4)*1000)+"ms"
    return out[0]


# product list by owner + number of keys,, editors and last_edit
@app.get("/product/{product}", response_model=List[ProductTag])
async def product_detail(response: Response, product: str, owner='', user: User = Depends(get_current_user)):
    if owner != '':
        if owner != user:
            return JSONResponse(status_code=422, content={"detail": {"msg": "owner should be '%s' or '' for public, was '%s'" % (user, owner)}})

    t = time.time()
    (db, cur) = await db_connect()
    query = cur.mogrify("""
SELECT json_agg(j)::json FROM(
    SELECT *
    FROM folksonomy 
    WHERE product = %s AND owner = %s
    ORDER BY k
    ) as j;
""", (product, owner))
    cur.execute(query)
    out = cur.fetchone()
    db.close()
    response.headers['x-pg-timing'] = str(round(time.time()-t, 4)*1000)+"ms"
    return out[0]


@app.get("/product/{product}/{k}", response_model=ProductTag)
async def product_tag_list_versions(response: Response, product: str, k: str, owner='', user: User = Depends(get_current_user)):
    if owner != '':
        if owner != user:
            return JSONResponse(status_code=422, content={"detail": {"msg": "owner should be '%s' or '' for public, was '%s'" % (user, owner)}})

    t = time.time()
    (db, cur) = await db_connect()
    query = cur.mogrify("""
SELECT row_to_json(j) FROM(
    SELECT *
    FROM folksonomy
    WHERE product = %s AND owner = %s AND k = %s
    ) as j;
""", (product, owner, k))
    cur.execute(query)
    out = cur.fetchone()
    db.close()
    response.headers['x-pg-timing'] = str(round(time.time()-t, 4)*1000)+"ms"
    return out[0]


@app.get("/product/{product}/{k}/versions", response_model=List[ProductTag])
async def product_tag_list_versions(response: Response, product: str, k: str, owner='', user: User = Depends(get_current_user)):
    """product list by owner + number of keys,, editors and last_edit"""
    if owner != '':
        if owner != user:
            return JSONResponse(status_code=422, content={"detail": {"msg": "owner should be '%s' or '' for public, was '%s'" % (user, owner)}})

    t = time.time()
    (db, cur) = await db_connect()
    query = cur.mogrify("""
SELECT json_agg(j)::json FROM(
    SELECT *
    FROM folksonomy_versions
    WHERE product = %s AND owner = %s AND k = %s
    ORDER BY version DESC
    ) as j;
""", (product, owner, k))
    cur.execute(query)
    out = cur.fetchone()
    db.close()
    response.headers['x-pg-timing'] = str(round(time.time()-t, 4)*1000)+"ms"
    return out[0]


@app.get("/product/{product}/{k}/version/{version}", response_model=ProductTag)
async def product_tag_version(response: Response, product: str, k: str, version: int, owner='', user: User = Depends(get_current_user)):
    if owner != '':
        if owner != user:
            return JSONResponse(status_code=422, content={"detail": {"msg": "owner should be '%s' or '' for public, was '%s'" % (user, owner)}})

    t = time.time()
    (db, cur) = await db_connect()
    query = cur.mogrify("""
SELECT row_to_json(j) FROM(
    SELECT *
    FROM folksonomy_versions
    WHERE product = %s AND owner = %s AND k = %s and version = %s
    ) as j;
""", (product, owner, k, version))
    cur.execute(query)
    out = cur.fetchone()
    db.close()
    response.headers['x-pg-timing'] = str(round(time.time()-t, 4)*1000)+"ms"
    return out[0]


@app.post("/product")
async def product_tag_add(  response: Response,
                            product_tag: ProductTag,
                            user: User = Depends(check_current_user)):

    if product_tag.owner not in ('', user["user_id"]):
        return JSONResponse(status_code=422, content={"detail": {"msg": "owner should be '%s' or '' for public, was '%s'" % (user["user_id"], product_tag.owner)}})

    t = time.time()
    (db, cur) = await db_connect()
    query = cur.mogrify("""
INSERT INTO folksonomy (product,k,v,owner,version,editor,comment)
    VALUES ('%s','%s','%s','%s', %s,'%s','%s')
    """ % ( product_tag.product,
            product_tag.k,
            product_tag.v,
            product_tag.owner,
            product_tag.version,
            user["user_id"],
            product_tag.comment
             ))
    try:
        cur.execute(query)
    except psycopg2.Error as e:
        error_msg = re.sub(r'.*@@ (.*) @@\n.*$', r'\1', e.pgerror)[:-1]
        return JSONResponse(status_code=422, content={"detail": {"msg": error_msg}})
    db.commit()
    if cur.rowcount == 1:
        return "ok"
    db.close()
    response.headers['x-pg-timing'] = str(round(time.time()-t, 4)*1000)+"ms"
    return


@app.put("/product")
async def product_tag_update(   response: Response,
                                product_tag: ProductTag,
                                user: User = Depends(check_current_user)):

    if product_tag.owner not in ('', user["user_id"]):
        return JSONResponse(status_code=422, content={"detail": {"msg": "owner should be '%s' or '' for public, was '%s'" % (user["user_id"], product_tag.owner)}})

    t = time.time()
    (db, cur) = await db_connect()
    query = cur.mogrify("""
UPDATE folksonomy SET 
    v = '%s',
    version = %s,
    editor = '%s',
    comment = '%s'
    WHERE product = '%s' AND owner = '%s' AND k = '%s'
    """ % (product_tag.v, product_tag.version, user["user_id"], product_tag.comment, product_tag.product, product_tag.owner, product_tag.k))
    try:
        cur.execute(query)
    except psycopg2.Error as e:
        error_msg = re.sub(r'.*@@ (.*) @@\n.*$',r'\1',e.pgerror)[:-1]
        return JSONResponse(status_code=422, content={"detail": {"msg": error_msg}})
    db.commit()
    if cur.rowcount == 1:
        return "ok"
    db.close()
    response.headers['x-pg-timing'] = str(round(time.time()-t, 4)*1000)+"ms"
    return


@app.delete("/product")
async def product_tag_delete(   response: Response,
                                product: str,
                                k: str,
                                version: int,
                                owner = '',
                                user: User = Depends(check_current_user)):

    if product_tag.owner not in ('', user["user_id"]):
        return JSONResponse(status_code=422, content={"detail": {"msg": "owner should be '%s' or '' for public, was '%s'" % (user["user_id"], product_tag.owner)}})

    t = time.time()
    (db, cur) = await db_connect()
    query = cur.mogrify("""
DELETE FROM folksonomy WHERE product = '%s' AND owner = '%s' AND k = '%s' AND version = %s
    """ % (product, owner, k, version))
    cur.execute(query)
    if cur.rowcount == 1:
        return "ok"
    db.close()
    response.headers['x-pg-timing'] = str(round(time.time()-t, 4)*1000)+"ms"
    return
