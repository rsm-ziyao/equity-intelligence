"""Add normalized company fundamentals tables."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_financial_fundamentals"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("financial_periods",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False), sa.Column("fiscal_period_type", sa.String(20), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False), sa.Column("fiscal_quarter", sa.Integer()),
        sa.Column("period_start", sa.DateTime()), sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("filing_date", sa.DateTime()), sa.Column("provider_period_key", sa.String(100)),
        sa.Column("provider_effective_at", sa.DateTime()), sa.Column("retrieved_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime()),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("stock_id", "provider", "fiscal_period_type", "period_end", name="uq_financial_period_key"))
    op.create_index("ix_financial_periods_id", "financial_periods", ["id"])
    op.create_index("ix_financial_periods_stock_id", "financial_periods", ["stock_id"])
    op.create_index("ix_financial_periods_period_end", "financial_periods", ["period_end"])
    op.create_index("idx_financial_period_stock_type_end", "financial_periods", ["stock_id", "fiscal_period_type", "period_end"])
    numeric = sa.Numeric(24, 6)
    for table, fields in {
        "income_statement_periods": [("revenue", numeric), ("gross_profit", numeric), ("operating_income", numeric), ("net_income", numeric), ("diluted_eps", numeric)],
        "cash_flow_periods": [("operating_cash_flow", numeric), ("capital_expenditures", numeric)],
        "balance_sheet_periods": [("cash_and_cash_equivalents", numeric), ("total_debt", numeric)],
    }.items():
        cols = [sa.Column("period_id", sa.Integer(), primary_key=True, nullable=False)] + [sa.Column(n, t) for n, t in fields] + [sa.Column("currency", sa.String(20)), sa.Column("unit", sa.String(50))]
        op.create_table(table, *cols, sa.ForeignKeyConstraint(["period_id"], ["financial_periods.id"], ondelete="CASCADE"))
        op.create_index(f"ix_{table}_period_id", table, ["period_id"])

def downgrade() -> None:
    for table in ("balance_sheet_periods", "cash_flow_periods", "income_statement_periods"):
        op.drop_index(f"ix_{table}_period_id", table_name=table); op.drop_table(table)
    op.drop_index("idx_financial_period_stock_type_end", table_name="financial_periods")
    op.drop_index("ix_financial_periods_period_end", table_name="financial_periods")
    op.drop_index("ix_financial_periods_stock_id", table_name="financial_periods")
    op.drop_index("ix_financial_periods_id", table_name="financial_periods")
    op.drop_table("financial_periods")
