"""Unit tests for activities data model and operations"""

import pytest
from src.app import activities


def test_activities_dict_exists():
    """Test that activities dictionary exists and is not empty"""
    assert activities is not None
    assert isinstance(activities, dict)
    assert len(activities) > 0


def test_activities_have_required_keys():
    """Test each activity in the activities dict has required keys"""
    required_keys = {"description", "schedule", "max_participants", "participants"}
    
    for activity_name, activity_data in activities.items():
        assert isinstance(activity_name, str)
        for key in required_keys:
            assert key in activity_data, f"Activity '{activity_name}' missing key '{key}'"


def test_activities_participants_is_list():
    """Test that participants field is always a list"""
    for activity_name, activity_data in activities.items():
        assert isinstance(activity_data["participants"], list), \
            f"Participants for '{activity_name}' should be a list"


def test_activities_max_participants_is_positive_int():
    """Test that max_participants is a positive integer"""
    for activity_name, activity_data in activities.items():
        assert isinstance(activity_data["max_participants"], int), \
            f"max_participants for '{activity_name}' should be an integer"
        assert activity_data["max_participants"] > 0, \
            f"max_participants for '{activity_name}' should be positive"


def test_activities_description_is_string():
    """Test that description field is always a string"""
    for activity_name, activity_data in activities.items():
        assert isinstance(activity_data["description"], str), \
            f"Description for '{activity_name}' should be string"
        assert len(activity_data["description"]) > 0, \
            f"Description for '{activity_name}' should not be empty"


def test_activities_schedule_is_string():
    """Test that schedule field is always a string"""
    for activity_name, activity_data in activities.items():
        assert isinstance(activity_data["schedule"], str), \
            f"Schedule for '{activity_name}' should be string"
        assert len(activity_data["schedule"]) > 0, \
            f"Schedule for '{activity_name}' should not be empty"


def test_participant_count_does_not_exceed_max():
    """Test that participant count never exceeds max_participants"""
    for activity_name, activity_data in activities.items():
        participant_count = len(activity_data["participants"])
        max_participants = activity_data["max_participants"]
        assert participant_count <= max_participants, \
            f"Activity '{activity_name}' has {participant_count} participants but max is {max_participants}"


def test_participants_are_strings():
    """Test that all participants are valid email strings (non-empty)"""
    for activity_name, activity_data in activities.items():
        for participant in activity_data["participants"]:
            assert isinstance(participant, str), \
                f"Participant in '{activity_name}' should be string, got {type(participant)}"
            assert len(participant) > 0, \
                f"Participant email in '{activity_name}' should not be empty"


def test_duplicate_participants_not_allowed(clean_activities):
    """Test that each activity doesn't have duplicate participants"""
    for activity_name, activity_data in clean_activities.items():
        participants = activity_data["participants"]
        unique_participants = set(participants)
        assert len(participants) == len(unique_participants), \
            f"Activity '{activity_name}' has duplicate participants"


def test_activity_names_are_unique():
    """Test that activity names are unique keys in the dict"""
    activity_names = list(activities.keys())
    unique_names = set(activity_names)
    assert len(activity_names) == len(unique_names), "Activity names should be unique"


def test_activities_data_immutability_not_corrupted():
    """Test that reading activities multiple times returns consistent data"""
    snapshot1 = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    # Read again
    snapshot2 = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    assert snapshot1 == snapshot2, "Reading activities multiple times should return same data"


class TestActivityDataValidation:
    """Test suite for activity data validation"""
    
    def test_all_activities_have_description(self):
        """Each activity must have a non-empty description"""
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert isinstance(activity_data["description"], str)
            assert len(activity_data["description"]) > 0
    
    def test_all_activities_have_schedule(self):
        """Each activity must have a non-empty schedule"""
        for activity_name, activity_data in activities.items():
            assert "schedule" in activity_data
            assert isinstance(activity_data["schedule"], str)
            assert len(activity_data["schedule"]) > 0
    
    def test_max_participants_reasonable_value(self):
        """max_participants should be a reasonable positive number"""
        for activity_name, activity_data in activities.items():
            max_p = activity_data["max_participants"]
            # Reasonable range: between 1 and 1000
            assert 1 <= max_p <= 1000, \
                f"Activity '{activity_name}' has unreasonable max_participants: {max_p}"


class TestParticipantManagement:
    """Test suite for participant list management logic"""
    
    def test_participant_list_operations_valid(self, clean_activities):
        """Test that participant list can be manipulated safely"""
        activity = list(clean_activities.values())[0]
        original_count = len(activity["participants"])
        
        # Simulate add
        test_email = "testmanagement@mergington.edu"
        if test_email not in activity["participants"]:
            activity["participants"].append(test_email)
            assert len(activity["participants"]) == original_count + 1
            
            # Verify it exists
            assert test_email in activity["participants"]
            
            # Simulate remove
            activity["participants"].remove(test_email)
            assert len(activity["participants"]) == original_count
            assert test_email not in activity["participants"]
