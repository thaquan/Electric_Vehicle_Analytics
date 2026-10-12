"""Runtime adapters; business transformations are shared across platforms."""
from contextlib import contextmanager
import sys


def cleanup(actions):
    """Attempt every cleanup without replacing the active processing exception."""
    primary = sys.exception()
    failures = []
    for action in actions:
        try:
            action()
        except Exception as exc:
            failures.append(exc)
    if primary is not None:
        for exc in failures:
            primary.add_note(f'Cleanup failed: {type(exc).__name__}: {exc}')
    elif failures:
        for exc in failures[1:]:
            failures[0].add_note(f'Additional cleanup failure: {exc}')
        raise failures[0]


@contextmanager
def managed_session(factory, stage, *, owned=True):
    session = factory(stage)
    try:
        yield session
    finally:
        if owned:
            cleanup([session.stop])


@contextmanager
def cached_frames(enabled=True):
    frames = []

    def keep(frame):
        if enabled:
            frame = frame.cache()
            frames.append(frame)
        return frame

    try:
        yield keep
    finally:
        cleanup([frame.unpersist for frame in reversed(frames)])
