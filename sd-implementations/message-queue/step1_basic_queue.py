"""Step 1: the simplest possible message queue.

A queue is a FIFO buffer that decouples producers from consumers.
"""
from collections import deque


class Queue:
    def __init__(self):
        self._messages = deque()

    def publish(self, body):
        self._messages.append(body)

    def consume(self):
        """Return the oldest message, or None if the queue is empty."""
        if not self._messages:
            return None
        return self._messages.popleft()

    def __len__(self):
        return len(self._messages)


if __name__ == "__main__":
    q = Queue()

    # Producer: knows nothing about the consumer.
    for i in range(3):
        q.publish(f"order-{i}")
    print("queued:", len(q))

    # Consumer: runs later, knows nothing about the producer.
    while (msg := q.consume()) is not None:
        print("got:", msg)
