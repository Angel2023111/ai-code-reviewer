from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(bind=engine)


def setup_database():
    Base.metadata.create_all(bind=engine)


def teardown_database():
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


def test_create_review_job():
    setup_database()
    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.api.routes.reviews.run_review_job.delay"
        ) as mock_delay:

            response = client.post(
                "/reviews/jobs",
                json={
                    "code": "x = 10\nprint(x)",
                    "language": "python",
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["job_id"]
        assert data["status"] == "PENDING"
        assert data["review_id"] is None
        assert data["error_message"] is None

        mock_delay.assert_called_once()

        args = mock_delay.call_args.args

        assert args[0] == data["job_id"]
        assert args[1] == "x = 10\nprint(x)"
        assert args[2] == "python"

    finally:
        teardown_database()
        app.dependency_overrides.clear()


def test_get_review_job():
    setup_database()
    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/reviews/jobs",
            json={
                "code": "x = 10",
                "language": "python",
            },
        )

        assert response.status_code == 200

        job_id = response.json()["job_id"]

        response = client.get(
            f"/reviews/jobs/{job_id}"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["job_id"] == job_id
        assert data["status"] == "PENDING"
        assert data["review_id"] is None
        assert data["error_message"] is None

    finally:
        teardown_database()
        app.dependency_overrides.clear()


def test_get_review_job_not_found():
    setup_database()
    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get(
            "/reviews/jobs/non-existent-job"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Review job not found"
        )

    finally:
        teardown_database()
        app.dependency_overrides.clear()