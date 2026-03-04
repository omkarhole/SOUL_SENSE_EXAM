import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.fastapi.api.main import app
from backend.fastapi.api.root_models import User, Score, Response, Question, QuestionCategory
from tests.fixtures import UserFactory, ScoreFactory

client = TestClient(app)

@pytest.fixture
def auth_headers(temp_db: Session):
    """Creates a test user and returns auth headers."""
    # Create user with a known password hash (bcrypt)
    # password = "password"
    user = UserFactory.create(
        temp_db, 
        username="results_user", 
        password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    )
    
    # Create personal profile (needed for some logic)
    from backend.fastapi.api.root_models import PersonalProfile
    profile = PersonalProfile(
        user_id=user.id,
        email="results@example.com",
        first_name="Results",
        last_name="User"
    )
    temp_db.add(profile)
    temp_db.commit()
    
    response = client.post("/api/v1/auth/login", data={"identifier": "results_user", "password": "password", "captcha_input": "FIXME", "session_id": "test_session"})
    # Wait, the login schema requires captcha. Let's adjust or mock the dependency.
    # Actually, many tests just bypass login and create a token directly.
    
    from backend.fastapi.api.services.auth_service import AuthService
    auth_service = AuthService(temp_db)
    token = auth_service.create_access_token(data={"sub": "results_user"})
    
    return {"Authorization": f"Bearer {token}"}, user

def test_get_detailed_results_success(temp_db, auth_headers):
    headers, user = auth_headers
    
    # 1. Setup Categories
    cat1 = QuestionCategory(name="Self Awareness")
    cat2 = QuestionCategory(name="Empathy")
    temp_db.add_all([cat1, cat2])
    temp_db.commit()
    
    # 2. Setup Questions
    q1 = Question(question_text="How aware are you?", category_id=cat1.id, weight=1.0)
    q2 = Question(question_text="How empathetic are you?", category_id=cat2.id, weight=2.0)
    temp_db.add_all([q1, q2])
    temp_db.commit()
    
    # 3. Setup Assessment and Responses
    session_id = "test_session_123"
    # total_score = (5*1.0) + (4*2.0) = 5 + 8 = 13
    score = ScoreFactory.create(temp_db, user=user, total_score=13, session_id=session_id)
    
    resp1 = Response(
        username=user.username,
        question_id=q1.id,
        response_value=5,
        session_id=session_id
    )
    resp2 = Response(
        username=user.username,
        question_id=q2.id,
        response_value=4,
        session_id=session_id
    )
    temp_db.add_all([resp1, resp2])
    temp_db.commit()
    
    # 4. Call API
    response = client.get(f"/api/v1/exams/{score.id}/results", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["assessment_id"] == score.id
    assert data["total_score"] == 13.0
    assert len(data["category_breakdown"]) == 2
    
    # Check aggregation for "Self Awareness"
    aware_breakdown = next(c for c in data["category_breakdown"] if c["category_name"] == "Self Awareness")
    assert aware_breakdown["score"] == 5.0
    assert aware_breakdown["max_score"] == 5.0
    assert aware_breakdown["percentage"] == 100.0

    # Check aggregation for "Empathy"
    empathy_breakdown = next(c for c in data["category_breakdown"] if c["category_name"] == "Empathy")
    assert empathy_breakdown["score"] == 8.0 # 4 * 2.0
    assert empathy_breakdown["max_score"] == 10.0 # 5 * 2.0
    assert empathy_breakdown["percentage"] == 80.0

def test_get_detailed_results_unauthorized(temp_db, auth_headers):
    headers, user = auth_headers
    
    # Create assessment for ANOTHER user
    other_user = UserFactory.create(temp_db, username="other_user")
    other_score = ScoreFactory.create(temp_db, user=other_user, total_score=10)
    
    # Attempt to fetch with first user's headers
    response = client.get(f"/api/v1/exams/{other_score.id}/results", headers=headers)
    
    assert response.status_code == 404 # Should be 404 per implementation filtering by user_id

def test_get_detailed_results_not_found(temp_db, auth_headers):
    headers, user = auth_headers
    
    # Non-existent ID
    response = client.get("/api/v1/exams/99999/results", headers=headers)
    assert response.status_code == 404
