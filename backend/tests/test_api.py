# import pytest
# from fastapi.testclient import TestClient
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.pool import StaticPool

# from database import Base, get_db
# from main import app


# @pytest.fixture()
# def client():
#     test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
#     Base.metadata.create_all(test_engine)
#     test_session = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)

#     def override_get_db():
#         db = test_session()
#         try:
#             yield db
#         finally:
#             db.close()

#     app.dependency_overrides[get_db] = override_get_db
#     with TestClient(app) as test_client:
#         yield test_client
#     app.dependency_overrides.clear()
#     Base.metadata.drop_all(test_engine)
#     test_engine.dispose()


# def create_zone(client, name="example.test", private=False):
#     response = client.post("/api/zones", json={"name": name, "comment": "integration test", "is_private": private})
#     assert response.status_code == 201, response.text
#     return response.json()


# def test_zone_crud_public_defaults_and_summary(client):
#     zone = create_zone(client)
#     assert zone["id"] > 0 and zone["created_at"]
#     assert client.get("/api/zones").json()["items"][0]["record_count"] == 2
#     defaults = client.get(f"/api/zones/{zone['id']}/records").json()
#     assert {record["type"] for record in defaults["items"]} == {"NS", "SOA"}
#     assert client.get("/api/summary").json() == {"hosted_zones": 1, "dns_records": 2}
#     assert client.get("/api/zones?search=example&page=1&page_size=1").json()["total"] == 1
#     updated = client.patch(f"/api/zones/{zone['id']}", json={"name": "example.test", "comment": "updated", "is_private": False})
#     assert updated.status_code == 200 and updated.json()["comment"] == "updated"
#     assert client.post("/api/zones", json={"name": "example.test"}).status_code == 409
#     assert client.delete(f"/api/zones/{zone['id']}").status_code == 204
#     assert client.get(f"/api/zones/{zone['id']}").status_code == 404
#     assert client.get("/api/summary").json() == {"hosted_zones": 0, "dns_records": 0}


# def test_private_zone_does_not_seed_public_nameservers(client):
#     zone = create_zone(client, "private.test", private=True)
#     assert client.get(f"/api/zones/{zone['id']}/records").json()["total"] == 0


# @pytest.mark.parametrize(("kind", "value"), [
#     ("A", "192.0.2.5"), ("AAAA", "2001:db8::5"), ("CNAME", "target.example.test."),
#     ("TXT", '"site verification"'), ("MX", "10 mail.example.test."),
#     ("NS", "ns1.example.test.\nns2.example.test."), ("PTR", "host.example.test."),
#     ("SRV", "10 20 443 service.example.test."), ("CAA", '0 issue "ca.example"'),
#     ("SOA", "ns.example.test. hostmaster.example.test. 2026092501 7200 900 1209600 86400"),
# ])
# def test_record_types_create_edit_search_filter_and_delete(client, kind, value):
#     zone = create_zone(client, f"{kind.lower()}.example.test", private=kind == "SOA")
#     record_name = zone["name"] if kind == "SOA" else f"service.{zone['name']}"
#     payload = {"name": record_name, "type": kind, "value": value, "ttl": 300, "routing_policy": "Simple"}
#     created = client.post(f"/api/zones/{zone['id']}/records", json=payload)
#     assert created.status_code == 201, created.text
#     record_id = created.json()["id"]
#     assert created.json()["type"] == kind
#     results = client.get(f"/api/zones/{zone['id']}/records?record_type={kind}&search={record_name}")
#     assert results.json()["total"] == 1
#     payload["value"] = value
#     payload["ttl"] = 600
#     payload["routing_policy"] = "Weighted"
#     updated = client.patch(f"/api/records/{record_id}", json=payload)
#     assert updated.status_code == 200 and updated.json()["ttl"] == 600
#     assert updated.json()["routing_policy"] == "Weighted"
#     assert client.delete(f"/api/records/{record_id}").status_code == 204
#     assert client.delete(f"/api/records/{record_id}").status_code == 404


# @pytest.mark.parametrize(("kind", "value"), [
#     ("A", "999.1.1.1"), ("AAAA", "not:ipv6"), ("CNAME", "bad hostname!"),
#     ("MX", "70000 mail.example.test"), ("NS", "bad hostname!"), ("PTR", "bad hostname!"),
#     ("SRV", "-1 0 53 target.example.test"), ("CAA", "999 issue ca.example"),
#     ("SOA", "ns.example.test hostmaster.example.test 1 2 3"),
# ])
# def test_invalid_record_values_return_422(client, kind, value):
#     zone = create_zone(client, f"bad-{kind.lower()}.test")
#     response = client.post(f"/api/zones/{zone['id']}/records", json={"name": "invalid", "type": kind, "value": value})
#     assert response.status_code == 422, response.text


