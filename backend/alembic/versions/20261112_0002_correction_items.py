"""correction ledger: correction_items table + dataset business key + run snapshot

Revision ID: 20261112_0002
Revises: 20261109_0001
Create Date: 2026-11-12

Adds the cross-run correction ledger (待修正清单):
* ``correction_items`` — one row per (dataset, rule, business key, occurrence);
* ``datasets.business_key_column`` — the column that identifies a business row;
* ``rule_runs.correction_json`` — per-run carry-over snapshot (created /
  still_open / reopened / fixed + reconciliation numbers).

Guards make the revision safe to run after the create_all-based 0001 on both
fresh and already-bootstrapped databases.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261112_0002"
down_revision = "20261109_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "correction_items" not in tables:
        from app.models import CorrectionItem  # noqa: F401

        CorrectionItem.__table__.create(bind, checkfirst=True)

    if "datasets" in tables:
        dataset_columns = {column["name"] for column in inspect(bind).get_columns("datasets")}
        if "business_key_column" not in dataset_columns:
            op.add_column("datasets", sa.Column("business_key_column", sa.String(length=190), nullable=True))

    if "rule_runs" in tables:
        run_columns = {column["name"] for column in inspect(bind).get_columns("rule_runs")}
        if "correction_json" not in run_columns:
            op.add_column("rule_runs", sa.Column("correction_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_table("correction_items")
    op.drop_column("datasets", "business_key_column")
    op.drop_column("rule_runs", "correction_json")
