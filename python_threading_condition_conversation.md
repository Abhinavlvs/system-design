# Python `threading.Condition()` --- Conversation Notes

This document captures the conversation about how Python's
`threading.Condition()` works, including multiple consumers, `notify()`
versus `notify_all()`, concurrency, and a complete producer-consumer
example.

------------------------------------------------------------------------

## User question

How threading.Condition() works in Python

## Explanation: What is `threading.Condition()`?

`threading.Condition()` is a synchronization primitive that allows
threads to wait until shared state satisfies a condition.

It combines:

1.  A lock, which protects shared state.
2.  A waiting mechanism, which lets a thread sleep instead of repeatedly
    checking.
3.  A notification mechanism, which lets another thread signal that
    shared state may have changed.

A typical producer-consumer arrangement:

-   A consumer waits while a queue is empty.
-   A producer adds data to the queue.
-   The producer notifies waiting consumers.
-   A consumer wakes, reacquires the lock, checks the queue again, and
    consumes an item.

### Basic example

``` python
import threading
import time

condition = threading.Condition()
data_available = False


def consumer():
    global data_available

    with condition:
        print("Consumer: Waiting for data...")

        while not data_available:
            condition.wait()

        print("Consumer: Data is available!")


def producer():
    global data_available

    time.sleep(2)

    with condition:
        print("Producer: Producing data...")
        data_available = True
        condition.notify()


t1 = threading.Thread(target=consumer)
t2 = threading.Thread(target=producer)

t1.start()
t2.start()

t1.join()
t2.join()
```

### What happens during `wait()`?

When `condition.wait()` is called while holding the condition lock, it:

1.  Releases the underlying lock.
2.  Puts the calling thread into a waiting state.
3.  Blocks until it is notified or its timeout expires.
4.  Reacquires the lock before returning.

The awakened thread does not immediately continue inside the critical
section. It must first reacquire the lock.

### What does `notify()` do?

``` python
with condition:
    data_available = True
    condition.notify()
```

`notify()` wakes one thread waiting on that condition. It does not
release the lock. The notifying thread continues until it releases the
lock; then the awakened thread can compete to reacquire it.

### `notify()` and `notify_all()`

  Method           Behaviour
  ---------------- -----------------------------
  `wait()`         Releases the lock and waits
  `notify()`       Wakes one waiting thread
  `notify_all()`   Wakes all waiting threads

Call `wait()`, `notify()`, and `notify_all()` while holding the
condition lock.

### Why use `while`, not `if`?

Use:

``` python
with condition:
    while not data_available:
        condition.wait()
```

rather than:

``` python
with condition:
    if not data_available:
        condition.wait()
```

A thread can wake spuriously, or another consumer may consume the
available item before this thread reacquires the lock. Therefore, the
predicate must be checked again after waking.

`Condition.wait_for(predicate)` is a convenient way to perform this
predicate-checking loop:

``` python
with condition:
    condition.wait_for(lambda: data_available)
```

### Producer-consumer queue example

``` python
import threading
from collections import deque

class Queue:
    def __init__(self):
        self.items = deque()
        self.condition = threading.Condition()

    def put(self, item):
        with self.condition:
            self.items.append(item)
            self.condition.notify()

    def get(self):
        with self.condition:
            self.condition.wait_for(
                lambda: len(self.items) > 0
            )
            return self.items.popleft()
```

### Condition vs Lock vs Event

  Primitive     Purpose
  ------------- -----------------------------------------------
  `Lock`        Protect a critical section
  `Event`       Signal that something has happened
  `Condition`   Wait until shared state satisfies a predicate

A `Condition` uses a lock and waiting threads internally. By default,
`threading.Condition()` uses an `RLock`.

------------------------------------------------------------------------

## User question

Questions:

1.  In cases of multiple workers or threads, How the code above behaves
2.  difference b/w notify and notify in case of multiple workers
    watching the queue
3.  If there 3 workers, which one get notified when data is available

## Explanation: Multiple workers

Suppose three consumers --- Worker A, Worker B, and Worker C --- are
waiting on the same condition because the queue is empty.

When the producer adds one item and calls `notify()`:

