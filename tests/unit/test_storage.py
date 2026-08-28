from __future__ import annotations

import io

from threed_od.storage import LocalFilesystemStorage


def test_local_storage_put_and_exists(tmp_path) -> None:
    storage = LocalFilesystemStorage(str(tmp_path))
    assert not storage.exists("foo/bar.bin")

    storage.put("foo/bar.bin", io.BytesIO(b"hello world"))
    assert storage.exists("foo/bar.bin")

    path = storage.get_path_or_url("foo/bar.bin")
    with open(path, "rb") as fh:
        assert fh.read() == b"hello world"
