import os
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("GITHUB_TOKEN", "ghp_test")


def test_celery_app_exists():
    from app.workers.celery_app import celery_app
    assert celery_app is not None
    assert celery_app.main == "project_verification"


def test_tier2_task_is_registered():
    from app.workers.celery_app import celery_app
    # Task names include the module path
    task_names = list(celery_app.tasks.keys())
    assert any("run_tier2_analysis" in name for name in task_names)
