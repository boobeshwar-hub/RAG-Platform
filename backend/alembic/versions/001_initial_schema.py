"""001_initial_schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-10-15 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Enable pgvector extension if PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), unique=True, index=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), server_default="user", nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # Documents
    op.create_table(
        'documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('storage_key', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('checksum_sha256', sa.String(64), nullable=False, index=True),
        sa.Column('processing_status', sa.String(50), server_default="pending", nullable=False),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.Text(), server_default="{}", nullable=False),
        sa.Column('upload_timestamp', sa.DateTime(), nullable=False),
    )

    # Document Chunks
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('page_or_sheet_location', sa.String(150), server_default="Passage 1", nullable=False),
        sa.Column('metadata_json', sa.Text(), server_default="{}", nullable=False),
        sa.Column('embedding', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # Claims
    op.create_table(
        'claims',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('chunk_id', sa.String(36), sa.ForeignKey('document_chunks.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('claim_text', sa.Text(), nullable=False),
        sa.Column('subject', sa.String(255), nullable=False, index=True),
        sa.Column('property', sa.String(255), nullable=False),
        sa.Column('context_date', sa.String(100), nullable=True),
        sa.Column('context_scope', sa.String(255), nullable=True),
        sa.Column('source_authority', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), server_default="extracted", nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # Conflicts
    op.create_table(
        'conflicts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('subject', sa.String(255), nullable=False, index=True),
        sa.Column('claim_a_id', sa.String(36), sa.ForeignKey('claims.id', ondelete='SET NULL'), nullable=True),
        sa.Column('claim_b_id', sa.String(36), sa.ForeignKey('claims.id', ondelete='SET NULL'), nullable=True),
        sa.Column('relationship_type', sa.String(50), server_default="contradicts", nullable=False),
        sa.Column('conflict_category', sa.String(100), server_default="factual_disagreement", nullable=False),
        sa.Column('source_a_name', sa.String(255), nullable=False),
        sa.Column('source_a_location', sa.String(150), nullable=False),
        sa.Column('source_a_excerpt', sa.Text(), nullable=False),
        sa.Column('source_b_name', sa.String(255), nullable=False),
        sa.Column('source_b_location', sa.String(150), nullable=False),
        sa.Column('source_b_excerpt', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('review_status', sa.String(50), server_default="unresolved", nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Conversations
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(255), server_default="New Research Session", nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Messages
    op.create_table(
        'messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('citations_json', sa.Text(), server_default="[]", nullable=False),
        sa.Column('verification_status', sa.String(50), server_default="supported", nullable=False),
        sa.Column('verification_details_json', sa.Text(), server_default="{}", nullable=False),
        sa.Column('conflicts_detected_json', sa.Text(), server_default="[]", nullable=False),
        sa.Column('uncertainty_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('actor_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('target_type', sa.String(100), nullable=False),
        sa.Column('target_id', sa.String(100), nullable=True),
        sa.Column('details_json', sa.Text(), server_default="{}", nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
    )

def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('conflicts')
    op.drop_table('claims')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('users')
