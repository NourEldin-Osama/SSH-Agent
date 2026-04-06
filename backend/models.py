from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False)
    hostname = Column(String, nullable=False)
    port = Column(Integer, default=22)
    username = Column(String, nullable=False)
    auth_method = Column(String, nullable=False)
    encrypted_password = Column(Text, nullable=True)
    encrypted_ssh_key = Column(Text, nullable=True)
    encrypted_passphrase = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions = relationship("Session", back_populates="server")
    memories = relationship("ServerMemory", back_populates="server")
    permission_rules = relationship("PermissionRule", back_populates="server")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"))
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    server = relationship("Server", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session")
    commands = relationship("Command", back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="messages")


class Command(Base):
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    server_id = Column(Integer, ForeignKey("servers.id"))
    parent_id = Column(Integer, ForeignKey("commands.id"), nullable=True)
    group_id = Column(String, nullable=True)
    position_in_group = Column(Integer, nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    command = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=True)
    rollback_steps = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")
    actual_output = Column(Text, nullable=True)
    is_risky = Column(Boolean, default=False)
    edited_by_user = Column(Boolean, default=False)
    original_command = Column(Text, nullable=True)
    node_position_x = Column(Float, nullable=True)
    node_position_y = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)

    session = relationship("Session", back_populates="commands")
    children = relationship("Command", backref="parent", remote_side=[id])


class ServerMemory(Base):
    __tablename__ = "server_memories"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"))
    content = Column(Text, nullable=False)
    source = Column(String, nullable=False)
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    server = relationship("Server", back_populates="memories")


class PermissionRule(Base):
    __tablename__ = "permission_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_type = Column(String, nullable=False)
    match_type = Column(String, nullable=False)
    command_value = Column(String, nullable=False)
    scope = Column(String, nullable=False)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    server = relationship("Server", back_populates="permission_rules")


class SessionAllowedCommand(Base):
    __tablename__ = "session_allowed_commands"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    command_value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False, unique=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)
    encrypted_api_key = Column(Text, nullable=False)
    base_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
