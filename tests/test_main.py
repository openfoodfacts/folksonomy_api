import json
import pytest
import time

from fastapi.testclient import TestClient

from folksonomy.api import app

try:
    import local_settings
    skip_auth = False
except:
    skip_auth = True
    pass

# use to test model conformance
from typing import List, Optional
from folksonomy.models import ProductStats,ProductList


client = TestClient(app)
access_token = None
date = int(time.time())

def test_hello():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello folksonomy World! Tip: open /docs for documentation"}


def test_ping():
    with TestClient(app) as client:
        response = client.get("/ping")
        assert response.status_code == 200


def test_products_stats():
    with TestClient(app) as client:
        response = client.get("/products/stats")
        assert response.status_code == 200
        return response.json()


def test_products_list():
    with TestClient(app) as client:
        response = client.get("/products")
        assert response.status_code == 422
        response = client.get("/products?k=xxx")
        assert response.status_code == 200
        response = client.get("/products?k=xxx&v=yyy")
        assert response.status_code == 200


def test_products_list_private_anonymous():
    with TestClient(app) as client:
        response = client.get("/products?owner=foo")
        assert response.status_code == 401


def test_product():
    products = test_products_stats()
    with TestClient(app) as client:
        response = client.get("/product/"+products[0]['product'])
        assert response.status_code == 200
        return response.json()


def test_product_missing():
    products = test_products_list()
    with TestClient(app) as client:
        response = client.get("/product/__xxxxx__")
        assert response.status_code == 200
        assert response.json() == None
        return response.json()


def test_product_key():
    product = test_product()
    with TestClient(app) as client:
        response = client.get(
            "/product/"+product[0]['product']+"/"+product[0]['k']+'*')
        assert response.status_code == 200

        response = client.get(
            "/product/"+product[0]['product']+"/"+product[0]['k'])
        assert response.status_code == 200
        return response.json()


def test_product_key_missing():
    product = test_product()
    with TestClient(app) as client:
        response = client.get("/product/"+product[0]['product']+"/__xxxxx__")
        assert response.status_code == 200
        assert response.json() == None


def test_product_key_versions():
    product = test_product()
    with TestClient(app) as client:
        response = client.get(
            "/product/%s/%s/versions" % (product[0]['product'], product[0]['k']))
        assert response.status_code == 200
        return response.json()


def test_product_key_versions_missing():
    product = test_product()
    with TestClient(app) as client:
        response = client.get(
            "/product/%s/__xxxx__/versions" % product[0]['product'])
        assert response.status_code == 200
        assert response.json() == None
        return response.json()


def test_product_missing():
    products = test_products_list()
    with TestClient(app) as client:
        response = client.get("/product/xxxxx")
        assert response.status_code == 200
        assert response.json() == None
        return response.json()


def test_products_stats_key():
    product = test_product()
    with TestClient(app) as client:
        response = client.get(
            "/products/stats?k=%s" % product[0]['k'])
        assert response.status_code == 200


def test_products_stats_key_value():
    product = test_product()
    with TestClient(app) as client:
        response = client.get(
            "/products/stats?k=%s&v=%s" % (product[0]['k'], product[0]['v']))
        assert response.status_code == 200


def test_products_list_key():
    product = test_product()
    with TestClient(app) as client:
        response = client.get(
            "/products?k=%s" % product[0]['k'])
        assert response.status_code == 200


def test_products_list_key_value():
    product = test_product()
    with TestClient(app) as client:
        response = client.get(
            "/products?k=%s&v=%s" % (product[0]['k'], product[0]['v']))
        assert response.status_code == 200


def test_keys_list():
    with TestClient(app) as client:
        response = client.get("/keys")
        assert response.status_code == 200
        return response.json()


def test_auth_empty():
    with TestClient(app) as client:
        response = client.post("/auth")
        assert response.status_code == 422


def test_auth_bad():
    with TestClient(app) as client:
        response = client.post(
            "/auth", data={"username": "foo", "password": "bar"})
        assert response.status_code == 401


def get_auth_token():
    global access_token
    if access_token is None:
        access_token = test_auth_ok()
    return {"Authorization":  "Bearer "+access_token }


@pytest.mark.skipif(skip_auth, reason="skip auth tests")
def test_auth_ok():
    global access_token
    with TestClient(app) as client:
        response = client.post(
            "/auth", data={"username": local_settings.USER, "password": local_settings.PASSWORD})
        assert response.status_code == 200
        assert 'token_type' in response.json()
        assert 'access_token' in response.json()
        access_token = response.json()['access_token']
        return access_token


