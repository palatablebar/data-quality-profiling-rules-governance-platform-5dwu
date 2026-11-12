from pydantic import BaseModel, Field

from app.constants.correction_status import CORRECTION_STATUS_LABELS
from app.schemas.common import iso
from app.utils.formatters import severity_label


class DatasetKeyUpdate(BaseModel):
    business_key_column: str | None = Field(default=None, max_length=190)


def serialize_correction_item(item) -> dict:
    return {
        "id": item.id,
        "dataset_id": item.dataset_id,
        "rule_id": item.rule_id,
        "rule_name": item.rule_name,
        "column_name": item.column_name,
        "severity": item.severity,
        "severity_label": severity_label(item.severity),
        "business_key": item.business_key,
        "key_occurrence": item.key_occurrence,
        "row_index": item.row_index,
        "first_row_index": item.first_row_index,
        "observed_value": item.observed_value,
        "expected_expr": item.expected_expr,
        "status": item.status,
        "status_label": CORRECTION_STATUS_LABELS.get(item.status, item.status),
        "first_seen_run_id": item.first_seen_run_id,
        "last_seen_run_id": item.last_seen_run_id,
        "fixed_run_id": item.fixed_run_id,
        "fixed_at": iso(item.fixed_at),
        "created_at": iso(item.created_at),
        "updated_at": iso(item.updated_at),
    }
