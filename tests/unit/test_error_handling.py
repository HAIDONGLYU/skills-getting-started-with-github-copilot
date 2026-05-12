"""Unit tests for error handling and edge cases"""

import pytest


class TestErrorHandling:
    """Test suite for error handling scenarios"""
    
    def test_get_activities_always_returns_valid_response(self, client):
        """Test GET /activities always returns valid JSON"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        
        # Should be able to parse as JSON
        data = response.json()
        assert isinstance(data, dict)
    
    def test_signup_error_response_has_detail_field(self, client, sample_activity):
        """Test that error responses have proper error detail"""
        activity_name = sample_activity["name"]
        
        # Try to signup nonexistent participant to nonexistent activity
        response = client.post(
            "/activities/NonexistentActivity/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "message" in data
    
    def test_unregister_error_response_has_detail_field(self, client):
        """Test that unregister error responses have proper error detail"""
        response = client.delete(
            "/activities/NonexistentActivity/unregister",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "message" in data
    
    def test_duplicate_signup_produces_error(self, client, clean_activities, sample_activity):
        """Test that duplicate signup produces proper error"""
        activity_name = sample_activity["name"]
        existing_email = sample_activity["existing_participant"]
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestEdgeCases:
    """Test suite for edge cases"""
    
    def test_very_long_email_address(self, client, sample_activity):
        """Test handling of very long email address"""
        activity_name = sample_activity["name"]
        long_email = "a" * 200 + "@example.com"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": long_email}
        )
        
        # Should not crash (500)
        assert response.status_code != 500
    
    def test_email_with_unicode_characters(self, client, sample_activity):
        """Test handling of email with Unicode characters"""
        activity_name = sample_activity["name"]
        unicode_email = "用户@example.com"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": unicode_email}
        )
        
        # Should not crash
        assert response.status_code != 500
    
    def test_email_with_special_chars(self, client, sample_activity):
        """Test handling of email with special characters"""
        activity_name = sample_activity["name"]
        special_emails = [
            "user+test@example.com",
            "user.name@example.com",
            "user_name@example.com",
            'user"name@example.com',
        ]
        
        for email in special_emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            # Should not crash
            assert response.status_code != 500
    
    def test_unregister_nonexistent_participant(self, client, sample_activity):
        """Test unregister of completely nonexistent participant"""
        activity_name = sample_activity["name"]
        fake_email = "fakeperson123456789@fakedomain.nonexistent"
        
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": fake_email}
        )
        
        # Should be 404, not 500
        assert response.status_code == 404
    
    def test_multiple_rapid_requests(self, client, sample_activity):
        """Test handling of multiple rapid requests"""
        activity_name = sample_activity["name"]
        emails = [f"rapid{i}@example.com" for i in range(10)]
        
        responses = []
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            responses.append(response)
        
        # None should error with 500
        assert all(r.status_code != 500 for r in responses)


class TestStateLoss:
    """Test suite for state handling and potential data loss"""
    
    def test_unregister_then_check_state_consistent(self, client, clean_activities, sample_activity):
        """Test that state remains consistent after unregister"""
        activity_name = sample_activity["name"]
        email = sample_activity["existing_participant"]
        
        # Get state before
        response1 = client.get("/activities")
        before_count = len(response1.json()[activity_name]["participants"])
        
        # Unregister
        client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Get state after
        response2 = client.get("/activities")
        after_count = len(response2.json()[activity_name]["participants"])
        
        # Should have decreased by 1
        assert after_count == before_count - 1
    
    def test_signup_then_check_state_consistent(self, client, clean_activities, sample_activity):
        """Test that state remains consistent after signup"""
        activity_name = sample_activity["name"]
        email = sample_activity["email"]
        
        # Get state before
        response1 = client.get("/activities")
        before_count = len(response1.json()[activity_name]["participants"])
        
        # Signup
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Get state after
        response2 = client.get("/activities")
        after_count = len(response2.json()[activity_name]["participants"])
        
        # Should have increased by 1
        assert after_count == before_count + 1
