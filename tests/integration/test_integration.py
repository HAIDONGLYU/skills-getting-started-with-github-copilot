"""Integration tests for signup and unregister workflows"""

import pytest


def test_signup_then_unregister_workflow(client, clean_activities, sample_activity):
    """Test complete workflow: signup → verify → unregister → verify"""
    activity_name = sample_activity["name"]
    email = sample_activity["email"]
    
    # Step 1: Signup
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response.status_code == 200
    
    # Step 2: Verify signup in GET
    response = client.get("/activities")
    activities = response.json()
    assert email in activities[activity_name]["participants"]
    
    # Step 3: Unregister
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response.status_code == 200
    
    # Step 4: Verify removed from GET
    response = client.get("/activities")
    activities = response.json()
    assert email not in activities[activity_name]["participants"]


def test_signup_unregister_signup_again(client, clean_activities, sample_activity):
    """Test student can re-signup after unregistering"""
    activity_name = sample_activity["name"]
    email = sample_activity["email"]
    
    # First signup
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response.status_code == 200
    
    # Unregister
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response.status_code == 200
    
    # Second signup (should succeed)
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response.status_code == 200
    
    # Verify re-registered
    response = client.get("/activities")
    activities = response.json()
    assert email in activities[activity_name]["participants"]


def test_multiple_signups_then_selective_unregister(client, clean_activities, sample_activity):
    """Test multiple students signup, then unregister one, others remain"""
    activity_name = sample_activity["name"]
    students = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
    
    # All signup
    for email in students:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    # Unregister one
    email_to_remove = students[1]
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email_to_remove}
    )
    assert response.status_code == 200
    
    # Verify removed, others stay
    response = client.get("/activities")
    activities = response.json()
    participants = activities[activity_name]["participants"]
    
    assert email_to_remove not in participants
    assert students[0] in participants
    assert students[2] in participants


def test_participant_count_accuracy_with_operations(client, clean_activities, sample_activity):
    """Test participant count is accurate throughout signup/unregister operations"""
    activity_name = sample_activity["name"]
    emails = ["new1@mergington.edu", "new2@mergington.edu"]
    
    # Get initial count
    response = client.get("/activities")
    initial_count = len(response.json()[activity_name]["participants"])
    
    # Signup 2 students
    for email in emails:
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
    
    # Verify count increased by 2
    response = client.get("/activities")
    after_signup_count = len(response.json()[activity_name]["participants"])
    assert after_signup_count == initial_count + 2
    
    # Unregister 1 student
    client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": emails[0]}
    )
    
    # Verify count decreased by 1
    response = client.get("/activities")
    after_unregister_count = len(response.json()[activity_name]["participants"])
    assert after_unregister_count == initial_count + 1


def test_state_isolation_between_tests(client, clean_activities, sample_activity):
    """Test that clean_activities fixture properly isolates state between tests"""
    activity_name = sample_activity["name"]
    email = sample_activity["email"]
    
    # Add a new participant
    client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    response = client.get("/activities")
    activities_with_new = response.json()
    
    # Verify it's there
    assert email in activities_with_new[activity_name]["participants"]


def test_multiple_activities_independent_state(client, clean_activities):
    """Test that changes in one activity don't affect others"""
    response = client.get("/activities")
    all_activities = response.json()
    activity_names = list(all_activities.keys())
    
    if len(activity_names) >= 2:
        activity1 = activity_names[0]
        activity2 = activity_names[1]
        
        new_email = "multiactivity@mergington.edu"
        
        # Signup for first activity
        response = client.post(
            f"/activities/{activity1}/signup",
            params={"email": new_email}
        )
        assert response.status_code == 200
        
        # Verify first activity has the new participant
        response = client.get("/activities")
        activities = response.json()
        assert new_email in activities[activity1]["participants"]
        
        # Verify second activity doesn't have the new participant
        assert new_email not in activities[activity2]["participants"]


def test_concurrent_signup_workflow(client, clean_activities, sample_activity):
    """Test rapid signup/unregister sequence maintains consistency"""
    activity_name = sample_activity["name"]
    emails = ["conc1@mergington.edu", "conc2@mergington.edu", "conc3@mergington.edu"]
    
    # Rapid signups
    responses = []
    for email in emails:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        responses.append(response)
    
    # All should succeed
    assert all(r.status_code == 200 for r in responses)
    
    # Rapid unregisters in different order
    for email in reversed(emails):
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
    
    # Verify all removed
    response = client.get("/activities")
    activities = response.json()
    for email in emails:
        assert email not in activities[activity_name]["participants"]
