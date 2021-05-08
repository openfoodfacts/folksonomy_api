from fastapi.testclient import TestClient

from folksonomy.api import app

client = TestClient(app)


def test_hello():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello folksonomy World"}


def test_ping():
    with TestClient(app) as client:
        response = client.get("/ping")
        assert response.status_code == 200


def test_auth_empty():
    with TestClient(app) as client:
        response = client.post("/auth")
        assert response.status_code == 422


def test_auth_bad():
    with TestClient(app) as client:
        response = client.post("/auth",data={"username": "foo", "password": "bar"})
        assert response.status_code == 401


def test_products_list():
    with TestClient(app) as client:
        response = client.get("/products")
        assert response.status_code == 200
        return response.json()


def test_products_list_private_anonymous():
    with TestClient(app) as client:
        response = client.get("/products?owner=foo")
        assert response.status_code == 401


def test_product():
    products = test_products_list()
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
        response = client.get("/product/"+product[0]['product']+"/"+product[0]['k'])
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


def test_product_key_last_version():
    product = test_product_key_versions()
    with TestClient(app) as client:
        response = client.get(
            "/product/%s/%s/version/1" % (product[0]['product'], product[0]['k']))
        assert response.status_code == 200


def test_product_key_first_version():
    product = test_product_key_versions()
    with TestClient(app) as client:
        response = client.get(
            "/product/%s/%s/version/%s" % (product[0]['product'], product[0]['k'], product[0]['version']))
        assert response.status_code == 200


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


def test_products_list_key():
    product = test_product()
    with TestClient(app) as client:
        response = client.get(
            "/products?k="+product[0]['k'])
        assert response.status_code == 200


def test_products_list_key_value():
    product = test_product()
    with TestClient(app) as client:
        response = client.get(
            "/products?k=%s&v=%s" % (product[0]['k'], product[0]['v']))
        assert response.status_code == 200


def test_products_list_key():
    product = test_product()
    with TestClient(app) as client:
        response = client.get(
            "/products/?k="+product[0]['k'])
        assert response.status_code == 200


def test_keys_list():
    with TestClient(app) as client:
        response = client.get("/keys")
        assert response.status_code == 200
        return response.json()
