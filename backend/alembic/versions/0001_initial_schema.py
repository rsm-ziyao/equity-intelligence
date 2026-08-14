"""Create the current stocks and stock_prices schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stocks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stocks_id", "stocks", ["id"], unique=False)
    op.create_index("ix_stocks_symbol", "stocks", ["symbol"], unique=True)

    op.create_table(
        "stock_prices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_timestamp", sa.String(length=50), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "stock_id",
            "provider",
            "provider_timestamp",
            name="uq_stock_provider_timestamp",
        ),
    )
    op.create_index("ix_stock_prices_id", "stock_prices", ["id"], unique=False)
    op.create_index("ix_stock_prices_stock_id", "stock_prices", ["stock_id"], unique=False)
    op.create_index("ix_stock_prices_timestamp", "stock_prices", ["timestamp"], unique=False)
    op.create_index("idx_stock_timestamp", "stock_prices", ["stock_id", "timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_stock_timestamp", table_name="stock_prices")
    op.drop_index("ix_stock_prices_timestamp", table_name="stock_prices")
    op.drop_index("ix_stock_prices_stock_id", table_name="stock_prices")
    op.drop_index("ix_stock_prices_id", table_name="stock_prices")
    op.drop_table("stock_prices")
    op.drop_index("ix_stocks_symbol", table_name="stocks")
    op.drop_index("ix_stocks_id", table_name="stocks")
    op.drop_table("stocks")
