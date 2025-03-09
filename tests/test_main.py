"""Integration tests

**Important:** you should run tests with PYTHONASYNCIODEBUG=1
"""
import asyncio
import collections
import contextlib
import json
import pytest
import time

import aiohttp
from fastapi.testclient import TestClient

from folksonomy import db, models, settings
from folksonomy.api import app


# use to test model conformance
from typing import List, Optional
from folksonomy.models import ProductStats,ProductList


client = TestClient(app)
access_token = None
date = int(time.time())


BARCODE_1 = "3701027900001"
BARCODE_2 = "3701027900002"
BARCODE_3 = "3701027900003"


SAMPLES = [
    {"product": BARCODE_1, "k": "color", "v": "red", "owner": "", "version": 1, "editor": "foo", "comment": ""},
    {"product": BARCODE_1, "k": "size", "v": "medium", "owner": "", "version": 1, "editor": "foo", "comment": ""},
    {"product": BARCODE_2, "k": "color", "v": "green", "owner": "", "version": 2, "editor": "foo", "comment": ""},
    {"product": BARCODE_2, "k": "size", "v": "small", "owner": "", "version": 1, "editor": "bar", "comment": ""},
    {"product": BARCODE_3, "k": "color", "v": "red", "owner": "", "version": 3, "editor": "foo", "comment": ""},
    {"product": BARCODE_1, "k": "private", "v": "private", "owner": "foo", "version": 1, "editor": "foo", "comment": ""},
    {"product": BARCODE_1, "k": "other", "v": "so-private", "owner": "bar", "version": 2, "editor": "bar", "comment": ""},
]

# useful to reference samples in tests
sample_by_keys = {(s["product"], s["k"], s["version"]): s for s in SAMPLES}


@pytest.fixture(autouse=True)
def clean_db():
    # clean database before running a test
    asyncio.run(_clean_db())


async def _clean_db():
    async with db.transaction():
        await clean_data()

@pytest.fixture
def with_sample(auth_tokens):
    asyncio.run(_with_sample())


async def _with_sample():
    async with db.transaction():
        await create_data(SAMPLES)


async def clean_data():
    # assert we are not in a production database
    cur, timing = await db.db_exec(
        """
        SELECT COUNT(*) as tags_count
        FROM folksonomy
        """
    )
    result = await cur.fetchone()
    if result and result[0] > 10:
        raise Exception("Database has %d items - refusing to run tests" % result[0])
    cur, timing = await db.db_exec("TRUNCATE folksonomy; TRUNCATE folksonomy_versions; TRUNCATE auth;")


async def create_data(samples):
    for sample in samples:
        data = dict(sample)
        target_version = sample["version"]
        data["version"] = 1 # mandatory for creation
        product_tag = models.ProductTag(**data)
        if target_version > 1:
            product_tag.v += " - 1"
        req, params = db.create_product_tag_req(product_tag)
        await db.db_exec(req, params)
        # make updates to upgrade versions
        for version in range(data["version"] + 1, target_version + 1):
            product_tag.v = sample["v"]
            if version < target_version:
                product_tag.v += " - %s" % version
            product_tag.version = version
            req, params = db.update_product_tag_req(product_tag)
            await db.db_exec(req, params)


@pytest.fixture
def auth_tokens():
    asyncio.run(_add_auth_tokens())


async def _add_auth_tokens():
    # add a token to auth foo and bar
    async with db.transaction():
        await db.db_exec(
            """
            INSERT INTO auth (user_id, token, last_use) VALUES
            ('foo','foo__Utest-token',current_timestamp AT TIME ZONE 'GMT'),
            ('bar','bar__Utest-token',current_timestamp AT TIME ZONE 'GMT')
            """
        )


class DummyResponse:

    def __init__(self, status):
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        pass

def dummy_auth(self, auth_url, data=None, cookies=None):
    assert auth_url == "http://authserver/cgi/auth.pl", "'test' replaced by 'auth' in URL"
    success = False
    # reject or not based on password, which should always be "test" :-)
    if data is not None:
        assert sorted(data.keys()) == ["password", "user_id"]
        if data["password"] == "test":
            success = True
    # session token must be test !
    else:
        assert sorted(cookies.keys()) == ["session"]
        if "&test&" in cookies.get("session", ""):
            success = True
    if success:
        return DummyResponse(200)
    else:
        return DummyResponse(403)

