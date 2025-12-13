"""Tests for middleware utilities."""

from statequark import middleware, persist


class TestMiddleware:
    def test_basic_middleware(self):
        log = []
        q = middleware(0)
        q.use(lambda old, new, next: (log.append((old, new)), next(new)))

        q.set_sync(1)
        q.set_sync(2)
        assert log == [(0, 1), (1, 2)]

    def test_middleware_chain(self):
        q = middleware(0)
        q.use(lambda o, n, next: next(n * 2))
        q.use(lambda o, n, next: next(n + 1))

        q.set_sync(5)
        assert q.value == 11

    def test_persist_middleware(self):
        storage = {}
        q = middleware(0)
        q.use(persist(storage, "count"))

        q.set_sync(42)
        assert storage["count"] == 42
