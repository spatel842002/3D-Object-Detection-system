from __future__ import annotations

import pytest
from pydantic import ValidationError

from threed_od.config import Settings


def test_defaults_load_without_any_env_vars() -> None:
    settings = Settings(_env_file=None)
    assert settings.storage_backend == "local"
    assert 0.0 < settings.yolo_confidence_threshold <= 1.0


def test_invalid_storage_backend_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, STORAGE_BACKEND="ftp")


def test_confidence_threshold_out_of_range_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, YOLO_CONFIDENCE_THRESHOLD=1.5)


def test_negative_upload_limit_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, MAX_UPLOAD_SIZE_MB=-1)


def test_cors_origins_list_splits_and_trims() -> None:
    settings = Settings(_env_file=None, API_CORS_ORIGINS="http://a.com, http://b.com")
    assert settings.cors_origins_list() == ["http://a.com", "http://b.com"]
