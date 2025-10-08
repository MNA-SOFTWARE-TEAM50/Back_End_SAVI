"""
Modelo de bitácora de auditoría
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.sql import func
from db.session import Base
import uuid


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    action = Column(String(50), nullable=False)  # e.g., create_user
    actor_user_id = Column(CHAR(36), nullable=False)
    target_user_id = Column(CHAR(36), nullable=True)
    role_assigned = Column(String(20), nullable=True)
    result = Column(String(20), nullable=False)  # success / failure
    detail = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
