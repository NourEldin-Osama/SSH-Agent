from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import fnmatch

from database import get_db
from models import PermissionRule, Server, AppSetting, SessionAllowedCommand
from schemas import PermissionRuleCreate, PermissionRuleUpdate, PermissionRuleResponse

router = APIRouter(prefix="/api/permissions", tags=["permissions"])


@router.get("/", response_model=List[PermissionRuleResponse])
def list_rules(db: Session = Depends(get_db)):
    rules = db.query(PermissionRule).all()
    return [
        PermissionRuleResponse(
            id=r.id,
            rule_type=r.rule_type,
            match_type=r.match_type,
            command_value=r.command_value,
            scope=r.scope,
            server_id=r.server_id,
            created_at=r.created_at,
        )
        for r in rules
    ]


@router.post("/", response_model=PermissionRuleResponse)
def create_rule(rule: PermissionRuleCreate, db: Session = Depends(get_db)):
    if rule.scope == "server" and rule.server_id is None:
        raise HTTPException(
            status_code=400, detail="server_id is required for server scope"
        )
    if rule.scope == "server" and rule.server_id is not None:
        server = db.query(Server).filter(Server.id == rule.server_id).first()
        if not server:
            raise HTTPException(
                status_code=404, detail="Server not found for rule scope"
            )
    db_rule = PermissionRule(
        rule_type=rule.rule_type,
        match_type=rule.match_type,
        command_value=rule.command_value,
        scope=rule.scope,
        server_id=rule.server_id,
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return PermissionRuleResponse(
        id=db_rule.id,
        rule_type=db_rule.rule_type,
        match_type=db_rule.match_type,
        command_value=db_rule.command_value,
        scope=db_rule.scope,
        server_id=db_rule.server_id,
        created_at=db_rule.created_at,
    )


@router.put("/{rule_id}", response_model=PermissionRuleResponse)
def update_rule(
    rule_id: int, rule_update: PermissionRuleUpdate, db: Session = Depends(get_db)
):
    rule = db.query(PermissionRule).filter(PermissionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    update_data = rule_update.model_dump(exclude_unset=True)
    new_scope = update_data.get("scope", rule.scope)
    new_server_id = update_data.get("server_id", rule.server_id)
    if new_scope == "server" and new_server_id is None:
        raise HTTPException(
            status_code=400, detail="server_id is required for server scope"
        )
    for field, value in update_data.items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return PermissionRuleResponse(
        id=rule.id,
        rule_type=rule.rule_type,
        match_type=rule.match_type,
        command_value=rule.command_value,
        scope=rule.scope,
        server_id=rule.server_id,
        created_at=rule.created_at,
    )


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(PermissionRule).filter(PermissionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"message": "Rule deleted"}


def _session_match(command: str, allowed: SessionAllowedCommand) -> bool:
    value = allowed.command_value
    if not value:
        return False
    if "*" in value or "?" in value or "[" in value:
        return fnmatch.fnmatch(command, value)
    return command == value


def _rule_priority(rule: PermissionRule) -> int:
    return 0 if rule.scope == "global" else 1


def _is_true_setting(value: str | None) -> bool:
    if not value:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def check_command_against_rules(
    command: str,
    server_id: int,
    db: Session,
    session_id: int | None = None,
):
    blacklists = (
        db.query(PermissionRule)
        .filter(PermissionRule.rule_type == "blacklist")
        .order_by(PermissionRule.created_at)
        .all()
    )
    for rule in sorted(blacklists, key=_rule_priority):
        if rule.scope == "global" and _matches(command, rule):
            return "blocked", f"Blocked by global {rule.match_type} blacklist rule"
        if (
            rule.scope == "server"
            and rule.server_id == server_id
            and _matches(command, rule)
        ):
            return "blocked", f"Blocked by server {rule.match_type} blacklist rule"

    whitelists = (
        db.query(PermissionRule)
        .filter(PermissionRule.rule_type == "whitelist")
        .order_by(PermissionRule.created_at)
        .all()
    )
    for rule in sorted(whitelists, key=_rule_priority):
        if rule.scope == "global" and _matches(command, rule):
            return "approved", "Auto-approved by global whitelist rule"
        if (
            rule.scope == "server"
            and rule.server_id == server_id
            and _matches(command, rule)
        ):
            return "approved", "Auto-approved by server whitelist rule"

    if session_id is not None:
        session_allowed_list = (
            db.query(SessionAllowedCommand)
            .filter(SessionAllowedCommand.session_id == session_id)
            .all()
        )
        for allowed in session_allowed_list:
            if _session_match(command, allowed):
                return "approved", "Auto-approved by session allow rule"

    danger = None
    if session_id is not None:
        danger = (
            db.query(AppSetting)
            .filter(AppSetting.key == f"danger_mode_session_{session_id}")
            .first()
        )
    if danger is None:
        danger = db.query(AppSetting).filter(AppSetting.key == "danger_mode").first()
    if danger and _is_true_setting(danger.value):
        return "approved", "Auto-approved because danger mode is enabled"

    return "pending", "Awaiting human approval"


def _matches(command: str, rule: PermissionRule) -> bool:
    if rule.match_type == "exact":
        return command == rule.command_value
    elif rule.match_type == "pattern":
        return fnmatch.fnmatch(command, rule.command_value)
    return False


@router.get("/check")
def check_command(
    command: str = Query(...),
    server_id: int = Query(...),
    session_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    result, reason = check_command_against_rules(
        command,
        server_id,
        db,
        session_id=session_id,
    )
    return {"command": command, "result": result, "reason": reason}
