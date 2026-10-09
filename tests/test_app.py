from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    return TestClient(app_module.app)


def test_get_activities_includes_participants(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_student_and_rejects_duplicate(client):
    signup_url = "/activities/Chess%20Club/signup"

    response = client.post(signup_url, params={"email": "student@mergington.edu"})
    duplicate_response = client.post(
        signup_url, params={"email": "student@mergington.edu"}
    )

    assert response.status_code == 200
    assert duplicate_response.status_code == 400
    assert app_module.activities["Chess Club"]["participants"].count(
        "student@mergington.edu"
    ) == 1


def test_signup_rejects_unknown_and_full_activities(client):
    missing_response = client.post(
        "/activities/Unknown/signup", params={"email": "student@mergington.edu"}
    )
    app_module.activities["Full Activity"] = {
        "description": "Full",
        "schedule": "Never",
        "max_participants": 1,
        "participants": ["existing@mergington.edu"],
    }
    full_response = client.post(
        "/activities/Full%20Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert missing_response.status_code == 404
    assert full_response.status_code == 400
    assert app_module.activities["Full Activity"]["participants"] == [
        "existing@mergington.edu"
    ]


def test_unregister_removes_student_and_handles_missing_records(client):
    unregister_url = "/activities/Chess%20Club/signup"
    params = {"email": "michael@mergington.edu"}

    response = client.delete(unregister_url, params=params)
    missing_participant_response = client.delete(unregister_url, params=params)
    missing_activity_response = client.delete(
        "/activities/Unknown/signup", params=params
    )

    assert response.status_code == 200
    assert "michael@mergington.edu" not in app_module.activities["Chess Club"][
        "participants"
    ]
    assert missing_participant_response.status_code == 404
    assert missing_activity_response.status_code == 404
