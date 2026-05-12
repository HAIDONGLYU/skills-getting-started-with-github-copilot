"""Tests for POST /activities/{activity_name}/signup endpoint"""

import pytest


def test_signup_valid_student(client, clean_activities, sample_activity):
    """Test successful signup: student is added to activity participants"""
    activity_name = sample_activity["name"]
    email = sample_activity["email"]
    initial_count = len(clean_activities[activity_name]["participants"])
    
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    assert response.status_code == 200
    assert email in clean_activities[activity_name]["participants"]
    assert len(clean_activities[activity_name]["participants"]) == initial_count + 1


def test_signup_response_message(client, clean_activities, sample_activity):
    """Test signup response message format"""
    activity_name = sample_activity["name"]
    email = sample_activity["email"]
    
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]


def test_signup_activity_not_found(client, clean_activities):
    """Test signup error: activity does not exist returns 404"""
    response = client.post(
        "/activities/NonexistentActivity/signup",
        params={"email": "test@mergington.edu"}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]


def test_signup_duplicate_student(client, clean_activities, sample_activity):
    """Test signup error: student already registered returns 400"""
    activity_name = sample_activity["name"]
    existing_email = sample_activity["existing_participant"]
    
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"]


def test_signup_appears_in_get_activities(client, clean_activities, sample_activity):
    """Test signup: new participant appears in GET /activities response"""
    activity_name = sample_activity["name"]
    email = sample_activity["email"]
    
    # Signup
    client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Verify in GET response
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    assert email in activities[activity_name]["participants"]


def test_signup_multiple_students_same_activity(client, clean_activities, sample_activity):
    """Test multiple students can signup for same activity"""
    activity_name = sample_activity["name"]
    emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
    
    for email in emails:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    for email in emails:
        assert email in clean_activities[activity_name]["participants"]


def test_signup_missing_email_parameter(client, clean_activities, sample_activity):
    """Test signup error: missing email parameter returns 422"""
    activity_name = sample_activity["name"]
    
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={}
    )
    
    assert response.status_code == 422


def test_signup_empty_email(client, clean_activities, sample_activity):
    """Test signup error: empty email string is rejected"""
    activity_name = sample_activity["name"]
    
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": ""}
    )
    
    # Should either return 422 (validation) or 400 (business logic)
    assert response.status_code in [400, 422]


def test_signup_email_with_whitespace(client, clean_activities, sample_activity):
    """Test signup: email with leading/trailing whitespace"""
    activity_name = sample_activity["name"]
    email_with_spaces = "  test@mergington.edu  "
    
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email_with_spaces}
    )
    
    # Should either accept with trim or reject
    assert response.status_code in [200, 400, 422]


def test_signup_invalid_email_format(client, clean_activities, sample_activity):
    """Test signup error: invalid email format"""
    activity_name = sample_activity["name"]
    invalid_emails = [
        "notanemail",
        "missing@domain",
        "@nodomain.com",
        "user@.com",
    ]
    
    for invalid_email in invalid_emails:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": invalid_email}
        )
        # Should reject invalid emails (could be 400 or 422)
        assert response.status_code in [400, 422], f"Should reject email: {invalid_email}"


def test_signup_case_sensitivity_of_activity_name(client, clean_activities, sample_activity):
    """Test signup: activity name case sensitivity"""
    activity_name = sample_activity["name"]
    email = sample_activity["email"]
    
    # Try with different case
    response = client.post(
        f"/activities/{activity_name.lower()}/signup",
        params={"email": email}
    )
    
    # Depending on implementation, might be 404 or succeed
    assert response.status_code in [200, 404]


def test_signup_response_has_message_field(client, clean_activities, sample_activity):
    """Test successful signup response always contains message field"""
    activity_name = sample_activity["name"]
    email = sample_activity["email"]
    
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0