# def test_exports_cors_health_pagination_and_cascade(client):
#     zone = create_zone(client, "export.test")
#     for index in range(3):
#         response = client.post(f"/api/zones/{zone['id']}/records", json={"name": f"host{index}.export.test", "type": "A", "value": f"192.0.2.{index + 1}"})
#         assert response.status_code == 201
#     page = client.get(f"/api/zones/{zone['id']}/records?page=1&page_size=2")
#     assert page.json()["total"] == 5 and len(page.json()["items"]) == 2
#     assert client.get(f"/api/zones/{zone['id']}/export?format=json").json()["zone"]["name"] == "export.test"
#     assert "$ORIGIN export.test." in client.get(f"/api/zones/{zone['id']}/export?format=bind").text
#     assert client.get("/health").json() == {"status": "ok"}
#     preflight = client.options("/api/zones", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
#     assert preflight.status_code == 200
#     assert client.delete(f"/api/zones/{zone['id']}").status_code == 204
#     assert client.get(f"/api/zones/{zone['id']}/records").status_code == 404


# def test_cname_exclusivity_and_soa_apex_rules(client):
#     zone = create_zone(client, "conflicts.test")
#     records = f"/api/zones/{zone['id']}/records"
#     payload = {"name": "mail.conflicts.test", "type": "A", "value": "192.0.2.20"}
#     assert client.post(records, json=payload).status_code == 201
#     payload.update(type="CNAME", value="target.conflicts.test")
#     assert client.post(records, json=payload).status_code == 409
#     cname = {"name": "alias.conflicts.test", "type": "CNAME", "value": "target.conflicts.test"}
#     assert client.post(records, json=cname).status_code == 201
#     cname.update(type="TXT", value="text")
#     assert client.post(records, json=cname).status_code == 409
#     cname.update(type="SOA", name="sub.conflicts.test", value="ns.example.test hostmaster.example.test 1 2 3 4 5")
#     assert client.post(records, json=cname).status_code == 422



import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


@pytest.fixture()
def client():
    test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(test_engine)
    test_session = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


def create_zone(client, name="example.test", private=False):
    response = client.post("/api/zones", json={"name": name, "comment": "integration test", "is_private": private})
    assert response.status_code == 201, response.text
    return response.json()


def test_zone_crud_public_defaults_and_summary(client):
    zone = create_zone(client)
    assert zone["id"] > 0 and zone["created_at"]
    assert client.get("/api/zones").json()["items"][0]["record_count"] == 2
    defaults = client.get(f"/api/zones/{zone['id']}/records").json()
    assert {record["type"] for record in defaults["items"]} == {"NS", "SOA"}
    assert client.get("/api/summary").json() == {"hosted_zones": 1, "dns_records": 2}
    assert client.get("/api/zones?search=example&page=1&page_size=1").json()["total"] == 1
    updated = client.patch(f"/api/zones/{zone['id']}", json={"name": "example.test", "comment": "updated", "is_private": False})
    assert updated.status_code == 200 and updated.json()["comment"] == "updated"
    assert client.post("/api/zones", json={"name": "example.test"}).status_code == 409
    assert client.delete(f"/api/zones/{zone['id']}").status_code == 204
    assert client.get(f"/api/zones/{zone['id']}").status_code == 404
    assert client.get("/api/summary").json() == {"hosted_zones": 0, "dns_records": 0}


def test_private_zone_does_not_seed_public_nameservers(client):
    zone = create_zone(client, "private.test", private=True)
    assert client.get(f"/api/zones/{zone['id']}/records").json()["total"] == 0


