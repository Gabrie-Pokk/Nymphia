"""initial_schema_postgresql_sqlite

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-14 14:22:00

Gera o schema inicial completo em PostgreSQL e SQLite, cobrindo todos os
modelos clínicos, obstétricos, governança CFM 2.454/2026, LGPD e assinaturas.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

from app.database import Base
import app.models  # Garante registro de todas as tabelas no Base.metadata

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria todas as tabelas e índices no banco de destino (PostgreSQL / SQLite)."""
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """Remove as tabelas criadas."""
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
