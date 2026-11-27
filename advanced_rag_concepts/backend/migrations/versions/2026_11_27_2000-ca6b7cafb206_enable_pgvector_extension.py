"""enable pgvector extension

Revision ID: ca6b7cafb206
Revises:
Create Date: 2026-11-27 20:00:16.982619

"""

from collections.abc import Sequence

from alembic import op

# Revision identifiers, used by Alembic to order migrations.
revision: str = "ca6b7cafb206"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector in this database (it is installed in the image, but off by default)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    # Undo: remove the extension (only works once no tables use the vector type)
    op.execute("DROP EXTENSION IF EXISTS vector")
