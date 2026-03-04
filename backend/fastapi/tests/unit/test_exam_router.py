import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from api.main import app
from api.services.exam_service import ExamService
from api.services.results_service import AssessmentResultsService
from api.root_models import User


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    return user


@pytest.fixture
def mock_db():
    return MagicMock()


class TestExamRouter:
    """Unit tests for exam API endpoints."""

    @patch('api.routers.exams.get_current_user')
    @patch('api.routers.exams.ExamService.start_exam')
    def test_start_exam_success(self, mock_start_exam, mock_get_user, client, mock_user, mock_db):
        """Test successful exam start."""
        mock_get_user.return_value = mock_user
        mock_start_exam.return_value = "session-123"

        with patch('backend.fastapi.api.routers.exams.get_db', return_value=mock_db):
            response = client.post("/api/v1/exams/start")

        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == "session-123"

    @patch('api.routers.exams.get_current_user')
    @patch('api.routers.exams.ExamService.save_response')
    def test_save_response_success(self, mock_save_response, mock_get_user, client, mock_user, mock_db):
        """Test successful response saving."""
        mock_get_user.return_value = mock_user
        mock_save_response.return_value = True

        response_data = {
            "question_id": 1,
            "value": 4,
            "age_group": "adult"
        }

        with patch('backend.fastapi.api.routers.exams.get_db', return_value=mock_db):
            response = client.post("/api/v1/exams/session-123/responses", json=response_data)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"

    @patch('api.routers.exams.get_current_user')
    @patch('api.routers.exams.ExamService.save_response')
    def test_save_response_failure(self, mock_save_response, mock_get_user, client, mock_user, mock_db):
        """Test response saving failure."""
        mock_get_user.return_value = mock_user
        mock_save_response.return_value = False

        response_data = {
            "question_id": 1,
            "value": 4,
            "age_group": "adult"
        }

        with patch('backend.fastapi.api.routers.exams.get_db', return_value=mock_db):
            response = client.post("/api/v1/exams/session-123/responses", json=response_data)

        assert response.status_code == 500
        data = response.json()
        assert "Failed to save response" in data["detail"]

    @patch('api.routers.exams.get_current_user')
    @patch('api.routers.exams.ExamService.save_score')
    def test_complete_exam_success(self, mock_save_score, mock_get_user, client, mock_user, mock_db):
        """Test successful exam completion."""
        mock_get_user.return_value = mock_user

        mock_score = MagicMock()
        mock_score.id = 1
        mock_score.total_score = 75
        mock_score.timestamp = "2024-01-01T12:00:00"
        mock_save_score.return_value = mock_score

        result_data = {
            "age": 25,
            "total_score": 75,
            "sentiment_score": 0.8,
            "reflection_text": "Test reflection",
            "is_rushed": False,
            "is_inconsistent": False,
            "detailed_age_group": "young_adult"
        }

        with patch('backend.fastapi.api.routers.exams.get_db', return_value=mock_db):
            response = client.post("/api/v1/exams/session-123/complete", json=result_data)

        assert response.status_code == 201
        data = response.json()
        assert data["assessment_id"] == 1
        assert data["total_score"] == 75
        assert data["timestamp"] == "2024-01-01T12:00:00"

    @patch('api.routers.exams.get_current_user')
    @patch('api.routers.exams.ExamService.save_score')
    def test_complete_exam_save_failure(self, mock_save_score, mock_get_user, client, mock_user, mock_db):
        """Test exam completion failure."""
        mock_get_user.return_value = mock_user
        mock_save_score.side_effect = Exception("DB Error")

        result_data = {
            "age": 25,
            "total_score": 75,
            "sentiment_score": 0.8,
            "reflection_text": "Test reflection",
            "is_rushed": False,
            "is_inconsistent": False,
            "detailed_age_group": "young_adult"
        }

        with patch('backend.fastapi.api.routers.exams.get_db', return_value=mock_db):
            response = client.post("/api/v1/exams/session-123/complete", json=result_data)

        assert response.status_code == 500
        data = response.json()
        assert "DB Error" in data["detail"]

    @patch('api.routers.exams.get_current_user')
    @patch('api.routers.exams.ExamService.get_history')
    def test_get_history_success(self, mock_get_history, mock_get_user, client, mock_user, mock_db):
        """Test successful history retrieval."""
        mock_get_user.return_value = mock_user

        mock_score1 = MagicMock()
        mock_score1.id = 1
        mock_score1.total_score = 75
        mock_score1.timestamp = "2024-01-01T12:00:00"

        mock_score2 = MagicMock()
        mock_score2.id = 2
        mock_score2.total_score = 80
        mock_score2.timestamp = "2024-01-02T12:00:00"

        mock_get_history.return_value = ([mock_score1, mock_score2], 2)

        with patch('backend.fastapi.api.routers.exams.get_db', return_value=mock_db):
            response = client.get("/api/v1/exams/history?skip=0&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["assessments"]) == 2
        assert data["total"] == 2
        assert data["assessments"][0]["id"] == 1
        assert data["assessments"][1]["id"] == 2

    @patch('api.routers.exams.get_current_user')
    @patch('api.routers.exams.AssessmentResultsService.get_detailed_results')
    def test_get_detailed_results_success(self, mock_get_detailed, mock_get_user, client, mock_user, mock_db):
        """Test successful detailed results retrieval."""
        mock_get_user.return_value = mock_user

        mock_result = MagicMock()
        mock_result.assessment_id = 1
        mock_result.total_score = 75.0
        mock_result.max_possible_score = 100.0
        mock_result.overall_percentage = 75.0
        mock_result.timestamp = "2024-01-01T12:00:00"
        mock_result.category_breakdown = []
        mock_result.recommendations = []

        mock_get_detailed.return_value = mock_result

        with patch('backend.fastapi.api.routers.exams.get_db', return_value=mock_db):
            response = client.get("/api/v1/exams/1/results")

        assert response.status_code == 200
        data = response.json()
        assert data["assessment_id"] == 1
        assert data["total_score"] == 75.0
        assert data["max_possible_score"] == 100.0

    @patch('api.routers.exams.get_current_user')
    @patch('api.routers.exams.AssessmentResultsService.get_detailed_results')
    def test_get_detailed_results_not_found(self, mock_get_detailed, mock_get_user, client, mock_user, mock_db):
        """Test detailed results not found."""
        mock_get_user.return_value = mock_user
        mock_get_detailed.return_value = None

        with patch('backend.fastapi.api.routers.exams.get_db', return_value=mock_db):
            response = client.get("/api/v1/exams/999/results")

        assert response.status_code == 404
        data = response.json()
        assert "Assessment not found" in data["detail"]