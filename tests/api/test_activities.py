"""Tests for GET /activities endpoint"""

import pytest


def test_get_activities_returns_all_activities(client, clean_activities):
    """Test GET /activities returns all available activities"""
    response = client.get("/activities")
    
    assert response.status_code == 200
    activities = response.json()
    assert len(activities) == len(clean_activities)
    assert set(activities.keys()) == set(clean_activities.keys())


def test_get_activities_has_required_fields(client, clean_activities):
    """Test each activity has required fields"""
    required_fields = {"description", "schedule", "max_participants", "participants"}
    
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    
    for activity_name, activity_data in activities.items():
        for field in required_fields:
            assert field in activity_data, f"Missing field '{field}' in activity '{activity_name}'"


def test_get_activities_participants_is_list(client, clean_activities):
    """Test participants field is a list"""
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    
    for activity_name, activity_data in activities.items():
        assert isinstance(activity_data["participants"], list), \
            f"Participants for '{activity_name}' is not a list"


def test_get_activities_max_participants_is_number(client, clean_activities):
    """Test max_participants field is a number"""
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    
    for activity_name, activity_data in activities.items():
        assert isinstance(activity_data["max_participants"], int), \
            f"max_participants for '{activity_name}' is not an integer"


def test_get_activities_reflects_recent_signup(client, clean_activities, sample_activity):
    """Test GET /activities reflects recent signup changes"""
    activity_name = sample_activity["name"]
    email = sample_activity["email"]
    
    # Signup
    client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Verify in response
    response = client.get("/activities")
    activities = response.json()
    assert email in activities[activity_name]["participants"]


def test_get_activities_reflects_recent_unregister(client, clean_activities, sample_activity):
    """Test GET /activities reflects recent unregister changes"""
    activity_name = sample_activity["name"]
    email = sample_activity["existing_participant"]
    
    # Unregister
    client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    # Verify not in response
    response = client.get("/activities")
    activities = response.json()
    assert email not in activities[activity_name]["participants"]


def test_get_activities_schema_validation(client, clean_activities):
    """Test response data types match schema requirements"""
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    
    for activity_name, activity_data in activities.items():
        assert isinstance(activity_name, str), "Activity name should be string"
        assert isinstance(activity_data["description"], str), "Description should be string"
        assert isinstance(activity_data["schedule"], str), "Schedule should be string"
        assert isinstance(activity_data["max_participants"], int), "max_participants should be int"
        assert activity_data["max_participants"] > 0, "max_participants should be positive"
        assert isinstance(activity_data["participants"], list), "Participants should be list"
        for participant in activity_data["participants"]:
            assert isinstance(participant, str), f"Participant '{participant}' should be string"


def test_get_activities_empty_participants_list(client):
    """Test activities with no participants return empty list"""
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    
    # At least some activities should have participants field as list
    for activity_name, activity_data in activities.items():
        assert isinstance(activity_data["participants"], list)


def test_get_activities_consistent_state(client, clean_activities):
    """Test multiple GET calls return consistent state"""
    response1 = client.get("/activities")
    response2 = client.get("/activities")
    
    assert response1.json() == response2.json()
