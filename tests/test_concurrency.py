"""Thread safety and concurrency tests."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from statequark import quark


def test_thread_safety_basic():
    counter = quark(0)

    def worker():
        for _ in range(100):
            counter.set(counter.value + 1)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert counter.value == 500


def test_concurrent_subscriptions():
    sensor = quark(0)
    results = []
    lock = threading.Lock()

    sensor.subscribe(
        lambda q: (lock.acquire(), results.append(q.value), lock.release())
    )

    def worker(start):
        for i in range(10):
            sensor.set(start + i)

    threads = [threading.Thread(target=worker, args=(i * 10,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 30


def test_derived_thread_safety():
    base = quark(0)
    results = []
    lock = threading.Lock()

    derived = quark(lambda get: get(base) * 2, deps=[base])
    derived.subscribe(
        lambda q: (lock.acquire(), results.append(q.value), lock.release())
    )

    def worker():
        for i in range(50):
            base.set(i)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 150


def test_thread_pool_executor():
    counter = quark(0)

    def task():
        counter.set(counter.value + 1)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(task) for _ in range(100)]
        for f in futures:
            f.result()

    assert counter.value == 100


def test_deadlock_prevention():
    q1, q2 = quark(0), quark(0)

    q1.subscribe(lambda q: q2.value)
    q2.subscribe(lambda q: q1.value)

    def worker1():
        for i in range(10):
            q1.set(i)
            time.sleep(0.001)

    def worker2():
        for i in range(10):
            q2.set(i)
            time.sleep(0.001)

    t1 = threading.Thread(target=worker1)
    t2 = threading.Thread(target=worker2)
    t1.start()
    t2.start()

    t1.join(timeout=5.0)
    t2.join(timeout=5.0)

    assert not t1.is_alive()
    assert not t2.is_alive()