@pytest.fixture
def fake_authentication(monkeypatch):
    """Fake authentication using dummy_auth"""
    monkeypatch.setattr(settings, "FOLKSONOMY_PREFIX", "test")
    monkeypatch.setattr(settings, "AUTH_PREFIX", "auth")
    monkeypatch.setattr(aiohttp.ClientSession, "post", dummy_auth)


def remove_last_edit(data):
    for d in data:
        d.pop("last_edit")
    return data


async def check_tag(product, k, **kwargs):
    expected_data = dict(product=product, k=k, **kwargs)
    cols = list(expected_data.keys())
    async with db.transaction():
        cur, _ = await db.db_exec(
            f"""SELECT {",".join(cols)} FROM folksonomy WHERE product=%s AND k=%s""",
            (product, k)
        )
        assert cur.rowcount == 1, f'Row exists in database'
        data = dict(zip(cols, await cur.fetchone()))
        assert data == expected_data


@pytest.mark.asyncio
async def test_versions_history(with_sample):
    # after sample insertions we have history
    async with db.transaction():
        cur, _ = await db.db_exec("""SELECT product, k, version, v, owner, editor, comment from folksonomy_versions""")
        data = await cur.fetchall()
        data = [dict(zip(["product", "k", "version", "v", "owner", "editor", "comment"], d)) for d in data]
    assert len(data) == 11  # cumulated versions of SAMPLE
    # get data corresponding to sample (that is last version)
    data_by_keys = {(d["product"], d["k"], d["version"]): d for d in data}
    for k in sample_by_keys.keys():
        version_data = data_by_keys.pop(k)
        assert version_data == sample_by_keys[k]
    # 4 older versions remaining (other where popped)
    assert len(data_by_keys) == 4
    old_versions = [data_by_keys[k] for k in sorted(data_by_keys.keys())]
    assert old_versions == [
        {'product': '3701027900001', 'k': 'other', 'version': 1, 'v': 'so-private - 1', 'owner': 'bar', 'editor': 'bar', 'comment': ''},
        {'product': '3701027900002', 'k': 'color', 'version': 1, 'v': 'green - 1', 'owner': '', 'editor': 'foo', 'comment': ''},
        {'product': '3701027900003', 'k': 'color', 'version': 1, 'v': 'red - 1', 'owner': '', 'editor': 'foo', 'comment': ''},
        {'product': '3701027900003', 'k': 'color', 'version': 2, 'v': 'red - 2', 'owner': '', 'editor': 'foo', 'comment': ''},
    ]


def test_hello():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello folksonomy World! Tip: open /docs for documentation"}


def test_ping():
    with TestClient(app) as client:
        response = client.get("/ping")
        assert response.status_code == 200


def test_products_stats(with_sample):
    with TestClient(app) as client:
        response = client.get("/products/stats")
        assert response.status_code == 200
        data = response.json()
    # Only public tags are shown
    assert sorted((d["product"], d["keys"], d["editors"]) for d in data) == [
        (BARCODE_1, 2, 1), # bar user tag on product 1 is private, two tags are private
        (BARCODE_2, 2, 2), # bar user tag on product 2 is public
        (BARCODE_3, 1, 1),
    ]


def get_product():
    with TestClient(app) as client:
        response = client.get("/product/" + BARCODE_1)
        assert response.status_code == 200
        return response.json()


def test_products_list(with_sample):
    with TestClient(app) as client:
        response = client.get("/products")
        assert response.status_code == 422
        assert "missing value for k" in response.json()["detail"]["msg"]
        response = client.get("/products?v=red")
        assert response.status_code == 422
        assert "missing value for k" in response.json()["detail"]["msg"]
        response = client.get("/products?k=color")
        assert response.status_code == 200
        data = response.json()
        assert sorted(data, key=lambda d: d["product"]) == [
            {'product': BARCODE_1, 'k': 'color', 'v': 'red'},
            {'product': BARCODE_2, 'k': 'color', 'v': 'green'},
            {'product': BARCODE_3, 'k': 'color', 'v': 'red'},
        ]
        response = client.get("/products?k=color&v=red")
        assert response.status_code == 200
        data = response.json()
        assert data == [
            {'product': BARCODE_1, 'k': 'color', 'v': 'red'},
            {'product': BARCODE_3, 'k': 'color', 'v': 'red'},
        ]
        # private one remains private
        response = client.get("/products?k=private")
        assert response.status_code == 200
        assert response.json() == []
        response = client.get("/products?k=private&v=private")
        assert response.status_code == 200
        assert response.json() == []
        # non existing
        response = client.get("/products?k=doesnotexists")
        assert response.status_code == 200
        assert response.json() == []


