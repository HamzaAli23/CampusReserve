from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from campusreserve.database import get_session, make_engine
from campusreserve.main import app


def make_client(tmp_path: Path) -> TestClient:
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)

    def session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    return TestClient(app)


def resource(client: TestClient) -> int:
    response = client.post("/api/resources", json={"name": "Lab 1", "kind": "Computer lab", "capacity": 20})
    assert response.status_code == 201
    return response.json()["id"]


def booking_payload(resource_id: int, start: str, end: str) -> dict[str, object]:
    return {"resource_id": resource_id, "booked_by": "Hamza", "starts_at": start, "ends_at": end, "purpose": "Study"}


def test_health_and_static_home(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        home = client.get("/").text
        assert "CampusReserve" in home
        assert "Not an official AYBU service" in home
        assert "data-cancel-id" in home


def test_conflict_and_adjacent_booking_rules(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        resource_id = resource(client)
        first = booking_payload(resource_id, "2026-09-11T10:00:00Z", "2026-09-11T11:00:00Z")
        assert client.post("/api/bookings", json=first).status_code == 201
        overlapping = booking_payload(resource_id, "2026-09-11T10:30:00Z", "2026-09-11T11:30:00Z")
        assert client.post("/api/bookings", json=overlapping).status_code == 409
        adjacent = booking_payload(resource_id, "2026-09-11T11:00:00Z", "2026-09-11T12:00:00Z")
        assert client.post("/api/bookings", json=adjacent).status_code == 201


def test_cancelled_time_can_be_rebooked(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        resource_id = resource(client)
        payload = booking_payload(resource_id, "2026-09-12T10:00:00+03:00", "2026-09-12T11:00:00+03:00")
        created = client.post("/api/bookings", json=payload)
        booking_id = created.json()["id"]
        assert client.post(f"/api/bookings/{booking_id}/cancel").json()["status"] == "cancelled"
        assert client.post("/api/bookings", json=payload).status_code == 201


def test_rejects_invalid_interval_and_missing_resource(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        invalid = booking_payload(999, "2026-09-11T11:00:00Z", "2026-09-11T10:00:00Z")
        assert client.post("/api/bookings", json=invalid).status_code == 422
        missing = booking_payload(999, "2026-09-11T10:00:00Z", "2026-09-11T11:00:00Z")
        assert client.post("/api/bookings", json=missing).status_code == 404


def test_resources_are_sorted_and_booking_list_is_persisted(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        second = client.post("/api/resources", json={"name": "Room Z-201", "kind": "Seminar room", "capacity": 12})
        first = client.post("/api/resources", json={"name": "Lab A-101", "kind": "Computer lab", "capacity": 24})
        assert second.status_code == first.status_code == 201
        resources = client.get("/api/resources").json()
        assert [item["name"] for item in resources] == ["Lab A-101", "Room Z-201"]

        payload = booking_payload(first.json()["id"], "2026-09-14T09:00:00+03:00", "2026-09-14T10:00:00+03:00")
        assert client.post("/api/bookings", json=payload).status_code == 201
        bookings = client.get("/api/bookings").json()
        assert len(bookings) == 1
        assert bookings[0]["booked_by"] == "Hamza"
        assert bookings[0]["starts_at"].endswith("Z")
        assert bookings[0]["ends_at"].endswith("Z")
