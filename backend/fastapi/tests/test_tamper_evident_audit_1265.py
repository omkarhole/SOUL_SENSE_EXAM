import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from api.services.tamper_evident_audit_service import TamperEvidentAuditService
from api.services.audit_service import AuditService
from api.models import AuditLog

class TestTamperEvidentAuditService:
    """Test suite for tamper-evident audit logging (#1265)."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for testing."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def sample_log_data(self):
        """Sample audit log data for testing."""
        return {
            "user_id": 123,
            "action": "LOGIN",
            "details": {"ip_address": "192.168.1.1", "user_agent": "Test Browser"},
            "timestamp": "2024-01-01T12:00:00.000000+00:00"
        }

    def test_generate_content_hash(self, sample_log_data):
        """Test SHA-256 content hash generation."""
        service = TamperEvidentAuditService()

        # Generate hash
        content_hash = service._generate_content_hash(
            user_id=sample_log_data["user_id"],
            action=sample_log_data["action"],
            details='{"ip_address": "192.168.1.1", "user_agent": "Test Browser"}',
            timestamp=sample_log_data["timestamp"],
            previous_hash=service.GENESIS_HASH
        )

        # Verify hash is valid SHA-256
        assert len(content_hash) == 64
        assert content_hash.isalnum()
        assert content_hash.islower()

        # Verify hash is deterministic
        content_hash2 = service._generate_content_hash(
            user_id=sample_log_data["user_id"],
            action=sample_log_data["action"],
            details='{"ip_address": "192.168.1.1", "user_agent": "Test Browser"}',
            timestamp=sample_log_data["timestamp"],
            previous_hash=service.GENESIS_HASH
        )
        assert content_hash == content_hash2

        # Verify hash changes with different input
        content_hash3 = service._generate_content_hash(
            user_id=456,  # Different user_id
            action=sample_log_data["action"],
            details='{"ip_address": "192.168.1.1", "user_agent": "Test Browser"}',
            timestamp=sample_log_data["timestamp"],
            previous_hash=service.GENESIS_HASH
        )
        assert content_hash != content_hash3

    def test_generate_chain_hash(self):
        """Test running chain hash generation."""
        service = TamperEvidentAuditService()

        current_hash = "abcd1234" * 8  # 64 chars
        previous_chain_hash = "efgh5678" * 8  # 64 chars

        chain_hash = service._generate_chain_hash(current_hash, previous_chain_hash)

        # Verify hash is valid SHA-256
        assert len(chain_hash) == 64
        assert chain_hash.isalnum()
        assert chain_hash.islower()

        # Verify hash is deterministic
        chain_hash2 = service._generate_chain_hash(current_hash, previous_chain_hash)
        assert chain_hash == chain_hash2

    @pytest.mark.asyncio
    async def test_get_last_log_entry_empty_chain(self, mock_db_session):
        """Test getting last log entry when chain is empty."""
        service = TamperEvidentAuditService()

        # Mock empty result
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        last_entry = await service.get_last_log_entry(mock_db_session)

        assert last_entry is None
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_event_with_hash_chain_first_entry(self, mock_db_session, sample_log_data):
        """Test logging first entry in tamper-evident chain."""
        service = TamperEvidentAuditService()

        # Mock empty chain (no previous entries)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Mock successful commit
        mock_db_session.commit = AsyncMock()

        success = await service.log_event_with_hash_chain(
            user_id=sample_log_data["user_id"],
            action=sample_log_data["action"],
            details=sample_log_data["details"],
            db_session=mock_db_session
        )

        assert success is True

        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

        # Verify the added log entry
        added_entry = mock_db_session.add.call_args[0][0]
        assert isinstance(added_entry, AuditLog)
        assert added_entry.user_id == sample_log_data["user_id"]
        assert added_entry.action == sample_log_data["action"]
        assert added_entry.previous_hash == service.GENESIS_HASH
        assert len(added_entry.current_hash) == 64
        assert len(added_entry.chain_hash) == 64

    @pytest.mark.asyncio
    async def test_validate_chain_integrity_valid_chain(self, mock_db_session):
        """Test chain integrity validation with valid chain."""
        service = TamperEvidentAuditService()

        # Create mock entries with valid hash chain
        mock_entries = []
        previous_hash = service.GENESIS_HASH
        previous_chain_hash = service.GENESIS_HASH

        for i in range(3):
            entry = AsyncMock()
            entry.id = i + 1
            entry.user_id = 123
            entry.action = f"ACTION_{i}"
            entry.details = f'{{"count": {i}}}'
            entry.timestamp = "2024-01-01T12:00:00.000000+00:00"

            # Generate valid hashes
            entry.current_hash = service._generate_content_hash(
                entry.user_id, entry.action, entry.details, entry.timestamp, previous_hash
            )
            entry.chain_hash = service._generate_chain_hash(entry.current_hash, previous_chain_hash)
            entry.previous_hash = previous_hash

            mock_entries.append(entry)

            # Update for next iteration
            previous_hash = entry.current_hash
            previous_chain_hash = entry.chain_hash

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalars.return_value = mock_entries
        mock_db_session.execute.return_value = mock_result

        is_valid, errors = await service.validate_chain_integrity(mock_db_session, max_entries=10)

        assert is_valid is True
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_validate_chain_integrity_broken_chain(self, mock_db_session):
        """Test chain integrity validation with broken hash links."""
        service = TamperEvidentAuditService()

        # Create mock entries with broken hash chain
        mock_entries = []

        for i in range(2):
            entry = AsyncMock()
            entry.id = i + 1
            entry.user_id = 123
            entry.action = f"ACTION_{i}"
            entry.details = f'{{"count": {i}}}'
            entry.timestamp = "2024-01-01T12:00:00.000000+00:00"

            if i == 0:
                # First entry is valid
                entry.previous_hash = service.GENESIS_HASH
                entry.current_hash = service._generate_content_hash(
                    entry.user_id, entry.action, entry.details, entry.timestamp, entry.previous_hash
                )
                entry.chain_hash = service._generate_chain_hash(entry.current_hash, service.GENESIS_HASH)
            else:
                # Second entry has broken previous hash link
                entry.previous_hash = "invalid_previous_hash"  # This breaks the chain
                entry.current_hash = service._generate_content_hash(
                    entry.user_id, entry.action, entry.details, entry.timestamp, entry.previous_hash
                )
                entry.chain_hash = service._generate_chain_hash(entry.current_hash, "invalid_chain_hash")

            mock_entries.append(entry)

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalars.return_value = mock_entries
        mock_db_session.execute.return_value = mock_result

        is_valid, errors = await service.validate_chain_integrity(mock_db_session, max_entries=10)

        assert is_valid is False
        assert len(errors) > 0
        assert "broken_previous_hash_link" in str(errors)

    @pytest.mark.asyncio
    async def test_get_chain_status(self, mock_db_session):
        """Test getting comprehensive chain status."""
        service = TamperEvidentAuditService()

        # Mock last entry
        mock_last_entry = AsyncMock()
        mock_last_entry.id = 42
        mock_last_entry.chain_hash = "test_chain_hash" * 4  # 64 chars

        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 100

        # Mock validation as valid
        with patch.object(service, 'validate_chain_integrity', return_value=(True, [])):
            with patch.object(service, 'get_last_log_entry', return_value=mock_last_entry):
                with patch('sqlalchemy.sql.functions.count') as mock_count:
                    mock_count.return_value = AsyncMock()
                    mock_count.return_value.scalar = AsyncMock(return_value=100)

                    status = await service.get_chain_status(mock_db_session)

                    assert status["total_entries"] == 100
                    assert status["last_entry_id"] == 42
                    assert status["chain_valid"] is True
                    assert len(status["validation_errors"]) == 0
                    assert status["genesis_hash"] == service.GENESIS_HASH

    @pytest.mark.asyncio
    async def test_detect_tampering_no_tampering(self, mock_db_session):
        """Test tampering detection with clean chain."""
        service = TamperEvidentAuditService()

        # Create valid chain
        mock_entries = []
        previous_hash = service.GENESIS_HASH

        for i in range(2):
            entry = AsyncMock()
            entry.id = i + 1
            entry.user_id = 123
            entry.action = f"ACTION_{i}"
            entry.details = f'{{"count": {i}}}'
            entry.timestamp = "2024-01-01T12:00:00.000000+00:00"
            entry.previous_hash = previous_hash
            entry.current_hash = service._generate_content_hash(
                entry.user_id, entry.action, entry.details, entry.timestamp, entry.previous_hash
            )
            mock_entries.append(entry)
            previous_hash = entry.current_hash

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalars.return_value = mock_entries
        mock_db_session.execute.return_value = mock_result

        suspicious_entries = await service.detect_tampering(mock_db_session)

        assert len(suspicious_entries) == 0

    @pytest.mark.asyncio
    async def test_detect_tampering_with_broken_links(self, mock_db_session):
        """Test tampering detection with broken hash links."""
        service = TamperEvidentAuditService()

        # Create chain with broken link
        mock_entries = []

        for i in range(2):
            entry = AsyncMock()
            entry.id = i + 1
            entry.user_id = 123
            entry.action = f"ACTION_{i}"
            entry.details = f'{{"count": {i}}}'
            entry.timestamp = "2024-01-01T12:00:00.000000+00:00"

            if i == 0:
                entry.previous_hash = service.GENESIS_HASH
                entry.current_hash = service._generate_content_hash(
                    entry.user_id, entry.action, entry.details, entry.timestamp, entry.previous_hash
                )
            else:
                # Break the chain
                entry.previous_hash = "tampered_hash"
                entry.current_hash = "also_tampered"

            mock_entries.append(entry)

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalars.return_value = mock_entries
        mock_db_session.execute.return_value = mock_result

        suspicious_entries = await service.detect_tampering(mock_db_session)

        assert len(suspicious_entries) > 0
        assert any("broken_previous_hash_link" in str(entry) for entry in suspicious_entries)

class TestAuditServiceIntegration:
    """Test integration between AuditService and TamperEvidentAuditService."""

    @pytest.mark.asyncio
    async def test_log_event_uses_tamper_evident_service(self, mock_db_session):
        """Test that AuditService.log_event now uses tamper-evident logging."""
        # Mock the tamper-evident service
        with patch('api.services.audit_service.TamperEvidentAuditService.log_event_with_hash_chain') as mock_log:
            mock_log.return_value = True

            success = await AuditService.log_event(
                user_id=123,
                action="TEST_ACTION",
                details={"test": "data"},
                db_session=mock_db_session
            )

            assert success is True
            mock_log.assert_called_once_with(
                user_id=123,
                action="TEST_ACTION",
                ip_address="SYSTEM",
                user_agent=None,
                details={"test": "data"},
                db_session=mock_db_session
            )

    @pytest.mark.asyncio
    async def test_validate_chain_integrity_delegates(self, mock_db_session):
        """Test that AuditService.validate_chain_integrity delegates to TamperEvidentAuditService."""
        expected_result = (True, [])

        with patch('api.services.audit_service.TamperEvidentAuditService.validate_chain_integrity',
                  return_value=expected_result) as mock_validate:

            result = await AuditService.validate_chain_integrity(mock_db_session, max_entries=50)

            assert result == expected_result
            mock_validate.assert_called_once_with(mock_db_session, 50)

    @pytest.mark.asyncio
    async def test_get_chain_status_delegates(self, mock_db_session):
        """Test that AuditService.get_chain_status delegates to TamperEvidentAuditService."""
        expected_status = {"chain_valid": True, "total_entries": 10}

        with patch('api.services.audit_service.TamperEvidentAuditService.get_chain_status',
                  return_value=expected_status) as mock_status:

            result = await AuditService.get_chain_status(mock_db_session)

            assert result == expected_status
            mock_status.assert_called_once_with(mock_db_session)