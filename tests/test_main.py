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


def test_products_list():
    with TestClient(app) as client:
        response = client.get("/products")
        assert response.status_code == 200
        return response.json()


def test_product():
    products = test_products_list()
    with TestClient(app) as client:
        response = client.get("/product/"+products[0]['product'])
        assert response.status_code == 200
        return response.json()

def test_product_key():
    product = test_product()
    with TestClient(app) as client:
        response = client.get("/product/"+product[0]['product']+"/"+product[0]['k'])
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
