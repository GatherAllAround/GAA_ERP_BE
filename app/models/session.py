from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    user_sessions = relationship("UserSession", back_populates="session")


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (UniqueConstraint("user_id", "session_id"),)

    user_session_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sessions.session_id"), nullable=False)
    is_main: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    skill_level: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, server_default="0.00")
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    user = relationship("User", back_populates="user_sessions")
    session = relationship("Session", back_populates="user_sessions")