@pytest.mark.skipif(skip_auth, reason="skip auth tests")
def test_post():
    p = test_product()[0]
    print(p)
    with TestClient(app) as client:
        response = client.post("/product", headers=get_auth_token(), json=
            {"product": "", "version": 1, "k": "test", "v": "test"})
        assert response.status_code == 422, f'product = "" should return 422, got {response.status_code}'

        response = client.post("/product", headers=get_auth_token(), json=
            {"product": "0000000000000", "version": 0, "k": "test", "v": "test"})
        assert response.status_code == 422, f'version != 1 should return 422, got {response.status_code}'

        response = client.post("/product", headers=get_auth_token(), json=
            {"product": "0000000000000", "version": -1, "k": "test", "v": "test"})
        assert response.status_code == 422, f'version != 1 should return 422, got {response.status_code}'

        response = client.post("/product", headers=get_auth_token(), json=
            {"product": "0000000000000", "version": 9999, "k": "test", "v": "test"})
        assert response.status_code == 422, f'version != 1 should return 422, got {response.status_code}'

        response = client.post("/product", headers = get_auth_token(), json=
                                {"product": "aa", "version": 1, "k": "test", "v": "test"})
        assert response.status_code == 422, f'non alphanum product should return 422, got {response.status_code}'

        response = client.post("/product", headers=get_auth_token(), json=
            {"product": "0000000000000", "version": 1, "k": "", "v": "test"})
        assert response.status_code == 422, f'k="" should return 422, got {response.status_code}'

        response = client.post("/product", headers=get_auth_token(), json=
            {"product": "0000000000000", "version": 1, "k": "ABCD", "v": "test"})
        assert response.status_code == 422, f'non lowercase k should return 422, got {response.status_code}'

        response = client.post("/product", headers=get_auth_token(), json=
            {"product": "0000000000000", "version": 1, "k": "$$", "v": "test"})
        assert response.status_code == 422, f'invalid k should return 422, got {response.status_code}'

        response = client.post("/product", headers=get_auth_token(), json=
            {"product": "0000000000000", "version": 1, "k": "aa", "v": "test", "owner": "someone_else"})
        assert response.status_code == 422, f'invalid owner should return 422, got {response.status_code}'

        response = client.post("/product", headers=get_auth_token(), json=
            {"product": "1234567890123456789012345", "version": 1, "k": "aa", "v": "test"})
        assert response.status_code == 422, f'invalid barcode with 25 digits should return 422, got {response.status_code}'

        response = client.post("/product", headers=get_auth_token(), json=
            {"product": p['product'], "version": 1, "k": "test_"+str(date), "v": "test"})
        assert response.status_code == 200, f'valid new entry should return 200, got {response.status_code} {response.text}'


@pytest.mark.skipif(skip_auth, reason="skip auth tests")
def test_put():
    p = test_product()[0]
    with TestClient(app) as client:
        response = client.put("/product", headers=get_auth_token(), json={
                              "product": p['product'], "k": "test_"+str(date), "v": "test", "version": 1})
        assert response.status_code == 422, f'invalid version should return 422, got {response.status_code} {response.text}'

        response = client.put("/product", headers=get_auth_token(), json={
                              "product": p['product'], "k": "test_"+str(date), "v": "test", "version": 2})
        assert response.status_code == 200, f'valid new version should return 200, got {response.status_code} {response.text}'

        response = client.put("/product", headers=get_auth_token(), json={
                              "product": p['product'], "k": "test_"+str(date), "v": "test", "version": 2})
        assert response.status_code == 422, f'invalid version should return 422, got {response.status_code} {response.text}'


@pytest.mark.skipif(skip_auth, reason="skip auth tests")
def test_delete():
    p = test_product()[0]
    with TestClient(app) as client:
        response = client.delete("/product/"+p['product']+"/test_"+str(date))
        assert response.status_code == 422, f'invalid auth should return 422, got {response.status_code} {response.text}'

        response = client.delete("/product/"+p['product']+"/test_"+str(date), headers=get_auth_token())
        assert response.status_code == 422, f'missing version should return 422, got {response.status_code} {response.text}'

        response = client.delete(
            "/product/"+p['product']+"/test_"+str(date)+"?version=1", headers=get_auth_token(),)
        assert response.status_code == 422, f'invalid version should return 422, got {response.status_code} {response.text}'

        response = client.delete(
            "/product/"+p['product']+"/test_"+str(date)+"?version=3", headers=get_auth_token(),)
        assert response.status_code == 422, f'invalid version should return 422, got {response.status_code} {response.text}'

        response = client.delete(
            "/product/"+p['product']+"/test_"+str(date)+"?version=2", headers=get_auth_token(),)
        assert response.status_code == 200, f'valid version should return 200, got {response.status_code} {response.text}'

        response = client.post("/product", headers=get_auth_token(), json={
            "product": p['product'], "version": 1, "k": "test_"+str(date), "v": "test"})
        assert response.status_code == 200, f'valid new entry should return 200, got {response.status_code} {response.text}'


def test_auth_by_cookie():
    with TestClient(app) as client:
        response = client.post("/auth_by_cookie")
        assert response.status_code == 422, f'missing cookie should return 422, got {response.status_code} {response.text}'

        response = client.post("/auth_by_cookie", headers={'Cookie': 'session=toto'})
        assert response.status_code == 422, f'Malformed session cookie should return 422, got {response.status_code} {response.text}'

        response = client.post("/auth_by_cookie", headers={'Cookie': 'session=titi&toto'})
        assert response.status_code == 422, f'Malformed session cookie should return 422, got {response.status_code} {response.text}'

        response = client.post("/auth_by_cookie", headers={'Cookie': 'session=user_session&2lRIus5uMqwfAjlMe8P2rETG9kUZPYwzCYfVJRfROozyQZYDH24yrWK567VNeYta&user_id&bibifricotin'})
        assert response.status_code == 401, f'Well formed cookie but invalid authentication credentials should return 401, got {response.status_code} {response.text}'

