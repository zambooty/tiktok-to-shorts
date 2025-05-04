"""Initial migration

Revision ID: 001
Create Date: 2025-05-04 20:37:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create videos table
    op.create_table(
        'videos',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('original_url', sa.String(512), nullable=False),
        sa.Column('original_file_path', sa.String(512)),
        sa.Column('processed_file_path', sa.String(512)),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('youtube_video_id', sa.String(50)),
        sa.Column('subtitles', sa.JSON),
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('youtube_credentials', sa.JSON),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'))
    )

    # Create processing_logs table
    op.create_table(
        'processing_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('video_id', UUID(as_uuid=True), nullable=False),
        sa.Column('step', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('message', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('idx_videos_user_id', 'videos', ['user_id'])
    op.create_index('idx_videos_status', 'videos', ['status'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_processing_logs_video_id', 'processing_logs', ['video_id'])
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_videos_user_id',
        'videos',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )

def downgrade():
    # Drop foreign key constraint first
    op.drop_constraint('fk_videos_user_id', 'videos', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('idx_processing_logs_video_id')
    op.drop_index('idx_users_email')
    op.drop_index('idx_videos_status')
    op.drop_index('idx_videos_user_id')
    
    # Drop tables
    op.drop_table('processing_logs')
    op.drop_table('videos')
    op.drop_table('users')