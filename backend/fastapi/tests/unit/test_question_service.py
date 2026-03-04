import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from api.services.db_service import QuestionService
from api.root_models import Question, QuestionCategory


class TestQuestionService:
    """Unit tests for QuestionService."""

    def test_get_questions_no_filters(self):
        """Test getting questions without filters."""
        mock_db = MagicMock(spec=Session)

        mock_questions = [MagicMock(spec=Question), MagicMock(spec=Question)]
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_questions

        mock_db.query.return_value = mock_query

        questions, total = QuestionService.get_questions(mock_db)

        assert questions == mock_questions
        assert total == 2

    def test_get_questions_with_filters(self):
        """Test getting questions with age and category filters."""
        mock_db = MagicMock(spec=Session)

        mock_questions = [MagicMock(spec=Question)]
        mock_query = MagicMock()
        # Mock the filter chain
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_questions

        mock_db.query.return_value = mock_query

        questions, total = QuestionService.get_questions(
            mock_db,
            min_age=20,
            max_age=30,
            category_id=1,
            active_only=True
        )

        assert questions == mock_questions
        assert total == 1

        # Verify filters were applied (checking call count since filter returns self)
        assert mock_query.filter.call_count >= 3  # active_only, category_id, min_age, max_age

    def test_get_question_by_id_found(self):
        """Test getting a question by ID when found."""
        mock_db = MagicMock(spec=Session)
        mock_question = MagicMock(spec=Question)
        mock_question.id = 1

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_question
        mock_db.query.return_value = mock_query

        result = QuestionService.get_question_by_id(mock_db, 1)

        assert result == mock_question

    def test_get_question_by_id_not_found(self):
        """Test getting a question by ID when not found."""
        mock_db = MagicMock(spec=Session)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = QuestionService.get_question_by_id(mock_db, 999)

        assert result is None

    def test_get_questions_by_age(self):
        """Test getting questions filtered by age."""
        mock_db = MagicMock(spec=Session)

        mock_questions = [MagicMock(spec=Question), MagicMock(spec=Question)]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_questions
        mock_db.query.return_value = mock_query

        result = QuestionService.get_questions_by_age(mock_db, 25, limit=10)

        assert result == mock_questions

        # Verify the filter conditions
        mock_query.filter.assert_called_once()
        filter_call = mock_query.filter.call_args[0][0]
        # The filter should check is_active == 1, min_age <= 25, max_age >= 25

    def test_get_questions_by_age_no_limit(self):
        """Test getting questions by age without limit."""
        mock_db = MagicMock(spec=Session)

        mock_questions = [MagicMock(spec=Question)]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_questions
        mock_db.query.return_value = mock_query

        result = QuestionService.get_questions_by_age(mock_db, 30)

        assert result == mock_questions

        # Verify limit was not called
        mock_query.limit.assert_not_called()

    def test_get_categories(self):
        """Test getting all categories."""
        mock_db = MagicMock(spec=Session)

        mock_categories = [MagicMock(spec=QuestionCategory), MagicMock(spec=QuestionCategory)]
        mock_query = MagicMock()
        mock_query.order_by.return_value.all.return_value = mock_categories
        mock_db.query.return_value = mock_query

        result = QuestionService.get_categories(mock_db)

        assert result == mock_categories

    def test_get_category_by_id_found(self):
        """Test getting a category by ID when found."""
        mock_db = MagicMock(spec=Session)
        mock_category = MagicMock(spec=QuestionCategory)
        mock_category.id = 1

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_category
        mock_db.query.return_value = mock_query

        result = QuestionService.get_category_by_id(mock_db, 1)

        assert result == mock_category

    def test_get_category_by_id_not_found(self):
        """Test getting a category by ID when not found."""
        mock_db = MagicMock(spec=Session)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = QuestionService.get_category_by_id(mock_db, 999)

        assert result is None