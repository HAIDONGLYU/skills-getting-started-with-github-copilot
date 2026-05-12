import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a FastAPI TestClient for making requests"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_activities():
    """Reset activities to a known state before and after each test"""
    # Store original state BEFORE test runs
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    # Reset state BEFORE test
    for name in activities.keys():
        activities[name]["participants"] = original_activities[name]["participants"].copy()
    
    yield activities
    
    # Restore original state AFTER test
    for name in activities.keys():
        activities[name]["participants"] = original_activities[name]["participants"].copy()


@pytest.fixture
def sample_activity():
    """Provide reference activity for testing"""
    return {
        "name": "Chess Club",
        "email": "test@mergington.edu",
        "existing_participant": "michael@mergington.edu"
    }
