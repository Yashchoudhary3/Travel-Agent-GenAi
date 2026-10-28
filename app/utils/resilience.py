import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry_call(
    fn: Callable[[], T],
    *,
    retries: int = 3,
    backoff: float = 0.6,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    fallback: T | Callable[[], T] | None = None,
) -> T:
    last_error: BaseException | None = None

    for attempt in range(retries):
        try:
            return fn()
        except exceptions as error:
            last_error = error
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt))

    if fallback is not None:
        return fallback() if callable(fallback) else fallback

    if last_error is not None:
        raise last_error

    raise RuntimeError("retry_call failed without an exception")


def invoke_with_retry(llm, prompt, retries: int = 3):
    return retry_call(
        lambda: llm.invoke(prompt),
        retries=retries,
        backoff=0.8,
    )
