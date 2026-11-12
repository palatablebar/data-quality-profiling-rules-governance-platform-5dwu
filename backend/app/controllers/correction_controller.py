from sqlalchemy.orm import Session

from app.schemas.correction import serialize_correction_item
from app.services import correction_service, dataset_service, run_service


def list_corrections(db: Session, dataset_id: int, status: str | None, page: int, page_size: int) -> dict:
    dataset_service.get_dataset(db, dataset_id)
    result = correction_service.list_items(db, dataset_id, status=status, page=page, page_size=page_size)
    result["items"] = [serialize_correction_item(item) for item in result["items"]]
    return result


def correction_summary(db: Session, dataset_id: int) -> dict:
    dataset = dataset_service.get_dataset(db, dataset_id)
    return correction_service.reconciliation(db, dataset)


def run_corrections(db: Session, run_id: int) -> dict:
    run = run_service.get_run(db, run_id)
    payload = correction_service.run_effect(db, run)
    payload["items"] = [serialize_correction_item(item) for item in payload["items"]]
    return payload
