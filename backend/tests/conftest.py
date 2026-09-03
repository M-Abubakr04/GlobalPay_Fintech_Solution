import os
from pathlib import Path

TEST_DB = Path("/tmp/globalpay_test.db")
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["REDIS_URL"] = "redis://localhost:6399/15"
os.environ["JWT_SECRET"] = "test-secret-that-is-more-than-32-bytes-long"
os.environ["PII_ENCRYPTION_KEY"] = "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="
os.environ["FRAUD_DATASET_PATH"] = str(Path(__file__).resolve().parents[2] / "datasets" / "transactions.csv")
os.environ["FRAUD_MODEL_PATH"] = "/tmp/globalpay_test_model.joblib"

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)