def test_products_list_private(with_sample):
    with TestClient(app) as client:
        response = client.get("/products?owner=foo&k=private")
        assert response.status_code == 401
        # with token
        headers = {"Authorization":  "Bearer foo__Utest-token"}
        response = client.get("/products?owner=foo&k=private", headers=headers)
        assert response.status_code == 200
        assert response.json() == [{'product': '3701027900001', 'k': 'private', 'v': 'private'}]
        response = client.get("/products?owner=foo&k=does-not-exists", headers=headers)
        assert response.status_code == 200
        assert response.json() == []


def test_product(with_sample):
    with TestClient(app) as client:
        response = client.get("/product/" + BARCODE_1)
        assert response.status_code == 200
        data = response.json()
    # only public data is visible
    assert len(data) == 2
    for d in data:
        d.pop("last_edit")
    assert sorted(data, key=lambda d: d["k"]) == [
        sample_by_keys[BARCODE_1, "color", 1],
        sample_by_keys[BARCODE_1, "size", 1],
    ]


def test_product_missing(with_sample):
    with TestClient(app) as client:
        response = client.get("/product/0000000000000")
        assert response.status_code == 200
        assert response.json() == None
        return response.json()


def test_product_key(with_sample):
    with TestClient(app) as client:
        for k in ["color*", "color"]:
            response = client.get(f"/product/{BARCODE_1}/{k}*")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            remove_last_edit(data)
            assert data[0] == {
                'product': '3701027900001', 'k': 'color', 'v': 'red', 'owner': '', 'version': 1, 'editor': 'foo', 'comment': ''
            }

def test_key_stripped_on_get(with_sample):
    with TestClient(app) as client:
        response = client.get(f"/product/{BARCODE_1}/ color  ")
        assert response.status_code == 200
        data = response.json()
        data.pop("last_edit")
        assert data == {
            'product': '3701027900001', 'k': 'color', 'v': 'red', 'owner': '', 'version': 1, 'editor': 'foo', 'comment': ''
        }

def test_product_key_missing(with_sample):
    with TestClient(app) as client:
        response = client.get(f"/product/{BARCODE_1}/not-existing")
        assert response.status_code == 404
        assert response.json() == None