-   One waiting worker is awakened.
-   That worker must reacquire the condition lock.
-   It checks the queue and consumes the item.
-   The other workers remain waiting.

The worker that wakes is not a task assignment chosen by application
logic.

### `notify()` versus `notify_all()`

Assume all three workers are waiting and the producer adds one item.

With `notify()`:

``` python
with condition:
    items.append("item-1")
    condition.notify()
```

Only one waiting worker is awakened.

With `notify_all()`:

``` python
with condition:
    items.append("item-1")
    condition.notify_all()
```

All waiting workers are awakened and compete to reacquire the same lock.
They do not all enter the critical section simultaneously.

If Worker A gets the lock first and consumes the only item, Workers B
and C will later acquire the lock, find the queue empty, and wait again.

**Important:** `notify_all()` does not mean all workers will consume an
item. It means all waiting workers are given a chance to wake up and
recheck the predicate.

### Which worker gets notified?

Python does not provide an application-level guarantee that a particular
worker will be selected, nor should code rely on a particular scheduling
order.

In current CPython implementations, condition waiters are maintained in
a deque and `notify()` generally selects the oldest waiter first.
However, FIFO ordering is not a general Python API guarantee. Also,
being notified and actually acquiring the lock are separate events.

If specific workers must receive specific tasks, use explicit task
routing, such as one queue per worker, or implement a scheduler.

### What if the producer adds three items?

If three workers are waiting, the producer can add three items and call
`notify()` three times:

``` python
with condition:
    items.extend([1, 2, 3])

    condition.notify()
    condition.notify()
    condition.notify()
```

This wakes up to three waiting threads. Each competes for the lock and
can remove one item.

Alternatively:

``` python
with condition:
    items.extend([1, 2, 3])
    condition.notify_all()
```

This wakes all waiting workers, even if there are more workers than
available items. Workers that find no item must wait again.

### Condition vs `queue.Queue`

  Feature                    Condition          `queue.Queue`
  -------------------------- ------------------ ---------------
  Thread synchronization     Yes                Yes
  Waiting for data           You implement it   Built in
  Multiple consumers         Yes                Yes
  Multiple producers         Yes                Yes
  Task distribution          You implement it   Built in
  Bounded capacity           You implement it   Built in
  Task completion tracking   You implement it   Built in

For ordinary producer-consumer workloads, `queue.Queue` is usually the
simpler choice. Use `Condition` when coordinating more complex shared
state or custom synchronization rules.

------------------------------------------------------------------------

## User question

when published adds 3 items at a time, with notify all the threads need
run one after another , becuase the self.items is held by one worker.
with notiyf all parllel execution is possible , is it ?

## Explanation: Parallel wake-up vs parallel execution

The distinction is between:

-   **Queue access:** serialized because all workers use the same lock.
-   **Task processing:** can happen concurrently if it occurs after
    releasing the lock.

For example:

``` python
def get(self):
    with self.condition:
        self.condition.wait_for(
            lambda: len(self.items) > 0
        )
        item = self.items.popleft()

    # The lock has been released.
    return item


def worker():
    while True:
        item = queue.get()
        process(item)  # Outside the lock
```

If the producer adds three items and calls `notify_all()`:

1.  All waiting workers wake and compete for the lock.
2.  One worker at a time acquires the lock and removes an item.
3.  Each worker releases the lock after removing its item.
4.  Workers can then process their separate items concurrently.

Do not hold the queue lock while performing slow processing. Otherwise,
workers would be forced to process serially.

### What if only `notify()` is used?

If the producer adds three items but calls `notify()` only once, only
one waiting worker is awakened. That worker may remove one item and
process it, while the other items remain queued and other workers remain
asleep.

If no further notification occurs, those workers may remain asleep even
though the queue contains work.

For batch insertion, `notify_all()` is a reasonable approach. Another
design is to call `notify()` once per added item.

### GIL consideration

In standard GIL-enabled CPython, threads doing CPU-bound Python work
generally do not execute Python bytecode in parallel across CPU cores.
I/O-bound work can overlap. Free-threaded Python builds can allow
parallel Python execution.

------------------------------------------------------------------------

## User request

give me full example

## Complete runnable example

This example uses:

