import shutil
import subprocess
import json
import re
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from loguru import logger

from database import get_db
from models import AgentConfig
from schemas import AgentConfigCreate, AgentConfigUpdate, AgentConfigResponse
from encryption import encrypt_value

router = APIRouter(prefix="/api/agents", tags=["agents"])


LOCAL_AGENT_EXECUTABLES = {
    "claude-code": ["claude"],
    "opencode": ["opencode"],
    "codex": ["codex"],
}


def _resolve_local_binary(agent_name: str):
    candidates = LOCAL_AGENT_EXECUTABLES.get(agent_name, [agent_name])
    for cmd in candidates:
        path = shutil.which(cmd)
        if path:
            return True, path
    return False, None


def _extract_models_from_text(text: str) -> list[str]:
    if not text:
        return []
    patterns = [
        r"claude-[a-z0-9.-]+",
        r"gpt-[a-z0-9.-]+",
        r"o[0-9](?:-[a-z0-9.-]+)?",
    ]
    found: list[str] = []
    for pattern in patterns:
        found.extend(re.findall(pattern, text.lower()))
    deduped = []
    seen = set()
    for item in found:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def _run_model_discovery(executable: str, args: list[str]) -> list[str]:
    try:
        completed = subprocess.run(
            [executable] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=12,
            check=False,
        )
    except Exception as exc:
        logger.debug("Model discovery failed cmd={} error={}", [executable] + args, exc)
        return []

    text_out = (completed.stdout or "") + "\n" + (completed.stderr or "")
    text_out = text_out.strip()
    if not text_out:
        return []

    try:
        parsed = json.loads(completed.stdout)
        models = []
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, str):
                    models.append(item)
                elif isinstance(item, dict):
                    model_id = item.get("id") or item.get("name") or item.get("model")
                    if isinstance(model_id, str):
                        models.append(model_id)
        elif isinstance(parsed, dict):
            values = parsed.get("models") or parsed.get("data") or []
            if isinstance(values, list):
                for item in values:
                    if isinstance(item, str):
                        models.append(item)
                    elif isinstance(item, dict):
                        model_id = (
                            item.get("id") or item.get("name") or item.get("model")
                        )
                        if isinstance(model_id, str):
                            models.append(model_id)
        if models:
            return list(dict.fromkeys(models))
    except Exception:
        pass

    return _extract_models_from_text(text_out)


def _discover_local_models(agent_name: str) -> list[str]:
    installed, executable = _resolve_local_binary(agent_name)
    if not installed or not executable:
        return []

    probe_commands: list[list[str]] = []
    if agent_name == "claude-code":
        probe_commands = [
            ["models", "--json"],
            ["model", "list", "--json"],
            ["--help"],
        ]
    elif agent_name == "opencode":
        probe_commands = [
            ["models", "--json"],
            ["model", "list", "--json"],
            ["--help"],
        ]

    discovered: list[str] = []
    for args in probe_commands:
        models = _run_model_discovery(executable, args)
        if models:
            discovered.extend(models)

    deduped = []
    seen = set()
    for m in discovered:
        if m not in seen:
            deduped.append(m)
            seen.add(m)
    return deduped