def test_product_key_versions(with_sample):
    with TestClient(app) as client:
        # a product with 3 versions
        response = client.get(f"/product/{BARCODE_3}/color/versions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        data = sorted(data, key=lambda d: d["version"])
        remove_last_edit(data)
        assert data == [
            {'product': BARCODE_3, 'k': 'color', 'v': 'red - 1', 'owner': '', 'version': 1, 'editor': 'foo', 'comment': ''},
            {'product': BARCODE_3, 'k': 'color', 'v': 'red - 2', 'owner': '', 'version': 2, 'editor': 'foo',  'comment': ''},
            {'product': BARCODE_3, 'k': 'color', 'v': 'red', 'owner': '', 'version': 3, 'editor': 'foo', 'comment': ''},
        ]


def test_product_key_versions_missing(with_sample):
    with TestClient(app) as client:
        response = client.get(f"/product/{BARCODE_3}/not-existing/versions")
        assert response.status_code == 200
        assert response.json() == None


def test_products_stats_key(with_sample):
    with TestClient(app) as client:
        response = client.get(f"/products/stats?k=color")
        assert response.status_code == 200
        data = sorted(response.json(), key=lambda d: d["product"])
        remove_last_edit(data)
        assert data == [
            {'product': BARCODE_1, 'keys': 1, 'editors': 1},
            {'product': BARCODE_2, 'keys': 1, 'editors': 1},
            {'product': BARCODE_3, 'keys': 1, 'editors': 1}
        ]


def test_products_stats_key_value(with_sample):
    with TestClient(app) as client:
        response = client.get(f"/products/stats?k=color&v=red")
        assert response.status_code == 200
        data = sorted(response.json(), key=lambda d: d["product"])
        remove_last_edit(data)
        assert data == [
            {'product': BARCODE_1, 'keys': 1, 'editors': 1},
            {'product': BARCODE_3, 'keys': 1, 'editors': 1},
        ]


def test_products_list_key(with_sample):
    with TestClient(app) as client:
        response = client.get("/products?k=color")
        assert response.status_code == 200
        data = sorted(response.json(), key=lambda d: d["product"])
        assert data == [
            {'product': BARCODE_1, 'k': 'color', 'v': 'red'},
            {'product': BARCODE_2, 'k': 'color', 'v': 'green'},
            {'product': BARCODE_3, 'k': 'color', 'v': 'red'}
        ]


def test_products_list_key_value(with_sample):
    with TestClient(app) as client:
        response = client.get("/products?k=color&v=red")
        assert response.status_code == 200
        data = sorted(response.json(), key=lambda d: d["product"])
        assert data == [
            {'product': BARCODE_1, 'k': 'color', 'v': 'red'},
            {'product': BARCODE_3, 'k': 'color', 'v': 'red'}
        ]


def test_keys_list(with_sample):
    with TestClient(app) as client:
        response = client.get("/keys")
        assert response.status_code == 200
        data = sorted(response.json(), key=lambda d: d["k"])
        assert data == [
            {'k': 'color', 'count': 3, 'values': 2},
            {'k': 'size', 'count': 2, 'values': 2}
        ]


def test_get_unique_values(with_sample):
    with TestClient(app) as client:
        response = client.get("/values/color")
        assert response.status_code == 200
        assert response.json() == [
            {'v': 'red', 'product_count': 2},
            {'v': 'green', 'product_count': 1}
        ]


def test_get_unique_values_with_limit(with_sample):
    with TestClient(app) as client:
        response = client.get("/values/color?limit=1")
        assert response.status_code == 200
        assert response.json() == [
            {'v': 'red', 'product_count': 2}
        ]


def test_get_unique_values_with_filter(with_sample):
    with TestClient(app) as client:
        response = client.get("/values/color?q=ed")
        assert response.status_code == 200
        assert response.json() == [
            {'v': 'red', 'product_count': 2}
        ]


def test_get_unique_values_non_existing_key(with_sample):
    with TestClient(app) as client:
        response = client.get("/values/non_existing_key")
        assert response.status_code == 200
        assert response.json() == []


def test_auth_empty():
    with TestClient(app) as client:
        response = client.post("/auth")
        assert response.status_code == 422


def test_auth_bad(monkeypatch, fake_authentication):
    # avoid waiting for 2 sec
    monkeypatch.setattr(settings, 'FAILED_AUTH_WAIT_TIME', .1)
    with TestClient(app) as client:
        response = client.post(
            "/auth", data={"username": "foo", "password": "bar"})
        assert response.status_code == 401


def test_auth_ok(fake_authentication):
    with TestClient(app) as client:
        response = client.post(
            "/auth", data={"username": "off", "password": "test"})
        assert response.status_code == 200
        assert 'token_type' in response.json()
        assert 'access_token' in response.json()
        access_token = response.json()['access_token']
        assert access_token.startswith("off__U")


def test_post_invalid(with_sample):
    with TestClient(app) as client:
        headers = {"Authorization":  "Bearer foo__Utest-token"}
        # empty barcode
        response = client.post("/product", headers=headers, json=
            {"product": "", "version": 1, "k": "test", "v": "test"})
        assert response.status_code == 422, f'product = "" should return 422, got {response.status_code}'
        # version 0, forbidden
        response = client.post("/product", headers=headers, json=
            {"product": "0000000000000", "version": 0, "k": "test", "v": "test"})
        assert response.status_code == 422, f'version != 1 should return 422, got {response.status_code}'
        # version -1, forbidden
        response = client.post("/product", headers=headers, json=
            {"product": "0000000000000", "version": -1, "k": "test", "v": "test"})
        assert response.status_code == 422, f'version != 1 should return 422, got {response.status_code}'
        # version not 1, forbidden
        response = client.post("/product", headers=headers, json=
            {"product": "0000000000000", "version": 9999, "k": "test", "v": "test"})
        assert response.status_code == 422, f'version != 1 should return 422, got {response.status_code}'
        # non numeric barcode, forbidden
        response = client.post("/product", headers = headers, json=
                                {"product": "aa", "version": 1, "k": "test", "v": "test"})
        assert response.status_code == 422, f'non numeric product should return 422, got {response.status_code}'
        # empty key, forbidden
        response = client.post("/product", headers=headers, json=
            {"product": "0000000000000", "version": 1, "k": "", "v": "test"})
        assert response.status_code == 422, f'k="" should return 422, got {response.status_code}'
        # empty value, forbidden
        response = client.post("/product", headers=headers, json=
            {"product": "0000000000000", "version": 1, "k": "ABCD", "v": "test"})
        assert response.status_code == 422, f'non lowercase k should return 422, got {response.status_code}'
        # invalid k, forbidden
        response = client.post("/product", headers=headers, json=
            {"product": "0000000000000", "version": 1, "k": "$$", "v": "test"})
        assert response.status_code == 422, f'invalid k should return 422, got {response.status_code}'
        # invalid owner
        response = client.post("/product", headers=headers, json=
            {"product": "0000000000000", "version": 1, "k": "aa", "v": "test", "owner": "someone_else"})
        assert response.status_code == 422, f'invalid owner should return 422, got {response.status_code}'
        # invalid barcode with 25 digits
        response = client.post("/product", headers=headers, json=
            {"product": "1234567890123456789012345", "version": 1, "k": "aa", "v": "test"})
        assert response.status_code == 422, f'invalid barcode with 25 digits should return 422, got {response.status_code}'
        # existing key value, forbidden
        response = client.post("/product", headers=headers, json=
            {"product": BARCODE_1, "version": 1, "k": "color", "v": "red"})
        assert response.status_code == 422, f'existing key value should return 422, got {response.status_code}'

@pytest.mark.asyncio
async def test_post(with_sample):
    with TestClient(app) as client:
        headers = {"Authorization":  "Bearer foo__Utest-token"}

        response = client.post("/product", headers=headers, json=
            {"product": BARCODE_1, "version": 1, "k": "test_new", "v": "test"})
        assert response.status_code == 200, f'valid new entry should return 200, got {response.status_code} {response.text}'
        # created
        await check_tag(BARCODE_1, "test_new", v="test", version=1)

        response = client.post("/product", headers=headers, json=
            {"product": BARCODE_1, "version": 1, "k": "a-1:b_2:c-3:d_4", "v": "test"})
        assert response.status_code == 200, f'lowercase k with hyphen, underscore and number should return 200, got {response.status_code}'
        # created
        await check_tag(BARCODE_1, "a-1:b_2:c-3:d_4", v="test", version=1)


@pytest.mark.asyncio
async def test_product_key_stripped_on_post(auth_tokens):
    with TestClient(app) as client:
        headers = {"Authorization":  "Bearer foo__Utest-token"}
        response = client.post("/product", headers=headers, json=
            {"product": BARCODE_1, "version": 1, "k": " test_new2  ", "v": "test"})
        assert response.status_code == 200, f'valid new entry should return 200, got {response.status_code} {response.text}'
        # check created stripped
        await check_tag(BARCODE_1, "test_new2", v="test", version=1)
        # reachable:
        response = client.get(f"/product/{BARCODE_1}/test_new2")
        assert response.status_code == 200, f'getting stripped key should return 200, got {response.status_code} {response.text}'


@pytest.mark.asyncio
async def test_product_value_stripped_on_post(auth_tokens):
    with TestClient(app) as client:
        headers = {"Authorization":  "Bearer foo__Utest-token"}
        response = client.post("/product", headers=headers, json=
            {"product": BARCODE_1, "version": 1, "k": "test_new", "v": " a test   "})
        assert response.status_code == 200, f'valid new entry should return 200, got {response.status_code} {response.text}'
        # check created stripped
        await check_tag(BARCODE_1, "test_new", v="a test", version=1)


def test_put_invalid(with_sample):
    with TestClient(app) as client:
        headers = {"Authorization":  "Bearer foo__Utest-token"}
        response = client.put("/product", headers=headers, json={
                              "product": BARCODE_1, "k": "test_new", "v": "test", "version": 1})
        assert response.status_code == 404, f'new key should return 404, got {response.status_code} {response.text}'

        response = client.put("/product", headers=headers, json={
                              "product": BARCODE_2, "k": "color", "v": "test", "version": 2})
        assert response.status_code == 422, f'invalid version should return 422, got {response.status_code} {response.text}'


@pytest.mark.asyncio
async def test_put(with_sample):
    with TestClient(app) as client:
        headers = {"Authorization":  "Bearer foo__Utest-token"}
        response = client.put("/product", headers=headers, json={
                            "product": BARCODE_1, "k": "color", "v": "purple", "version": 2})
        assert response.status_code == 200, f'valid new version should return 200, got {response.status_code} {response.text}'
        updated_tag = response.json()
        assert updated_tag["v"] == "purple", f'updated value should be "purple", got {updated_tag["v"]}'
        await check_tag(BARCODE_1, "color", v="purple", version=2)
        # and again
        response = client.put("/product", headers=headers, json={
                            "product": BARCODE_1, "k": "color", "v": "brown", "version": 3})
        assert response.status_code == 200, f'valid new version should return 200, got {response.status_code} {response.text}'
        updated_tag = response.json()
        assert updated_tag["v"] == "brown", f'updated value should be "brown", got {updated_tag["v"]}'
        await check_tag(BARCODE_1, "color", v="brown", version=3)


def test_delete_invalid(with_sample):
    headers = {"Authorization":  "Bearer foo__Utest-token"}
    with TestClient(app) as client:
        response = client.delete(f"/product/{BARCODE_1}/not-existing")
        assert response.status_code == 422, f'invalid auth should return 422, got {response.status_code} {response.text}'

        response = client.delete(f"/product/{BARCODE_1}/color", headers=headers)
        assert response.status_code == 422, f'missing version should return 422, got {response.status_code} {response.text}'

        response = client.delete(
            f"/product/{BARCODE_2}/color?version=1", headers=headers,)
        assert response.status_code == 422, f'invalid version should return 422, got {response.status_code} {response.text}'

        response = client.delete(
            f"/product/{BARCODE_2}/color?version=3", headers=headers,)
        assert response.status_code == 422, f'invalid version should return 422, got {response.status_code} {response.text}'


@pytest.mark.asyncio
async def test_delete(with_sample):
    headers = {"Authorization":  "Bearer foo__Utest-token"}
    with TestClient(app) as client:
        response = client.delete(f"/product/{BARCODE_1}/color?version=1", headers=headers,)
        assert response.status_code == 200, f'valid version should return 200, got {response.status_code} {response.text}'
        # assert False, "FIXME test it's not there !"
        # add anew
        response = client.post("/product", headers=headers, json={
            "product": BARCODE_1, "version": 1, "k": "color", "v": "purple"})
        assert response.status_code == 200, f'valid new entry should return 200, got {response.status_code} {response.text}'
        await check_tag(BARCODE_1, "color", v="purple", version=1)
        # and update
        response = client.put("/product", headers=headers, json={
            "product": BARCODE_1, "version": 2, "k": "color", "v": "brown"})
        assert response.status_code == 200, f'update on new entry should return 200, got {response.status_code} {response.text}'
        await check_tag(BARCODE_1, "color", v="brown", version=2)


@pytest.mark.asyncio
async def test_auth_by_cookie(fake_authentication, monkeypatch):
    # avoid waiting for too long on bad auth
    monkeypatch.setattr(settings, 'FAILED_AUTH_WAIT_TIME', .1)
    with TestClient(app) as client:
        response = client.post("/auth_by_cookie")
        assert response.status_code == 422, f'missing cookie should return 422, got {response.status_code} {response.text}'

        response = client.post("/auth_by_cookie", headers={'Cookie': 'session=test'})
        assert response.status_code == 422, f'Malformed session cookie should return 422, got {response.status_code} {response.text}'

        response = client.post("/auth_by_cookie", headers={'Cookie': 'session=user_session&test'})
        assert response.status_code == 422, f'Malformed session cookie should return 422, got {response.status_code} {response.text}'

        response = client.post("/auth_by_cookie", headers={'Cookie': 'session=user_session&not-a-good-token&user_id&bibifricotin'})
        assert response.status_code == 401, f'Well formed cookie but invalid authentication credentials should return 401, got {response.status_code} {response.text}'

        response = client.post("/auth_by_cookie", headers={'Cookie': 'session=user_session&test&user_id&bibifricotin'})
        assert response.status_code == 200, f'Well formed cookie and valid authentication credentials should return 200, got {response.status_code} {response.text}'
        # token created
        async with db.transaction():
            cur, _ = await db.db_exec("""SELECT user_id FROM auth WHERE user_id = 'bibifricotin'""")
            assert cur.rowcount == 1, f'Well formed cookie and valid authentication credentials should create a token, got {cur.rowcount}'
