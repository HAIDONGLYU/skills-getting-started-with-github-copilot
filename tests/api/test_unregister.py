"""Tests for DELETE /activities/{activity_name}/unregister endpoint"""

import pytest


def test_unregister_valid_participant(client, clean_activities, sample_activity):
    """Test successful unregister: participant is removed from activity"""
    activity_name = sample_activity["name"]
    email = sample_activity["existing_participant"]
    initial_count = len(clean_activities[activity_name]["participants"])
    
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 200
    assert email not in clean_activities[activity_name]["participants"]
    assert len(clean_activities[activity_name]["participants"]) == initial_count - 1


def test_unregister_response_message(client, clean_activities, sample_activity):
    """Test unregister response message format"""
    activity_name = sample_activity["name"]
    email = sample_activity["existing_participant"]
    
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]


def test_unregister_activity_not_found(client, clean_activities):
    """Test unregister error: activity does not exist returns 404"""
    response = client.delete(
        "/activities/NonexistentActivity/unregister",
        params={"email": "test@mergington.edu"}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]


def test_unregister_participant_not_found(client, clean_activities, sample_activity):
    """Test unregister error: participant not registered returns 404"""
    activity_name = sample_activity["name"]
    email = "notregistered@mergington.edu"
    
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Participant not found" in data["detail"]


def test_unregister_disappears_from_get_activities(client, clean_activities, sample_activity):
    """Test unregister: removed participant disappears from GET /activities response"""
    activity_name = sample_activity["name"]
    email = sample_activity["existing_participant"]
    
    # Unregister
    client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    # Verify not in GET response
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    assert email not in activities[activity_name]["participants"]


def test_unregister_updates_participant_count(client, clean_activities, sample_activity):
    """Test unregister: participant count decreases in GET /activities response"""
    activity_name = sample_activity["name"]
    email = sample_activity["existing_participant"]
    
    # Get initial count
    response = client.get("/activities")
    activities = response.json()
    initial_count = len(activities[activity_name]["participants"])
    
    # Unregister
    client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    # Get updated count
    response = client.get("/activities")
    activities = response.json()
    new_count = len(activities[activity_name]["participants"])
    
    assert new_count == initial_count - 1


def test_unregister_one_of_many_participants(client, clean_activities, sample_activity):
    """Test unregister: removing one participant doesn't affect others"""
    activity_name = sample_activity["name"]
    email_to_remove = sample_activity["existing_participant"]
    
    # Get other existing participants
    other_participants = [
        email for email in clean_activities[activity_name]["participants"]
        if email != email_to_remove
    ]
    
    # Unregister one
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email_to_remove}
    )
    
    assert response.status_code == 200
    
    # Verify others remain
    for other_email in other_participants:
        assert other_email in clean_activities[activity_name]["participants"]


def test_unregister_missing_email_parameter(client, clean_activities, sample_activity):
    """Test unregister error: missing email parameter returns 422"""
    activity_name = sample_activity["name"]
    
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={}
    )
    
    assert response.status_code == 422


def test_unregister_empty_email(client, clean_activities, sample_activity):
    """Test unregister error: empty email string is rejected"""
    activity_name = sample_activity["name"]
    
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": ""}
    )
    
    # Should either return 422 (validation) or 404 (not found)
    assert response.status_code in [404, 422]


def test_unregister_response_has_message_field(client, clean_activities, sample_activity):
    """Test successful unregister response always contains message field"""
    activity_name = sample_activity["name"]
    email = sample_activity["existing_participant"]
    
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0
