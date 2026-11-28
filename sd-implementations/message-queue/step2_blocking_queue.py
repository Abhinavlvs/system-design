"""Step 2: thread-safe queue with blocking consume.

A Condition bundles a lock with wait/notify, so consumers sleep until
a producer signals that a message arrived.
"""
import threading
import time
from collections import deque


class Queue:
    def __init__(self):
        self._messages = deque()
        self._cond = threading.Condition()

    def publish(self, body):
        with self._cond:
            self._messages.append(body)
            self._cond.notify()  # wake one waiting consumer

    def consume(self, timeout=None):
        """Block until a message is available. Return None on timeout."""
        with self._cond:
            if not self._cond.wait_for(lambda: self._messages, timeout):
                return None
            return self._messages.popleft()

    def __len__(self):
        with self._cond:
            return len(self._messages)


if __name__ == "__main__":
    q = Queue()

    def consumer(name):
        while (msg := q.consume(timeout=1)) is not None:
            print(f"{name} got {msg}")

    workers = [threading.Thread(target=consumer, args=(f"c{i}",)) for i in range(2)]
    for w in workers:
        w.start()

    # Consumers are already waiting; producer publishes later.
    for i in range(6):
        time.sleep(0.1)
        q.publish(f"order-{i}")

    for w in workers:
        w.join()
    print("left in queue:", len(q))