def _discover_claude_current_model() -> str | None:
    installed, executable = _resolve_local_binary("claude-code")
    if not installed or not executable:
        return None

    try:
        completed = subprocess.run(
            [executable, "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=8,
            check=False,
        )
    except Exception as exc:
        logger.debug("Claude model discovery failed: {}", exc)
        return None

    combined = (completed.stdout or "") + "\n" + (completed.stderr or "")
    candidates = _extract_models_from_text(combined)
    if candidates:
        return candidates[0]
    return None


def _build_acp_config_options(agent_name: str) -> list[dict]:
    model_map = {
        "claude-code": [
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-haiku-4-20250514",
        ],
        "opencode": ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4-20250514"],
        "codex": ["o3", "o4-mini", "gpt-4.1"],
    }

    models = _discover_local_models(agent_name)
    if not models:
        models = model_map.get(agent_name, ["default-model"])

    current = os.getenv("ACP_MODEL_NAME", "") or (models[0] if models else "")
    if current and current not in models:
        models = [current] + models

    return [
        {
            "id": "model",
            "name": "Model",
            "category": "model",
            "type": "select",
            "currentValue": current,
            "options": [
                {
                    "value": m,
                    "name": m,
                    "description": "Available model option",
                }
                for m in models
            ],
        }
    ]


async def _resolve_config_options(
    request: Request,
    agent_name: str,
) -> list[dict]:
    runtime = getattr(request.app.state, "acp_runtime", None)
    if runtime is not None:
        try:
            options = await runtime.fetch_agent_config_options(agent_name)
            if options:
                logger.info(
                    "Agent config options resolved via ACP session negotiation agent_name={} count={}",
                    agent_name,
                    len(options),
                )
                return options
        except Exception as exc:
            logger.warning(
                "ACP config option negotiation failed for agent={} error={}",
                agent_name,
                exc,
            )
    options = _build_acp_config_options(agent_name)
    logger.info(
        "Agent config options resolved via local fallback agent_name={} count={}",
        agent_name,
        len(options),
    )
    return options


@router.get("/", response_model=List[AgentConfigResponse])
def list_agents(db: Session = Depends(get_db)):
    agents = db.query(AgentConfig).all()
    return [
        AgentConfigResponse(
            id=a.id,
            agent_name=a.agent_name,
            base_url=a.base_url,
            is_active=a.is_active,
            created_at=a.created_at,
            installed_local=_resolve_local_binary(a.agent_name)[0],
            local_executable=_resolve_local_binary(a.agent_name)[1],
        )
        for a in agents
    ]


@router.post("/", response_model=AgentConfigResponse)
def create_agent(agent: AgentConfigCreate, db: Session = Depends(get_db)):
    is_local = _resolve_local_binary(agent.agent_name)[0]
    if not is_local and not agent.api_key:
        raise HTTPException(
            status_code=400,
            detail="API key is required for non-local agent configurations",
        )

    encrypted_key = None
    if agent.api_key:
        encrypted_key = encrypt_value(agent.api_key)
    elif is_local:
        encrypted_key = encrypt_value("local-agent-no-key")
    else:
        raise HTTPException(
            status_code=400,
            detail="API key is required for non-local agent configurations",
        )

    db_agent = AgentConfig(
        agent_name=agent.agent_name,
        encrypted_api_key=encrypted_key,
        base_url=agent.base_url,
        is_active=agent.is_active,
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return AgentConfigResponse(
        id=db_agent.id,
        agent_name=db_agent.agent_name,
        base_url=db_agent.base_url,
        is_active=db_agent.is_active,
        created_at=db_agent.created_at,
        installed_local=_resolve_local_binary(db_agent.agent_name)[0],
        local_executable=_resolve_local_binary(db_agent.agent_name)[1],
    )


@router.put("/{agent_id}", response_model=AgentConfigResponse)
def update_agent(
    agent_id: int, agent_update: AgentConfigUpdate, db: Session = Depends(get_db)
):
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    update_data = agent_update.model_dump(exclude_unset=True)
    if "api_key" in update_data and update_data["api_key"] is not None:
        agent.encrypted_api_key = encrypt_value(update_data.pop("api_key"))
    if "base_url" in update_data and update_data["base_url"] is not None:
        if agent.agent_name in {"claude-code", "opencode"}:
            update_data["base_url"] = None
    for field, value in update_data.items():
        setattr(agent, field, value)
    db.commit()
    db.refresh(agent)
    return AgentConfigResponse(
        id=agent.id,
        agent_name=agent.agent_name,
        base_url=agent.base_url,
        is_active=agent.is_active,
        created_at=agent.created_at,
        installed_local=_resolve_local_binary(agent.agent_name)[0],
        local_executable=_resolve_local_binary(agent.agent_name)[1],
    )


@router.delete("/{agent_id}")
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db.delete(agent)
    db.commit()
    return {"message": "Agent deleted"}


@router.get("/{agent_name}/models")
async def get_agent_models(
    agent_name: str,
    request: Request,
    db: Session = Depends(get_db),
):
    agent = db.query(AgentConfig).filter(AgentConfig.agent_name == agent_name).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    config_options = await _resolve_config_options(request, agent_name)
    model_option = next(
        (o for o in config_options if o.get("category") == "model"), None
    )
    models = [
        o.get("value")
        for o in (model_option or {}).get("options", [])
        if o.get("value")
    ]
    current_model = (model_option or {}).get("currentValue")
    logger.info(
        "Agent models resolved via ACP config options agent_name={} count={} current_model={}",
        agent_name,
        len(models),
        current_model,
    )
    return {
        "models": models,
        "current_model": current_model,
        "source": "acp_config_options",
    }


@router.get("/local/installed")
def list_local_installed_agents():
    items = []
    for name in ["claude-code", "opencode", "codex"]:
        installed, path = _resolve_local_binary(name)
        items.append({"agent_name": name, "installed": installed, "executable": path})
    return {"agents": items}


@router.get("/local/current-model")
def get_local_current_model(agent_name: str = "claude-code"):
    config_options = _build_acp_config_options(agent_name)
    model_option = next(
        (o for o in config_options if o.get("category") == "model"), None
    )
    current_model = (model_option or {}).get("currentValue")
    return {
        "agent_name": agent_name,
        "current_model": current_model,
        "source": "acp_config_options",
    }


@router.get("/{agent_name}/acp-config-options")
async def get_agent_acp_config_options(
    agent_name: str,
    request: Request,
    db: Session = Depends(get_db),
):
    agent = db.query(AgentConfig).filter(AgentConfig.agent_name == agent_name).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"configOptions": await _resolve_config_options(request, agent_name)}
