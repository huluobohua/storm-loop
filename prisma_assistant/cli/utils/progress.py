"""Progress indicator utilities."""

from contextlib import contextmanager
from typing import Iterator

from tqdm import tqdm


@contextmanager
def progress_bar(iterable, **tqdm_kwargs) -> Iterator:
    bar = tqdm(iterable, **tqdm_kwargs)
    try:
        yield bar
    finally:
        bar.close()
