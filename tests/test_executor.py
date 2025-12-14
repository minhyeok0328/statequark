"""Executor tests."""

import threading
import time

import pytest

from statequark import quark
from statequark.executor import (
    cleanup_executor,
    get_executor_manager,
    get_shared_executor,
)


@pytest.fixture(autouse=True)
def reset_executor():
    yield
    get_executor_manager().reset()


def test_executor_singleton():
    assert get_executor_manager() is get_executor_manager()
    assert get_shared_executor() is get_shared_executor()


def test_task_execution():
    executor = get_shared_executor()
    future = executor.submit(lambda: 42)
    assert future.result(timeout=5.0) == 42


def test_with_quarks():
    counter = quark(0)
    results = []

    counter.subscribe(lambda q: results.append(q.value))

    for i in range(5):
        counter.set(i + 1)

    assert results == [1, 2, 3, 4, 5]
    counter.cleanup()


def test_cleanup():
    executor = get_shared_executor()
    assert executor is not None
    cleanup_executor()


def test_concurrent_access():
    results = []
    lock = threading.Lock()

    def worker():
        with lock:
            results.append(get_shared_executor())

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(e is results[0] for e in results)


def test_error_handling():
    executor = get_shared_executor()
    future = executor.submit(lambda: (_ for _ in ()).throw(ValueError("error")))

    with pytest.raises(ValueError):
        future.result(timeout=5.0)


def test_multiple_tasks():
    executor = get_shared_executor()
    results = []
    lock = threading.Lock()

    def task(v):
        time.sleep(0.01)
        with lock:
            results.append(v)
        return v * 2

    futures = [executor.submit(task, i) for i in range(10)]
    task_results = [f.result(timeout=5.0) for f in futures]

    assert sorted(results) == list(range(10))
    assert sorted(task_results) == [i * 2 for i in range(10)]