@pytest.mark.parametrize(("kind", "value"), [
    ("A", "192.0.2.5"), ("AAAA", "2001:db8::5"), ("CNAME", "target.example.test."),
    ("TXT", '"site verification"'), ("MX", "10 mail.example.test."),
    ("NS", "ns1.example.test.\nns2.example.test."), ("PTR", "host.example.test."),
    ("SRV", "10 20 443 service.example.test."), ("CAA", '0 issue "ca.example"'),
    ("SOA", "ns.example.test. hostmaster.example.test. 2026092501 7200 900 1209600 86400"),
])
def test_record_types_create_edit_search_filter_and_delete(client, kind, value):
    zone = create_zone(client, f"{kind.lower()}.example.test", private=kind == "SOA")
    record_name = zone["name"] if kind == "SOA" else f"service.{zone['name']}"
    payload = {"name": record_name, "type": kind, "value": value, "ttl": 300, "routing_policy": "Simple"}
    created = client.post(f"/api/zones/{zone['id']}/records", json=payload)
    assert created.status_code == 201, created.text
    record_id = created.json()["id"]
    assert created.json()["type"] == kind
    results = client.get(f"/api/zones/{zone['id']}/records?record_type={kind}&search={record_name}")
    assert results.json()["total"] == 1
    payload["value"] = value
    payload["ttl"] = 600
    payload["routing_policy"] = "Weighted"
    updated = client.patch(f"/api/records/{record_id}", json=payload)
    assert updated.status_code == 200 and updated.json()["ttl"] == 600
    assert updated.json()["routing_policy"] == "Weighted"
    assert client.delete(f"/api/records/{record_id}").status_code == 204
    assert client.delete(f"/api/records/{record_id}").status_code == 404


@pytest.mark.parametrize(("kind", "value"), [
    ("A", "999.1.1.1"), ("AAAA", "not:ipv6"), ("CNAME", "bad hostname!"),
    ("MX", "70000 mail.example.test"), ("NS", "bad hostname!"), ("PTR", "bad hostname!"),
    ("SRV", "-1 0 53 target.example.test"), ("CAA", "999 issue ca.example"),
    ("SOA", "ns.example.test hostmaster.example.test 1 2 3"),
])
def test_invalid_record_values_return_422(client, kind, value):
    zone = create_zone(client, f"bad-{kind.lower()}.test")
    response = client.post(f"/api/zones/{zone['id']}/records", json={"name": "invalid", "type": kind, "value": value})
    assert response.status_code == 422, response.text


def test_exports_cors_health_pagination_and_cascade(client):
    zone = create_zone(client, "export.test")
    for index in range(3):
        response = client.post(f"/api/zones/{zone['id']}/records", json={"name": f"host{index}.export.test", "type": "A", "value": f"192.0.2.{index + 1}"})
        assert response.status_code == 201
    page = client.get(f"/api/zones/{zone['id']}/records?page=1&page_size=2")
    assert page.json()["total"] == 5 and len(page.json()["items"]) == 2
    assert client.get(f"/api/zones/{zone['id']}/export?format=json").json()["zone"]["name"] == "export.test"
    assert "$ORIGIN export.test." in client.get(f"/api/zones/{zone['id']}/export?format=bind").text
    assert client.get("/health").json() == {"status": "ok"}
    preflight = client.options("/api/zones", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
    assert preflight.status_code == 200
    assert client.delete(f"/api/zones/{zone['id']}").status_code == 204
    assert client.get(f"/api/zones/{zone['id']}/records").status_code == 404


def test_cname_exclusivity_and_soa_apex_rules(client):
    zone = create_zone(client, "conflicts.test")
    records = f"/api/zones/{zone['id']}/records"
    payload = {"name": "mail.conflicts.test", "type": "A", "value": "192.0.2.20"}
    assert client.post(records, json=payload).status_code == 201
    payload.update(type="CNAME", value="target.conflicts.test")
    assert client.post(records, json=payload).status_code == 409
    cname = {"name": "alias.conflicts.test", "type": "CNAME", "value": "target.conflicts.test"}
    assert client.post(records, json=cname).status_code == 201
    cname.update(type="TXT", value="text")
    assert client.post(records, json=cname).status_code == 409
    cname.update(type="SOA", name="sub.conflicts.test", value="ns.example.test hostmaster.example.test 1 2 3 4 5")
    assert client.post(records, json=cname).status_code == 422


def test_bind_zone_file_import(client):
    zone = create_zone(client, "import.test", private=True)
    zone_file = (
        "$ORIGIN import.test.\n"
        "$TTL 300\n"
        "; a comment line should be ignored\n"
        "www.import.test. 300 IN A 192.0.2.10\n"
        "mail.import.test. IN MX 10 mail.import.test.\n"
        "not a valid record line\n"
        "txt.import.test. 300 IN TXT \"hello world\"\n"
    )
    response = client.post(f"/api/zones/{zone['id']}/import", json={"content": zone_file})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["imported"] == 3
    assert len(body["skipped"]) == 1
    records = client.get(f"/api/zones/{zone['id']}/records").json()
    assert records["total"] == 3
    assert {r["type"] for r in records["items"]} == {"A", "MX", "TXT"}
    empty = client.post(f"/api/zones/{zone['id']}/import", json={"content": "   "})
    assert empty.status_code == 422
