"""add_performance_indexes

Revision ID: 20260227_160145
Revises: f62984ab805f
Create Date: 2026-02-27 16:01:45

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260227_160145'
down_revision: Union[str, Sequence[str], None] = '20260227102116'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for high-frequency query patterns.
    
    This migration adds B-Tree indexes to:
    - Foreign key columns for efficient JOIN operations
    - Timestamp columns for efficient sorting (ORDER BY)
    - Status/category columns for efficient filtering (WHERE)
    """
    
    # ==================== FOREIGN KEY INDEXES ====================
    # These indexes optimize JOIN operations and user_id lookups
    
    # otp_codes table - user_id lookups
    op.create_index(
        op.f('ix_otp_codes_user_id'), 
        'otp_codes', 
        ['user_id'], 
        unique=False
    )
    
    # password_history table - user_id lookups
    op.create_index(
        op.f('ix_password_history_user_id'), 
        'password_history', 
        ['user_id'], 
        unique=False
    )
    
    # refresh_tokens table - user_id lookups
    op.create_index(
        op.f('ix_refresh_tokens_user_id'), 
        'refresh_tokens', 
        ['user_id'], 
        unique=False
    )
    
    # analytics_events table - user_id lookups
    op.create_index(
        op.f('ix_analytics_events_user_id'), 
        'analytics_events', 
        ['user_id'], 
        unique=False
    )
    
    # scores table - user_id lookups
    op.create_index(
        op.f('ix_scores_user_id'), 
        'scores', 
        ['user_id'], 
        unique=False
    )
    
    # responses table - user_id lookups
    op.create_index(
        op.f('ix_responses_user_id'), 
        'responses', 
        ['user_id'], 
        unique=False
    )
    
    # journal_entries table - user_id lookups
    op.create_index(
        op.f('ix_journal_entries_user_id'), 
        'journal_entries', 
        ['user_id'], 
        unique=False
    )
    
    # assessment_results table - user_id lookups
    op.create_index(
        op.f('ix_assessment_results_user_id'), 
        'assessment_results', 
        ['user_id'], 
        unique=False
    )
    
    # assessment_results table - journal_entry_id lookups
    op.create_index(
        op.f('ix_assessment_results_journal_entry_id'), 
        'assessment_results', 
        ['journal_entry_id'], 
        unique=False
    )
    
    # ==================== TIMESTAMP INDEXES ====================
    # These indexes optimize ORDER BY and range queries
    
    # otp_codes table - created_at sorting
    op.create_index(
        op.f('ix_otp_codes_created_at'), 
        'otp_codes', 
        ['created_at'], 
        unique=False
    )
    
    # otp_codes table - expires_at for cleanup queries
    op.create_index(
        op.f('ix_otp_codes_expires_at'), 
        'otp_codes', 
        ['expires_at'], 
        unique=False
    )
    
    # password_history table - created_at sorting
    op.create_index(
        op.f('ix_password_history_created_at'), 
        'password_history', 
        ['created_at'], 
        unique=False
    )
    
    # refresh_tokens table - created_at sorting
    op.create_index(
        op.f('ix_refresh_tokens_created_at'), 
        'refresh_tokens', 
        ['created_at'], 
        unique=False
    )
    
    # refresh_tokens table - expires_at for cleanup queries
    op.create_index(
        op.f('ix_refresh_tokens_expires_at'), 
        'refresh_tokens', 
        ['expires_at'], 
        unique=False
    )
    
    # scores table - timestamp sorting
    op.create_index(
        op.f('ix_scores_timestamp'), 
        'scores', 
        ['timestamp'], 
        unique=False
    )
    
    # responses table - timestamp sorting
    op.create_index(
        op.f('ix_responses_timestamp'), 
        'responses', 
        ['timestamp'], 
        unique=False
    )
    
    # journal_entries table - timestamp sorting
    op.create_index(
        op.f('ix_journal_entries_timestamp'), 
        'journal_entries', 
        ['timestamp'], 
        unique=False
    )
    
    # journal_entries table - entry_date for date-based queries
    op.create_index(
        op.f('ix_journal_entries_entry_date'), 
        'journal_entries', 
        ['entry_date'], 
        unique=False
    )
    
    # assessment_results table - timestamp sorting
    op.create_index(
        op.f('ix_assessment_results_timestamp'), 
        'assessment_results', 
        ['timestamp'], 
        unique=False
    )
    
    # challenges table - start_date and end_date for active challenges
    op.create_index(
        op.f('ix_challenges_start_date'), 
        'challenges', 
        ['start_date'], 
        unique=False
    )
    
    op.create_index(
        op.f('ix_challenges_end_date'), 
        'challenges', 
        ['end_date'], 
        unique=False
    )
    
    # ==================== STATUS/CATEGORY INDEXES ====================
    # These indexes optimize WHERE clause filtering
    
    # otp_codes table - purpose filtering
    op.create_index(
        op.f('ix_otp_codes_purpose'), 
        'otp_codes', 
        ['purpose'], 
        unique=False
    )
    
    # otp_codes table - is_used filtering
    op.create_index(
        op.f('ix_otp_codes_is_used'), 
        'otp_codes', 
        ['is_used'], 
        unique=False
    )
    
    # refresh_tokens table - is_revoked filtering
    op.create_index(
        op.f('ix_refresh_tokens_is_revoked'), 
        'refresh_tokens', 
        ['is_revoked'], 
        unique=False
    )
    
    # analytics_events table - event_name filtering
    op.create_index(
        op.f('ix_analytics_events_event_name'), 
        'analytics_events', 
        ['event_name'], 
        unique=False
    )
    
    # challenges table - is_active filtering
    op.create_index(
        op.f('ix_challenges_is_active'), 
        'challenges', 
        ['is_active'], 
        unique=False
    )
    
    # challenges table - challenge_type filtering
    op.create_index(
        op.f('ix_challenges_challenge_type'), 
        'challenges', 
        ['challenge_type'], 
        unique=False
    )
    
    # journal_entries table - category filtering
    op.create_index(
        op.f('ix_journal_entries_category'), 
        'journal_entries', 
        ['category'], 
        unique=False
    )
    
    # journal_entries table - is_deleted filtering (for soft delete)
    op.create_index(
        op.f('ix_journal_entries_is_deleted'), 
        'journal_entries', 
        ['is_deleted'], 
        unique=False
    )
    
    # journal_entries table - privacy_level filtering
    op.create_index(
        op.f('ix_journal_entries_privacy_level'), 
        'journal_entries', 
        ['privacy_level'], 
        unique=False
    )
    
    # journal_entries table - username filtering
    op.create_index(
        op.f('ix_journal_entries_username'), 
        'journal_entries', 
        ['username'], 
        unique=False
    )
    
    # scores table - session_id filtering
    op.create_index(
        op.f('ix_scores_session_id'), 
        'scores', 
        ['session_id'], 
        unique=False
    )
    
    # responses table - session_id filtering
    op.create_index(
        op.f('ix_responses_session_id'), 
        'responses', 
        ['session_id'], 
        unique=False
    )


