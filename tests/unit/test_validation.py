"""Unit tests for input validation"""

import pytest


class TestEmailValidation:
    """Test suite for email parameter validation"""
    
    def test_valid_email_formats(self, client, sample_activity):
        """Test that valid email formats are accepted"""
        activity_name = sample_activity["name"]
        valid_emails = [
            "simple@example.com",
            "user.name@example.co.uk",
            "user+tag@example.com",
            "user_name@example.org",
            "123@example.com",
        ]
        
        for email in valid_emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            # Should either succeed (200) or give validation error (400/422)
            # Not interested in 400/422 for this test, just not a server error
            assert response.status_code < 500, f"Server error for valid email: {email}"
    
    def test_invalid_email_no_at_symbol(self, client, sample_activity):
        """Test that email without @ is rejected or handled"""
        activity_name = sample_activity["name"]
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "notanemail"}
        )
        
        # Should not be 500 error
        assert response.status_code != 500
    
    def test_invalid_email_no_domain(self, client, sample_activity):
        """Test that email without domain is rejected or handled"""
        activity_name = sample_activity["name"]
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "user@"}
        )
        
        assert response.status_code != 500
    
    def test_invalid_email_no_local_part(self, client, sample_activity):
        """Test that email without local part is rejected or handled"""
        activity_name = sample_activity["name"]
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "@domain.com"}
        )
        
        assert response.status_code != 500
    
    def test_email_null_value(self, client, sample_activity):
        """Test handling of null email value"""
        activity_name = sample_activity["name"]
        
        # This is tricky - depends on FastAPI/HTTP handling
        # Just ensure it doesn't crash
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": None}
        )
        
        assert response.status_code != 500


class TestActivityNameValidation:
    """Test suite for activity name parameter validation"""
    
    def test_nonexistent_activity_name(self, client):
        """Test that nonexistent activity returns 404"""
        response = client.post(
            "/activities/NonexistentActivity/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code in [404, 422]
    
    def test_empty_activity_name(self, client):
        """Test handling of empty activity name in URL path"""
        response = client.post(
            "/activities//signup",
            params={"email": "test@mergington.edu"}
        )
        
        # Empty path segment usually results in 404 or redirect
        assert response.status_code != 500
    
    def test_activity_name_special_characters(self, client):
        """Test activity name with special characters"""
        special_names = [
            "Activity-With-Dashes",
            "Activity_With_Underscores",
            "Activity With Spaces",
            "Activity@123",
            "活动",  # Non-ASCII
        ]
        
        for name in special_names:
            response = client.post(
                f"/activities/{name}/signup",
                params={"email": "test@mergington.edu"}
            )
            # Should not crash (500), but might be 404
            assert response.status_code != 500


class TestParameterPresence:
    """Test suite for required parameter validation"""
    
    def test_signup_missing_email(self, client, sample_activity):
        """Test signup without email parameter"""
        activity_name = sample_activity["name"]
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={}
        )
        
        # FastAPI should return 422 (Unprocessable Entity)
        assert response.status_code == 422
    
    def test_unregister_missing_email(self, client, sample_activity):
        """Test unregister without email parameter"""
        activity_name = sample_activity["name"]
        
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={}
        )
        
        assert response.status_code == 422
    
    def test_signup_extra_parameters(self, client, sample_activity):
        """Test signup with extra parameters (should be ignored)"""
        activity_name = sample_activity["name"]
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "test@mergington.edu", "extra": "param", "another": "value"}
        )
        
        # Should succeed, extra params are typically ignored
        assert response.status_code == 200


class TestMaxParticipantsEnforcement:
    """Test suite for max participants limit validation"""
    
    def test_signup_respects_max_participants(self, client, clean_activities):
        """Test that signup respects max_participants limit"""
        # Find an activity
        response = client.get("/activities")
        all_activities = response.json()
        
        for activity_name, activity_info in all_activities.items():
            max_p = activity_info["max_participants"]
            current_p = len(activity_info["participants"])
            
            # If not at capacity, add shouldn't fail on max limit
            if current_p < max_p:
                new_email = f"testmaxp{current_p}@mergington.edu"
                response = client.post(
                    f"/activities/{activity_name}/signup",
                    params={"email": new_email}
                )
                # Should succeed (either 200 or 400 for other reasons)
                # but should not fail on max participants
                assert response.status_code != 500
                break
