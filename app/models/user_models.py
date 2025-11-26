from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    String,
    BigInteger,
    SmallInteger,
    Numeric,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


"""Справочник статусов пользователя"""
class DUserStatus(Base):
    __tablename__ = "d_user_status"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[int] = mapped_column(Numeric(1), default=1)

    users: Mapped[List["User"]] = relationship(
        back_populates="status",
        lazy="selectin",
    )


"""Справочник ролей пользователя"""
class DUserRole(Base):
    __tablename__ = "d_user_role"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[int] = mapped_column(Numeric(1), default=1)

    users: Mapped[List["User"]] = relationship(
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin",
    )

    user_links: Mapped[List["UserRole"]] = relationship(
        back_populates="role",
        lazy="selectin",
    )


"""Основная модель пользователя, содержащая персональные данные и настройки"""
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(50))
    password_hash: Mapped[Optional[str]] = mapped_column(String(300))
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    status_id: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        ForeignKey("d_user_status.id"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    status: Mapped[Optional[DUserStatus]] = relationship(
        back_populates="users",
        lazy="joined",
    )

    # Many-to-Many через user_roles
    roles: Mapped[List[DUserRole]] = relationship(
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",
    )

    # Ассоциативная таблица
    role_links: Mapped[List["UserRole"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    tokens: Mapped[List["UserToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


"""Связующая таблица между пользователями и ролями"""
class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("d_user_role.id"),
        primary_key=True,
    )

    user: Mapped[User] = relationship(
        back_populates="role_links",
    )
    role: Mapped[DUserRole] = relationship(
        back_populates="user_links",
    )


"""Токены авторизации пользователя"""
class UserToken(Base):
    __tablename__ = "user_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    jwt: Mapped[str] = mapped_column(String(500), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(512), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped[User] = relationship(
        back_populates="tokens",
        lazy="joined",
    )
