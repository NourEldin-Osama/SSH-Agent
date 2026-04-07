from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ServerBase(BaseModel):
    label: str
    hostname: str
    port: int = 22
    username: str
    auth_method: str
    password: Optional[str] = None
    ssh_key: Optional[str] = None
    passphrase: Optional[str] = None
    tags: Optional[List[str]] = None


class ServerCreate(ServerBase):
    pass


class ServerUpdate(BaseModel):
    label: Optional[str] = None
    hostname: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    auth_method: Optional[str] = None
    password: Optional[str] = None
    ssh_key: Optional[str] = None
    passphrase: Optional[str] = None
    tags: Optional[List[str]] = None


class ServerResponse(ServerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionBase(BaseModel):
    title: Optional[str] = None


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    title: Optional[str] = None


class SessionResponse(SessionBase):
    id: int
    server_id: int
    command_count: int = 0
    created_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatMessageBase(BaseModel):
    role: str
    content: str
    agent_name: Optional[str] = None
    model: Optional[str] = None


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageResponse(ChatMessageBase):
    id: int
    session_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CommandBase(BaseModel):
    title: str
    description: str
    command: str
    expected_output: Optional[str] = None
    rollback_steps: Optional[str] = None
    is_risky: bool = False
    group_id: Optional[str] = None
    position_in_group: Optional[int] = None
    parent_id: Optional[int] = None
    node_position_x: Optional[float] = None
    node_position_y: Optional[float] = None


class CommandCreate(CommandBase):
    session_id: int
    server_id: int


class CommandUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    command: Optional[str] = None
    expected_output: Optional[str] = None
    rollback_steps: Optional[str] = None


class CommandResponse(CommandBase):
    id: int
    session_id: int
    server_id: int
    status: str
    actual_output: Optional[str] = None
    edited_by_user: bool = False
    original_command: Optional[str] = None
    created_at: datetime
    executed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ServerMemoryBase(BaseModel):
    content: str
    source: str


class ServerMemoryCreate(ServerMemoryBase):
    server_id: int


class ServerMemoryUpdate(BaseModel):
    content: Optional[str] = None


class ServerMemoryResponse(ServerMemoryBase):
    id: int
    server_id: int
    approved: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PermissionRuleBase(BaseModel):
    rule_type: str
    match_type: str
    command_value: str
    scope: str
    server_id: Optional[int] = None


class PermissionRuleCreate(PermissionRuleBase):
    pass


class PermissionRuleUpdate(BaseModel):
    rule_type: Optional[str] = None
    match_type: Optional[str] = None
    command_value: Optional[str] = None
    scope: Optional[str] = None
    server_id: Optional[int] = None


class PermissionRuleResponse(PermissionRuleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AgentConfigBase(BaseModel):
    agent_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: bool = True


class AgentConfigCreate(AgentConfigBase):
    pass


class AgentConfigUpdate(BaseModel):
    agent_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: Optional[bool] = None


class AgentConfigResponse(BaseModel):
    id: int
    agent_name: str
    base_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    installed_local: Optional[bool] = None
    local_executable: Optional[str] = None

    class Config:
        from_attributes = True


class WebSocketEvent(BaseModel):
    event: str
    data: dict


class SessionAllowedCommandResponse(BaseModel):
    id: int
    session_id: int
    command_value: str
    created_at: datetime

    class Config:
        from_attributes = True


class AppSettingBase(BaseModel):
    key: str
    value: str


class AppSettingResponse(AppSettingBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class DangerModeUpdate(BaseModel):
    enabled: bool


class DebugModeUpdate(BaseModel):
    enabled: bool
