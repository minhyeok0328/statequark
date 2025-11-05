"""Tests for executor management."""

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
    """Reset executor after each test to ensure test isolation."""
    yield
    # Reset executor after each test
    manager = get_executor_manager()
    manager.reset()


def test_executor_manager_singleton():
    """Test that ExecutorManager is a singleton."""
    manager1 = get_executor_manager()
    manager2 = get_executor_manager()

    assert manager1 is manager2


def test_get_shared_executor():
    """Test getting the shared executor."""
    executor = get_shared_executor()
    assert executor is not None

    # Getting it again should return the same instance
    executor2 = get_shared_executor()
    assert executor is executor2


def test_executor_task_execution():
    """Test that executor can run tasks."""
    executor = get_shared_executor()
    results = []

    def task():
        results.append(threading.current_thread().name)
        return 42

    future = executor.submit(task)
    result = future.result(timeout=5.0)

    assert result == 42
    assert len(results) == 1
    assert "quark-callback" in results[0]


def test_executor_with_quarks():
    """Test executor integration with quarks."""
    counter = quark(0)
    callback_results = []

    def callback(q):
        callback_results.append(q.value)
        time.sleep(0.01)  # Simulate some work

    counter.subscribe(callback)

    # Trigger multiple updates
    for i in range(5):
        counter.set_sync(i + 1)

    # All callbacks should have executed
    assert callback_results == [1, 2, 3, 4, 5]

    counter.cleanup()


def test_executor_cleanup():
    """Test executor cleanup."""
    # Get executor to ensure it's created
    executor = get_shared_executor()
    assert executor is not None

    # Clean up
    cleanup_executor()

    # After cleanup, getting executor should raise an error or create a new one
    # depending on implementation


def test_concurrent_executor_access():
    """Test concurrent access to executor."""
    results = []
    lock = threading.Lock()

    def worker():
        executor = get_shared_executor()
        with lock:
            results.append(executor)

    threads = [threading.Thread(target=worker) for _ in range(10)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # All threads should get the same executor
    assert len(results) == 10
    assert all(executor is results[0] for executor in results)


def test_executor_error_handling():
    """Test error handling in executor tasks."""
    executor = get_shared_executor()

    def failing_task():
        raise ValueError("Test error")

    future = executor.submit(failing_task)

    with pytest.raises(ValueError, match="Test error"):
        future.result(timeout=5.0)


def test_executor_multiple_tasks():
    """Test running multiple tasks concurrently."""
    executor = get_shared_executor()
    results = []
    lock = threading.Lock()

    def task(value):
        time.sleep(0.01)
        with lock:
            results.append(value)
        return value * 2

    futures = [executor.submit(task, i) for i in range(10)]

    # Wait for all tasks to complete
    task_results = [future.result(timeout=5.0) for future in futures]

    assert len(results) == 10
    assert sorted(results) == list(range(10))
    assert sorted(task_results) == [i * 2 for i in range(10)]


def test_executor_manager_reset():
    """Test resetting executor manager."""
    manager = get_executor_manager()

    # Get executor to ensure it's created
    executor1 = manager.get_executor()
    assert executor1 is not None

    # Reset the manager
    manager.reset()

    # Getting executor again should work
    executor2 = manager.get_executor()
    assert executor2 is not None