def downgrade() -> None:
    """Remove performance indexes.
    
    Drops all indexes created by the upgrade function.
    """
    
    # Drop responses indexes
    op.drop_index(op.f('ix_responses_session_id'), table_name='responses')
    op.drop_index(op.f('ix_responses_timestamp'), table_name='responses')
    op.drop_index(op.f('ix_responses_user_id'), table_name='responses')
    
    # Drop scores indexes
    op.drop_index(op.f('ix_scores_session_id'), table_name='scores')
    op.drop_index(op.f('ix_scores_timestamp'), table_name='scores')
    op.drop_index(op.f('ix_scores_user_id'), table_name='scores')
    
    # Drop journal_entries indexes
    op.drop_index(op.f('ix_journal_entries_username'), table_name='journal_entries')
    op.drop_index(op.f('ix_journal_entries_privacy_level'), table_name='journal_entries')
    op.drop_index(op.f('ix_journal_entries_is_deleted'), table_name='journal_entries')
    op.drop_index(op.f('ix_journal_entries_category'), table_name='journal_entries')
    op.drop_index(op.f('ix_journal_entries_entry_date'), table_name='journal_entries')
    op.drop_index(op.f('ix_journal_entries_timestamp'), table_name='journal_entries')
    op.drop_index(op.f('ix_journal_entries_user_id'), table_name='journal_entries')
    
    # Drop assessment_results indexes
    op.drop_index(op.f('ix_assessment_results_timestamp'), table_name='assessment_results')
    op.drop_index(op.f('ix_assessment_results_journal_entry_id'), table_name='assessment_results')
    op.drop_index(op.f('ix_assessment_results_user_id'), table_name='assessment_results')
    
    # Drop challenges indexes
    op.drop_index(op.f('ix_challenges_challenge_type'), table_name='challenges')
    op.drop_index(op.f('ix_challenges_is_active'), table_name='challenges')
    op.drop_index(op.f('ix_challenges_end_date'), table_name='challenges')
    op.drop_index(op.f('ix_challenges_start_date'), table_name='challenges')
    
    # Drop analytics_events indexes
    op.drop_index(op.f('ix_analytics_events_event_name'), table_name='analytics_events')
    op.drop_index(op.f('ix_analytics_events_user_id'), table_name='analytics_events')
    
    # Drop refresh_tokens indexes
    op.drop_index(op.f('ix_refresh_tokens_is_revoked'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_expires_at'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_created_at'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    
    # Drop password_history indexes
    op.drop_index(op.f('ix_password_history_created_at'), table_name='password_history')
    op.drop_index(op.f('ix_password_history_user_id'), table_name='password_history')
    
    # Drop otp_codes indexes
    op.drop_index(op.f('ix_otp_codes_is_used'), table_name='otp_codes')
    op.drop_index(op.f('ix_otp_codes_purpose'), table_name='otp_codes')
    op.drop_index(op.f('ix_otp_codes_expires_at'), table_name='otp_codes')
    op.drop_index(op.f('ix_otp_codes_created_at'), table_name='otp_codes')
    op.drop_index(op.f('ix_otp_codes_user_id'), table_name='otp_codes')
