from __future__ import annotations

from collections import deque
from threading import Condition, Thread
from time import sleep

from hotel_booking.notifications import Confirmation, NotificationCounts, NotificationSender


class EmailNotificationSender:
    """Simulated: counts the emails it would send and needs no network."""

    def __init__(self, delay_seconds: float = 0) -> None:
        self.delay_seconds = delay_seconds
        self.sent = 0

    def send_confirmation(self, confirmation: Confirmation) -> None:
        if self.delay_seconds:
            sleep(self.delay_seconds)
        self.sent += 1


class SmsNotificationSender:
    """Simulated, like the email sender."""

    def __init__(self) -> None:
        self.sent = 0

    def send_confirmation(self, confirmation: Confirmation) -> None:
        self.sent += 1


class QueuedNotificationSender:
    """One worker per app process. Capacity zero enables the unbounded experiment."""

    def __init__(self, sender: NotificationSender, capacity: int = 8) -> None:
        if capacity < 0:
            raise ValueError("notification capacity must be nonnegative")
        self._sender = sender
        self._capacity = capacity
        self._pending: deque[Confirmation] = deque()
        self._condition = Condition()
        self._closed = False
        self._sent = self._failed = self._dropped = 0
        self._worker = Thread(target=self._run, name="confirmation-worker")
        self._worker.start()

    def send_confirmation(self, confirmation: Confirmation) -> None:
        with self._condition:
            if self._closed or (self._capacity and len(self._pending) >= self._capacity):
                self._dropped += 1
                return
            self._pending.append(confirmation)
            self._condition.notify()

    def counts(self) -> NotificationCounts:
        with self._condition:
            return NotificationCounts(len(self._pending), self._sent, self._failed, self._dropped)

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._condition.notify_all()
        self._worker.join()

    def _run(self) -> None:
        while True:
            with self._condition:
                self._condition.wait_for(lambda: self._pending or self._closed)
                if not self._pending:
                    return
                confirmation = self._pending.popleft()
            try:
                self._sender.send_confirmation(confirmation)
            except Exception:
                with self._condition:
                    self._failed += 1
            else:
                with self._condition:
                    self._sent += 1
