"""Tests for storage utilities."""

import tempfile

from statequark import quark_with_storage
from statequark.utils.storage import FileStorage, MemoryStorage


class TestQuarkWithStorage:
    def test_memory_storage(self):
        storage = MemoryStorage()
        q = quark_with_storage("test", 10, storage)
        assert q.value == 10

        q.set_sync(20)
        assert q.value == 20
        assert storage.get("test", 0) == 20

    def test_file_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileStorage(tmpdir)
            q = quark_with_storage("sensor", 25.0, storage)
            q.set_sync(30.0)

            q2 = quark_with_storage("sensor", 0.0, storage)
            assert q2.value == 30.0

    def test_storage_with_dict(self):
        storage = MemoryStorage()
        q = quark_with_storage("config", {"threshold": 25}, storage)
        q.set_sync({"threshold": 30, "enabled": True})

        assert storage.get("config", {})["threshold"] == 30
