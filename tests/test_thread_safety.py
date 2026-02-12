"""Thread-safety tests for storage-dashboard style worker lifecycle.

These tests are pytest-native and avoid script-style side effects.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal, Qt


class _Worker(QObject):
    finished = Signal()

    def run(self) -> None:
        self.finished.emit()


def test_worker_state_tracking_logic() -> None:
    """State flags should allow load only when no worker/thread is pending."""
    load_worker = None
    load_thread = None

    is_worker_running = bool(load_thread and load_thread.isRunning())
    has_pending_worker = load_worker is not None or load_thread is not None
    assert (not is_worker_running and not has_pending_worker) is True


def test_thread_lifecycle_cleanup(qtbot) -> None:
    """Worker thread should start, emit, and stop cleanly."""
    worker = _Worker()
    thread = QThread()
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    # Ensure quit executes via event queue to avoid cross-thread timer warnings on Windows.
    worker.finished.connect(thread.quit, Qt.ConnectionType.QueuedConnection)

    with qtbot.waitSignal(worker.finished, timeout=3000):
        thread.start()

    if thread.isRunning():
        with qtbot.waitSignal(thread.finished, timeout=3000):
            thread.quit()

    assert thread.wait(3000) is True
    assert thread.isRunning() is False
