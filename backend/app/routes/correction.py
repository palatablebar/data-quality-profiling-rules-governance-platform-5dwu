from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import correction_controller
from app.middlewares.auth import get_current_user
from app.models import User

router = APIRouter(tags=["corrections"])


@router.get("/datasets/{dataset_id}/corrections")
def list_corrections(
    dataset_id: int,
    status: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return correction_controller.list_corrections(db, dataset_id, status, page, page_size)


@router.get("/datasets/{dataset_id}/corrections/summary")
def correction_summary(dataset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return correction_controller.correction_summary(db, dataset_id)


@router.get("/runs/{run_id}/corrections")
def run_corrections(run_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return correction_controller.run_corrections(db, run_id)
