"""Thread safety and concurrency tests."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from statequark import quark


def test_thread_safety_basic():
    """Test basic thread safety with multiple writers."""
    counter = quark(0)
    results = []

    def worker():
        for i in range(100):
            counter.set_sync(counter.value + 1)
            results.append(counter.value)

    threads = []
    for _ in range(5):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # All increments should be accounted for
    assert counter.value == 500
    assert len(results) == 500


def test_concurrent_subscriptions():
    """Test concurrent subscription callbacks."""
    sensor = quark(0)
    results = []
    lock = threading.Lock()

    def callback(q):
        with lock:
            results.append(q.value)

    sensor.subscribe(callback)

    def update_worker(start_val):
        for i in range(10):
            sensor.set_sync(start_val + i)

    threads = []
    for i in range(3):
        thread = threading.Thread(target=update_worker, args=(i * 10,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Should receive all 30 updates
    assert len(results) == 30


def test_thread_safety_with_derived_quarks():
    """Test thread safety with derived quarks."""
    base = quark(0)
    results = []
    lock = threading.Lock()

    def double(get):
        return get(base) * 2

    def callback(q):
        with lock:
            results.append(q.value)

    derived = quark(double, deps=[base])
    derived.subscribe(callback)

    def worker():
        for i in range(50):
            base.set_sync(i)

    threads = []
    for _ in range(3):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Should receive updates for all changes
    assert len(results) == 150  # 3 threads * 50 updates each


def test_concurrent_subscribe_unsubscribe():
    """Test concurrent subscription and unsubscription operations."""
    sensor = quark(0)
    callbacks_executed = []
    lock = threading.Lock()

    def make_callback(callback_id):
        def callback(q):
            with lock:
                callbacks_executed.append(callback_id)

        return callback

    def subscribe_worker():
        for i in range(10):
            callback = make_callback(f"sub_{threading.current_thread().ident}_{i}")
            sensor.subscribe(callback)
            time.sleep(0.001)  # Small delay
            sensor.unsubscribe(callback)

    def update_worker():
        for i in range(20):
            sensor.set_sync(i)
            time.sleep(0.001)

    # Start subscription threads
    sub_threads = []
    for _ in range(3):
        thread = threading.Thread(target=subscribe_worker)
        sub_threads.append(thread)
        thread.start()

    # Start update thread
    update_thread = threading.Thread(target=update_worker)
    update_thread.start()

    # Wait for all to complete
    for thread in sub_threads:
        thread.join()
    update_thread.join()

    # Test should complete without deadlock or errors
    assert True


def test_thread_pool_executor():
    """Test using ThreadPoolExecutor with quarks."""
    counter = quark(0)
    results = []
    lock = threading.Lock()

    def increment_task():
        current = counter.value
        counter.set_sync(current + 1)
        with lock:
            results.append(counter.value)
        return counter.value

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(increment_task) for _ in range(100)]

        # Wait for all tasks to complete
        for future in futures:
            future.result()

    assert counter.value == 100
    assert len(results) == 100


def test_reader_writer_scenario():
    """Test reader-writer scenario with multiple threads."""
    shared_data = quark({"count": 0, "data": []})
    read_results = []
    lock = threading.Lock()

    def writer():
        for i in range(20):
            current = shared_data.value.copy()
            current["count"] += 1
            current["data"].append(f"item_{i}")
            shared_data.set_sync(current)
            time.sleep(0.001)

    def reader():
        for _ in range(25):
            data = shared_data.value
            with lock:
                read_results.append(data["count"])
            time.sleep(0.001)

    # Start writers and readers
    writer_threads = [threading.Thread(target=writer) for _ in range(2)]
    reader_threads = [threading.Thread(target=reader) for _ in range(3)]

    all_threads = writer_threads + reader_threads

    for thread in all_threads:
        thread.start()

    for thread in all_threads:
        thread.join()

    # Verify final state
    final_data = shared_data.value
    assert final_data["count"] == 40  # 2 writers * 20 increments
    assert len(final_data["data"]) == 40
    assert len(read_results) == 75  # 3 readers * 25 reads


def test_stress_test_subscriptions():
    """Stress test with many subscribers and updates."""
    sensor = quark(0)
    callback_counts = {}
    lock = threading.Lock()

    def make_callback(callback_id):
        def callback(q):
            with lock:
                callback_counts[callback_id] = callback_counts.get(callback_id, 0) + 1

        return callback

    # Add many subscribers
    callbacks = []
    for i in range(50):
        callback = make_callback(f"callback_{i}")
        callbacks.append(callback)
        sensor.subscribe(callback)

    def updater():
        for i in range(20):
            sensor.set_sync(i)

    # Start multiple updater threads
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=updater)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Each callback should have been called 100 times (5 threads * 20 updates)
    for callback_id, count in callback_counts.items():
        assert (
            count == 100
        ), f"Callback {callback_id} called {count} times, expected 100"


def test_deadlock_prevention():
    """Test that operations don't cause deadlocks."""
    quark1 = quark(0)
    quark2 = quark(0)

    def cross_reference_callback1(q):
        # Try to read from quark2 while in quark1's callback
        _ = quark2.value

    def cross_reference_callback2(q):
        # Try to read from quark1 while in quark2's callback
        _ = quark1.value

    quark1.subscribe(cross_reference_callback1)
    quark2.subscribe(cross_reference_callback2)

    def worker1():
        for i in range(10):
            quark1.set_sync(i)
            time.sleep(0.001)

    def worker2():
        for i in range(10):
            quark2.set_sync(i)
            time.sleep(0.001)

    thread1 = threading.Thread(target=worker1)
    thread2 = threading.Thread(target=worker2)

    thread1.start()
    thread2.start()

    # Should complete without deadlock
    thread1.join(timeout=5.0)
    thread2.join(timeout=5.0)

    assert not thread1.is_alive(), "Thread1 appears to be deadlocked"
    assert not thread2.is_alive(), "Thread2 appears to be deadlocked"
