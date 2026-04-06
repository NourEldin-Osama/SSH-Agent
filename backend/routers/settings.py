from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import AppSetting
from schemas import DangerModeUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/danger-mode")
def get_danger_mode(session_id: int | None = None, db: Session = Depends(get_db)):
    key = (
        f"danger_mode_session_{session_id}" if session_id is not None else "danger_mode"
    )
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    enabled = bool(
        setting and setting.value.strip().lower() in {"1", "true", "yes", "on"}
    )
    return {"enabled": enabled, "session_id": session_id}


@router.put("/danger-mode")
def set_danger_mode(
    payload: DangerModeUpdate,
    session_id: int | None = None,
    db: Session = Depends(get_db),
):
    key = (
        f"danger_mode_session_{session_id}" if session_id is not None else "danger_mode"
    )
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if not setting:
        setting = AppSetting(key=key, value="false")
        db.add(setting)

    setting.value = "true" if payload.enabled else "false"
    db.commit()
    db.refresh(setting)
    return {"enabled": payload.enabled, "session_id": session_id}
