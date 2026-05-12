"""Edge case tests for API endpoints"""

import pytest


class TestEdgeCasesActivities:
    """Edge case tests for GET /activities endpoint"""
    
    def test_get_activities_field_types_consistency(self, client, clean_activities):
        """Test that all response fields maintain consistent types across activities"""
        response = client.get("/activities")
        activities = response.json()
        
        # All activities should have consistent field types
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
            
            # Participants list should contain only strings (emails)
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)


class TestEdgeCasesSignup:
    """Edge case tests for signup endpoint"""
    
    def test_signup_whitespace_in_email(self, client, sample_activity):
        """Test signup with whitespace variations in email"""
        activity_name = sample_activity["name"]
        test_cases = [
            " test@example.com",          # Leading space
            "test@example.com ",          # Trailing space
            "  test@example.com  ",       # Both
            "test @example.com",          # Space in local part
            "test@ example.com",          # Space in domain
        ]
        
        for email in test_cases:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            # Should either accept, reject cleanly, or treat as invalid
            # Should never crash (500)
            assert response.status_code != 500
    
    def test_signup_case_sensitive_email(self, client, sample_activity, clean_activities):
        """Test if signup treats emails as case-insensitive"""
        activity_name = sample_activity["name"]
        email_lower = "testcase@example.com"
        email_upper = "TESTCASE@EXAMPLE.COM"
        
        # Try signup with lowercase
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email_lower}
        )
        
        if response1.status_code == 200:
            # Try signup with uppercase (same email)
            response2 = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email_upper}
            )
            
            # Either both succeed (case-sensitive storage) or
            # second one returns 400 (case-insensitive duplicate check)
            # or 200 if different emails
            assert response2.status_code in [200, 400]
    
    def test_signup_response_format_consistency(self, client, sample_activity):
        """Test that success responses always have consistent format"""
        activity_name = sample_activity["name"]
        email = sample_activity["email"]
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Response should be dictionary with message
            assert isinstance(data, dict)
            assert "message" in data
            assert isinstance(data["message"], str)
            assert len(data["message"]) > 0


class TestEdgeCasesUnregister:
    """Edge case tests for unregister endpoint"""
    
    def test_unregister_response_format_consistency(self, client, sample_activity):
        """Test that unregister responses always have consistent format"""
        activity_name = sample_activity["name"]
        email = sample_activity["existing_participant"]
        
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Response should be dictionary with message
            assert isinstance(data, dict)
            assert "message" in data
            assert isinstance(data["message"], str)
            assert len(data["message"]) > 0
    
    def test_unregister_same_participant_twice(self, client, sample_activity):
        """Test unregistering the same participant twice"""
        activity_name = sample_activity["name"]
        email = sample_activity["existing_participant"]
        
        # First unregister should succeed
        response1 = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second unregister of same participant should fail (404)
        response2 = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 404


class TestActivityNameCaseSensitivity:
    """Test suite for activity name case sensitivity"""
    
    def test_activity_names_case_preservation(self, client, clean_activities):
        """Test that activity names preserve their case"""
        response = client.get("/activities")
        activities = response.json()
        activity_names = list(activities.keys())
        
        # Activity names should preserve their original case
        # (assuming they are case-sensitive)
        response2 = client.get("/activities")
        activities2 = response2.json()
        activity_names2 = list(activities2.keys())
        
        assert activity_names == activity_names2
    
    def test_signup_activity_name_case_sensitive(self, client):
        """Test if activity name matching is case-sensitive"""
        # This will depend on implementation
        # Get a valid activity name
        response = client.get("/activities")
        activities = response.json()
        
        if activities:
            valid_name = list(activities.keys())[0]
            
            # Try with different case
            if valid_name != valid_name.lower():
                response = client.post(
                    f"/activities/{valid_name.lower()}/signup",
                    params={"email": "test@example.com"}
                )
                # Should either work (case-insensitive) or 404 (case-sensitive)
                assert response.status_code in [200, 400, 404, 422]


class TestConcurrentState:
    """Test suite for concurrent access patterns"""
    
    def test_sequential_operations_maintain_order_independence(self, client, clean_activities, sample_activity):
        """Test that operation order doesn't affect final state in obvious ways"""
        activity_name = sample_activity["name"]
        email1 = "seq1@example.com"
        email2 = "seq2@example.com"
        
        # Signup both
        client.post(f"/activities/{activity_name}/signup", params={"email": email1})
        client.post(f"/activities/{activity_name}/signup", params={"email": email2})
        
        # Unregister first
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email1}
        )
        assert response.status_code == 200
        
        # Verify second is still there
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        assert email2 in participants
        assert email1 not in participants
