"""Progress indicator utilities."""

from contextlib import contextmanager
from typing import Iterator, Any

from tqdm import tqdm


@contextmanager
def progress_bar(
    iterable: Any,
    description: str = "Processing",
    **tqdm_kwargs,
) -> Iterator[tqdm]:
    """Context manager for progress bars."""
    bar = tqdm(iterable, desc=description, **tqdm_kwargs)
    try:
        yield bar
    finally:
        bar.close()
