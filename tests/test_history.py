"""Tests for history utilities."""

from statequark import history


class TestHistory:
    def test_undo_redo(self):
        q = history(0)
        q.set(1)
        q.set(2)
        q.set(3)

        assert q.value == 3
        assert q.undo()
        assert q.value == 2
        assert q.undo()
        assert q.value == 1
        assert q.redo()
        assert q.value == 2

    def test_undo_at_start(self):
        q = history(0)
        assert not q.undo()
        assert q.value == 0

    def test_redo_at_end(self):
        q = history(0)
        q.set(1)
        assert not q.redo()

    def test_history_truncation(self):
        q = history(0)
        q.set(1)
        q.set(2)
        q.undo()
        q.set(3)
        assert not q.redo()
        assert q.value == 3

    def test_max_size(self):
        q = history(0, max_size=3)
        for i in range(1, 10):
            q.set(i)
        assert q.history_size <= 4
