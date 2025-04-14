import pytest
import datetime
from core.logging_config import setup_logging
from pathlib import Path

@pytest.fixture(scope="session", autouse=True)
def init_logging():
    """Set up colorized, structured logging once for all tests."""
    log_dir = Path("logs/test_runs")
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = log_dir / f"test_run_{timestamp}.log"

    setup_logging(log_file=log_file)