"""
Comprehensive tests for the Mergington High School API
Using the AAA (Arrange-Act-Assert) testing pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Arrange: Define clean test data
    test_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 2,
            "participants": []
        },
        "Programming Class": {
            "description": "Learn programming fundamentals",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 3,
            "participants": ["emma@example.com"]
        }
    }
    
    # Clear and repopulate activities
    activities.clear()
    activities.update(test_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()


@pytest.fixture
def client():
    """Provide a TestClient for making requests"""
    return TestClient(app)


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        # Arrange: No setup needed, testing redirect behavior
        
        # Act: Make request to root endpoint
        response = client.get("/", follow_redirects=False)
        
        # Assert: Verify redirect status and location
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        # Arrange: Activities are set up by fixture
        
        # Act: Fetch all activities
        response = client.get("/activities")
        
        # Assert: Verify response structure and content
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 2
    
    def test_get_activities_includes_participant_info(self, client):
        # Arrange: Activities with participants exist
        
        # Act: Fetch activities
        response = client.get("/activities")
        data = response.json()
        
        # Assert: Verify participant data is included
        assert data["Chess Club"]["participants"] == []
        assert data["Programming Class"]["participants"] == ["emma@example.com"]
        assert data["Chess Club"]["max_participants"] == 2


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client):
        # Arrange: User wants to sign up for Chess Club
        activity = "Chess Club"
        email = "alice@example.com"
        
        # Act: Make signup request
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Verify successful signup
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in activities[activity]["participants"]
    
    def test_signup_duplicate_email_fails(self, client):
        # Arrange: Emma is already signed up for Programming Class
        activity = "Programming Class"
        email = "emma@example.com"
        
        # Act: Try to sign up again with same email
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Verify error response
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_at_max_capacity_fails(self, client):
        # Arrange: Fill Chess Club to capacity (max 2)
        activity = "Chess Club"
        activities[activity]["participants"] = ["user1@example.com", "user2@example.com"]
        
        # Act: Try to sign up new user when at capacity
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": "user3@example.com"}
        )
        
        # Assert: Verify capacity error
        assert response.status_code == 400
        assert "full" in response.json()["detail"]
    
    def test_signup_invalid_activity_fails(self, client):
        # Arrange: Non-existent activity name
        
        # Act: Try to sign up for non-existent activity
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "alice@example.com"}
        )
        
        # Assert: Verify not found error
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_signup_multiple_users_same_activity(self, client):
        # Arrange: Multiple users want to sign up
        activity = "Chess Club"
        users = ["alice@example.com", "bob@example.com"]
        
        # Act: Sign up first user
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": users[0]}
        )
        
        # Assert: First signup succeeds
        assert response1.status_code == 200
        
        # Act: Sign up second user
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": users[1]}
        )
        
        # Assert: Second signup succeeds, both are registered
        assert response2.status_code == 200
        assert set(activities[activity]["participants"]) == set(users)


class TestUnsignupEndpoint:
    """Tests for DELETE /activities/{activity_name}/unsignup endpoint"""
    
    def test_unsignup_successful(self, client):
        # Arrange: Emma is signed up for Programming Class
        activity = "Programming Class"
        email = "emma@example.com"
        
        # Act: Remove participant
        response = client.delete(
            f"/activities/{activity}/unsignup",
            params={"email": email}
        )
        
        # Assert: Verify successful removal
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert email not in activities[activity]["participants"]
    
    def test_unsignup_not_signed_up_fails(self, client):
        # Arrange: User is not signed up
        activity = "Chess Club"
        email = "unknown@example.com"
        
        # Act: Try to unregister user who is not signed up
        response = client.delete(
            f"/activities/{activity}/unsignup",
            params={"email": email}
        )
        
        # Assert: Verify error response
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unsignup_invalid_activity_fails(self, client):
        # Arrange: Activity doesn't exist
        
        # Act: Try to unregister from non-existent activity
        response = client.delete(
            "/activities/Phantom Club/unsignup",
            params={"email": "alice@example.com"}
        )
        
        # Assert: Verify not found error
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_unsignup_increases_available_spots(self, client):
        # Arrange: Activity is at capacity
        activity = "Chess Club"
        email = "alice@example.com"
        activities[activity]["participants"] = ["user1@example.com", email]
        
        # Act: Remove one participant
        response = client.delete(
            f"/activities/{activity}/unsignup",
            params={"email": email}
        )
        
        # Assert: Verify participant removed and signup now possible
        assert response.status_code == 200
        assert len(activities[activity]["participants"]) == 1
        
        # Try to sign up new user (should now succeed)
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": "bob@example.com"}
        )
        assert response2.status_code == 200