-   One producer.
-   Three consumer workers.
-   A shared `deque`.
-   One `threading.Condition`.
-   Batches of three tasks.
-   `notify_all()` for each batch.
-   Processing outside the lock.
-   One sentinel (`None`) per worker for graceful shutdown.

``` python
import threading
import time
from collections import deque


class TaskQueue:

    def __init__(self):
        self.items = deque()
        self.condition = threading.Condition()

    def put_many(self, new_items):
        """Producer adds multiple items."""

        with self.condition:
            self.items.extend(new_items)

            print(
                f"\\n[PRODUCER] Added {new_items}. "
                f"Queue size: {len(self.items)}"
            )

            # Wake all waiting consumers
            self.condition.notify_all()

    def get(self):
        """Consumer retrieves one item."""

        with self.condition:

            # Wait until items are available
            self.condition.wait_for(
                lambda: len(self.items) > 0
            )

            # Remove one item while holding the lock
            item = self.items.popleft()

            print(
                f"[{threading.current_thread().name}] "
                f"Retrieved {item}. "
                f"Remaining: {len(self.items)}"
            )

        # Lock is released before returning
        return item


def process(item):
    """Simulate some time-consuming work."""

    worker = threading.current_thread().name

    print(f"[{worker}] Processing {item}...")

    # Simulate I/O-bound work
    time.sleep(3)

    print(f"[{worker}] Completed {item}")


def worker(queue):

    while True:

        item = queue.get()

        # Special value indicates shutdown
        if item is None:
            print(
                f"[{threading.current_thread().name}] "
                "Shutting down."
            )
            break

        # Processing happens OUTSIDE the lock
        process(item)


def main():

    queue = TaskQueue()

    # Create 3 consumer workers
    workers = [
        threading.Thread(
            target=worker,
            args=(queue,),
            name=f"Worker-{i}"
        )
        for i in range(1, 4)
    ]

    # Start workers
    for w in workers:
        w.start()

    # Producer adds 3 batches
    batches = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]

    for batch in batches:
        queue.put_many(batch)

        # Wait before adding the next batch
        time.sleep(4)

    # Graceful shutdown: one poison pill per worker
    queue.put_many([None, None, None])

    # Wait for all workers to finish
    for w in workers:
        w.join()

    print("\\nAll workers finished.")


if __name__ == "__main__":
    main()
```

### How the first batch runs

1.  All three workers initially wait because the queue is empty.
2.  The producer adds `[1, 2, 3]` and calls `notify_all()`.
3.  All three workers wake and compete for the condition lock.
4.  One worker at a time removes one item from the queue.
5.  Each worker releases the lock after removing its item.
6.  The workers process their items outside the lock, so their
    processing can overlap.

The exact worker-to-item assignment and print ordering are
nondeterministic.

### Illustrative output

``` text
[PRODUCER] Added [1, 2, 3]. Queue size: 3

[Worker-1] Retrieved 1. Remaining: 2
[Worker-1] Processing 1...

[Worker-2] Retrieved 2. Remaining: 1
[Worker-2] Processing 2...

[Worker-3] Retrieved 3. Remaining: 0
[Worker-3] Processing 3...

[Worker-1] Completed 1
[Worker-2] Completed 2
[Worker-3] Completed 3

[PRODUCER] Added [4, 5, 6]. Queue size: 3
...
```

Actual worker assignment and output ordering may differ.

### Experiment: change `notify_all()` to `notify()`

Replace:

``` python
self.condition.notify_all()
```

with:

``` python
self.condition.notify()
```

Now only one waiting worker is awakened per batch. Since the producer
adds three items but wakes only one worker, the other items may remain
in the queue while the other workers sleep. This illustrates why
`notify_all()` can be useful for batch insertion.

### Core takeaway

**A condition notification is not a task assignment. It is a signal that
shared state may have changed.**

-   `notify_all()` wakes all waiting workers.
-   The shared lock serializes access to the queue.
-   Releasing the lock before processing allows workers to process
    independently.
-   In GIL-enabled CPython, I/O-bound tasks can overlap, while CPU-bound
    Python tasks generally need multiprocessing or a free-threaded build
    for true multi-core parallelism.
