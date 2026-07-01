import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User

logger = logging.getLogger(__name__)


def _connect_args(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args(settings.DATABASE_URL),
)


def create_db_and_tables():
    """Create tables for local development; production should run Alembic."""
    import app.models  # noqa: F401

    if settings.ENABLE_CREATE_ALL:
        SQLModel.metadata.create_all(engine)


def check_migrations_current() -> bool:
    """Best-effort startup check that Alembic metadata exists."""
    try:
        with engine.connect() as connection:
            if settings.DATABASE_URL.startswith("sqlite"):
                result = connection.execute(
                    text(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name='alembic_version'"
                    )
                )
                present = result.first() is not None
            else:
                result = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                )
                present = result.first() is not None
    except SQLAlchemyError as exc:
        logger.debug("migration_check_skipped: %s", exc)
        return False

    if not present:
        logger.info("alembic_version table not found; run alembic upgrade head")
    return present


def seed_default_governance_users() -> None:
    """Seed local governance accounts only when password env vars are supplied."""
    seed_specs = [
        (
            "INITIAL_ADMIN_EMAIL",
            "INITIAL_ADMIN_PASSWORD",
            "INITIAL_ADMIN_FULL_NAME",
            "admin",
        ),
        (
            "INITIAL_CLIENT_EMAIL",
            "INITIAL_CLIENT_PASSWORD",
            "INITIAL_CLIENT_FULL_NAME",
            "client",
        ),
        (
            "INITIAL_SECURITY_EMAIL",
            "INITIAL_SECURITY_PASSWORD",
            "INITIAL_SECURITY_FULL_NAME",
            "security_reviewer",
        ),
        (
            "INITIAL_APPROVER_EMAIL",
            "INITIAL_APPROVER_PASSWORD",
            "INITIAL_APPROVER_FULL_NAME",
            "security_approver",
        ),
    ]
    with Session(engine) as session:
        for email_key, password_key, name_key, role in seed_specs:
            password = getattr(settings, password_key, "")
            email = getattr(settings, email_key, "")
            if not password or not email:
                continue
            existing = session.query(User).filter(User.email == email).first()
            if existing:
                continue
            username = email.split("@", 1)[0]
            user = User(
                username=username,
                email=email,
                full_name=getattr(settings, name_key, "") or username,
                hashed_password=get_password_hash(password),
                role=role,
                is_active=True,
                is_superuser=role == "admin",
            )
            session.add(user)
        session.commit()


def get_session():
    with Session(engine) as session:
        yield session
