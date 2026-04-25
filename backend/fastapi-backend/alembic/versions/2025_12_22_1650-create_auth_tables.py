"""create_auth_tables

Revision ID: create_auth_tables_001
Revises: 
Create Date: 2025-12-22 16:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_auth_tables_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First, create users table (required by other tables)
    # Check if users table exists first
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'users' not in tables:
        # Create users table
        # Note: clinic_id FK will be added later if clinics table exists
        op.create_table(
            'users',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('email', sa.String(255), nullable=False),
            sa.Column('password', sa.String(255), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('phone', sa.String(20), nullable=True),
            sa.Column('role', sa.String(50), nullable=False, server_default='patient'),
            sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_login_ip', sa.String(45), nullable=True),
            sa.Column('reset_token', sa.String(255), nullable=True),
            sa.Column('reset_token_expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('verification_token', sa.String(255), nullable=True),
            sa.Column('avatar', sa.String(255), nullable=True),
            sa.Column('user_metadata', sa.Text(), nullable=True),
            sa.Column('remember_token', sa.String(100), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        )
        
        # Create indexes for users table
        op.create_index('ix_users_email', 'users', ['email'], unique=True)
        op.create_index('ix_users_role', 'users', ['role'])
        op.create_index('ix_users_clinic_id', 'users', ['clinic_id'])
        op.create_index('ix_users_is_active', 'users', ['is_active'])
        op.create_index('ix_users_reset_token', 'users', ['reset_token'], unique=True)
        op.create_index('ix_users_verification_token', 'users', ['verification_token'], unique=True)
        op.create_index('ix_users_remember_token', 'users', ['remember_token'])
        op.create_index('ix_users_created_at', 'users', ['created_at'])
        op.create_index('ix_users_deleted_at', 'users', ['deleted_at'])
        
        # Add clinic_id foreign key only if clinics table exists
        if 'clinics' in tables:
            op.create_foreign_key(
                'fk_users_clinic_id_clinics',
                'users', 'clinics',
                ['clinic_id'], ['id'],
                ondelete='CASCADE'
            )
    
    # Create roles table
    # Note: UUID defaults are handled by SQLAlchemy models (BaseModel), not at DB level
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('guard_name', sa.String(255), nullable=False, server_default='web'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for roles table
    op.create_index('roles_name_index', 'roles', ['name'], unique=True)
    op.create_index('roles_guard_name_index', 'roles', ['guard_name'])
    op.create_index('roles_created_at_index', 'roles', ['created_at'])
    op.create_index('roles_deleted_at_index', 'roles', ['deleted_at'])
    
    # Create user_roles pivot table
    op.create_table(
        'user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id'),
        sa.UniqueConstraint('user_id', 'role_id', name='user_roles_user_id_role_id_unique'),
    )
    
    # Create indexes for user_roles table
    op.create_index('user_roles_user_id_index', 'user_roles', ['user_id'])
    op.create_index('user_roles_role_id_index', 'user_roles', ['role_id'])
    
    # Add remember_token to users table if it doesn't exist (for existing installations)
    # Note: If users table was just created above, remember_token is already included
    if 'users' in tables:  # Only if users table existed before
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'remember_token' not in columns:
            op.add_column('users', sa.Column('remember_token', sa.String(100), nullable=True))
            op.create_index('users_remember_token_index', 'users', ['remember_token'])
    
    # Create password_resets table
    # Note: Using composite primary key (email, token) as SQLAlchemy requires a primary key
    # Laravel's password_resets table doesn't have a PK, but we need one for SQLAlchemy
    op.create_table(
        'password_resets',
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('email', 'token'),
    )
    
    # Create indexes for password_resets table
    op.create_index('password_resets_email_index', 'password_resets', ['email'])
    op.create_index('password_resets_token_index', 'password_resets', ['token'])
    
    # Create login_attempts table
    # Note: UUID defaults are handled by SQLAlchemy models (BaseModel), not at DB level
    op.create_table(
        'login_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for login_attempts table
    op.create_index('login_attempts_user_id_index', 'login_attempts', ['user_id'])
    op.create_index('login_attempts_email_index', 'login_attempts', ['email'])
    op.create_index('login_attempts_success_index', 'login_attempts', ['success'])
    op.create_index('login_attempts_created_at_index', 'login_attempts', ['created_at'])
    op.create_index('login_attempts_deleted_at_index', 'login_attempts', ['deleted_at'])
    
    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.String(255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('last_activity', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for user_sessions table
    op.create_index('user_sessions_user_id_index', 'user_sessions', ['user_id'])
    op.create_index('user_sessions_last_activity_index', 'user_sessions', ['last_activity'])


def downgrade() -> None:
    # Drop user_sessions table
    op.drop_index('user_sessions_last_activity_index', table_name='user_sessions')
    op.drop_index('user_sessions_user_id_index', table_name='user_sessions')
    op.drop_table('user_sessions')
    
    # Drop login_attempts table
    op.drop_index('login_attempts_deleted_at_index', table_name='login_attempts')
    op.drop_index('login_attempts_created_at_index', table_name='login_attempts')
    op.drop_index('login_attempts_success_index', table_name='login_attempts')
    op.drop_index('login_attempts_email_index', table_name='login_attempts')
    op.drop_index('login_attempts_user_id_index', table_name='login_attempts')
    op.drop_table('login_attempts')
    
    # Drop password_resets table
    op.drop_index('password_resets_token_index', table_name='password_resets')
    op.drop_index('password_resets_email_index', table_name='password_resets')
    op.drop_table('password_resets')
    
    # Remove remember_token from users table (only if it was added by this migration)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'users' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'remember_token' in columns:
            try:
                op.drop_index('users_remember_token_index', table_name='users')
            except:
                pass
            op.drop_column('users', 'remember_token')
    
    # Drop user_roles table
    op.drop_index('user_roles_role_id_index', table_name='user_roles')
    op.drop_index('user_roles_user_id_index', table_name='user_roles')
    op.drop_table('user_roles')
    
    # Drop roles table
    op.drop_index('roles_deleted_at_index', table_name='roles')
    op.drop_index('roles_created_at_index', table_name='roles')
    op.drop_index('roles_guard_name_index', table_name='roles')
    op.drop_index('roles_name_index', table_name='roles')
    op.drop_table('roles')
    
    # Note: We don't drop users table here as it may have been created separately
    # If you need to drop users table, do it in a separate migration

