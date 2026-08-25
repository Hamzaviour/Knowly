import os
import pytest
from sqlalchemy import create_engine, delete

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

import app.models  # noqa — register all models into Base.metadata
from app.database import Base


test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    import app.database
    app.database.engine = test_engine
    app.database.SessionLocal.configure(bind=test_engine)
    yield


@pytest.fixture
def db():
    from app.database import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_workspace_id():
    return "test-ws-clear"


@pytest.fixture(autouse=True)
def clean_db(db):
    from app.models.document import Document
    from app.models.chat import ChatMessage
    from app.models.analytics import UsageMetric
    from app.models.workflow import Workflow, WorkflowRun

    for model in (WorkflowRun, Workflow, ChatMessage, UsageMetric, Document):
        db.execute(delete(model.__table__))
        db.commit()
    yield
