"""Step 3: acknowledgements and redelivery.

consume() hands out a message but keeps it in-flight. The consumer must
ack() it when done. nack(), or silence past the visibility timeout,
puts it back on the queue so another consumer can retry.
"""
import itertools
import threading
import time
from collections import deque
from dataclasses import dataclass


@dataclass
class Message:
    id: int
    body: object
    attempts: int = 0


class Queue:
    def __init__(self, visibility_timeout=30.0):
        self._messages = deque()
        self._in_flight = {}  # id -> (Message, deadline)
        self._visibility_timeout = visibility_timeout
        self._ids = itertools.count(1)
        self._cond = threading.Condition()

    def publish(self, body):
        with self._cond:
            self._messages.append(Message(next(self._ids), body))
            self._cond.notify()

    def consume(self, timeout=None):
        """Block until a message is available. Return None on timeout."""
        end = None if timeout is None else time.monotonic() + timeout
        with self._cond:
            while True:
                self._requeue_expired()
                if self._messages:
                    msg = self._messages.popleft()
                    msg.attempts += 1
                    deadline = time.monotonic() + self._visibility_timeout
                    self._in_flight[msg.id] = (msg, deadline)
                    return msg

                now = time.monotonic()
                waits = []
                if end is not None:
                    if end <= now:
                        return None
                    waits.append(end - now)
                if self._in_flight:  # wake up when the next lease expires
                    waits.append(min(d for _, d in self._in_flight.values()) - now)
                self._cond.wait(min(waits) if waits else None)

    def ack(self, msg):
        """Done with the message: delete it for good."""
        with self._cond:
            self._in_flight.pop(msg.id, None)

    def nack(self, msg):
        """Failed: put it back at the front for another attempt."""
        with self._cond:
            if self._in_flight.pop(msg.id, None):
                self._messages.appendleft(msg)
                self._cond.notify()

    def _requeue_expired(self):
        now = time.monotonic()
        for msg_id, (msg, deadline) in list(self._in_flight.items()):
            if deadline <= now:
                del self._in_flight[msg_id]
                self._messages.appendleft(msg)

    def __len__(self):
        with self._cond:
            return len(self._messages)


if __name__ == "__main__":
    q = Queue(visibility_timeout=0.3)
    q.publish("order-1")
    q.publish("order-2")

    # 1. Consumer takes order-1 then "crashes": never acks.
    msg = q.consume()
    print(f"crashing consumer took {msg.body} (attempt {msg.attempts})")

    # 2. Consumer takes order-2, fails, nacks it.
    msg = q.consume()
    print(f"consumer took {msg.body}, failed, nack")
    q.nack(msg)

    # 3. order-2 comes back immediately; this time it succeeds.
    msg = q.consume()
    print(f"consumer took {msg.body} (attempt {msg.attempts}), ack")
    q.ack(msg)

    # 4. order-1 reappears once its visibility timeout expires.
    msg = q.consume(timeout=1)
    print(f"consumer took {msg.body} (attempt {msg.attempts}), ack")
    q.ack(msg)

    print("left in queue:", len(q), "| in flight:", len(q._in_flight))
