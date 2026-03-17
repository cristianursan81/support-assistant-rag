from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import relationship
from src.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    mission = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    agents = relationship("Agent", back_populates="company", foreign_keys="Agent.company_id")
    goals = relationship("Goal", back_populates="company")
    tickets = relationship("Ticket", back_populates="company")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    role_description = Column(Text)
    boss_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    system_prompt = Column(Text)
    heartbeat_interval = Column(Integer, default=3600)  # seconds
    monthly_budget_usd = Column(Float, default=10.0)
    spent_this_month_usd = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_heartbeat = Column(DateTime, nullable=True)

    company = relationship("Company", back_populates="agents", foreign_keys=[company_id])
    boss = relationship("Agent", remote_side="Agent.id", foreign_keys=[boss_id], back_populates="subordinates")
    subordinates = relationship("Agent", foreign_keys=[boss_id], back_populates="boss")
    tickets = relationship("Ticket", back_populates="assigned_agent")
    token_usages = relationship("TokenUsage", back_populates="agent")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    level = Column(String, default="task")  # company | project | task
    status = Column(String, default="active")  # active | completed | paused
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="goals")
    parent = relationship("Goal", remote_side="Goal.id", foreign_keys=[parent_id], back_populates="children")
    children = relationship("Goal", foreign_keys=[parent_id], back_populates="parent")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="open")  # open | in_progress | completed | blocked
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="tickets")
    assigned_agent = relationship("Agent", back_populates="tickets")
    messages = relationship(
        "TicketMessage", back_populates="ticket",
        order_by="TicketMessage.created_at"
    )
    token_usages = relationship("TokenUsage", back_populates="ticket")


class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    role = Column(String, nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="messages")


class TokenUsage(Base):
    __tablename__ = "token_usages"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="token_usages")
    ticket = relationship("Ticket", back_populates="token_usages")


class AgentEvent(Base):
    """Audit log of every action an agent takes."""
    __tablename__ = "agent_events"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    event_type = Column(String, nullable=False)
    # e.g. heartbeat_start | tool_call | delegation | goal_created
    # | status_change | escalation | budget_exceeded | error
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent")
    ticket = relationship("Ticket")


# ---------------------------------------------------------------------------
# Multi-tenant / SaaS models
# ---------------------------------------------------------------------------

class Workspace(Base):
    """One workspace = one SME customer."""
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    name = Column(String, nullable=False)
    industry = Column(String, default="custom")
    # restaurante | clinica | tienda | custom

    # Contact / channel config
    whatsapp_number = Column(String, nullable=True, index=True)   # E.164 e.g. +34612345678
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)

    # Business info fed to agents via get_business_info()
    business_info = Column(JSON, nullable=True)
    # { "nombre": "...", "horarios": "...", "servicios": [...],
    #   "precios": "...", "direccion": "...", "faqs": [...] }

    # Subscription
    plan = Column(String, default="trial")
    # trial | basico | profesional | empresa
    trial_ends_at = Column(DateTime, nullable=True)
    monthly_message_limit = Column(Integer, default=100)
    messages_used_this_month = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company")
    users = relationship("User", back_populates="workspace")
    conversations = relationship("Conversation", back_populates="workspace")


class User(Base):
    """Dashboard login for an SME operator."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="users")


class Conversation(Base):
    """One ongoing customer conversation on any channel."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    channel = Column(String, nullable=False)
    # whatsapp | email | web
    customer_identifier = Column(String, nullable=False)
    # phone number (whatsapp) or email address
    customer_name = Column(String, nullable=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    status = Column(String, default="active")
    # active | resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="conversations")
    ticket = relationship("Ticket")

    __table_args__ = (
        # Fast lookup for inbound message deduplication
        Index("ix_conv_ws_channel_ident_status",
              "workspace_id", "channel", "customer_identifier", "status"),
    )


class Booking(Base):
    """Appointment/reservation created by an agent."""
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    customer_name = Column(String, nullable=False)
    customer_contact = Column(String, nullable=True)
    service = Column(String, nullable=True)
    booking_date = Column(String, nullable=False)   # ISO date string
    booking_time = Column(String, nullable=False)   # HH:MM
    status = Column(String, default="confirmed")
    # confirmed | cancelled | completed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_booking_ws_date_time", "workspace_id", "booking_date", "booking_time"),
    )
