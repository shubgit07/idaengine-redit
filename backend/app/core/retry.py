import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


async def async_retry(
    func: Callable[[], Awaitable[T]],
    retries: int = 3,
    backoff_base: float = 0.5,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """
    Generic async retry with exponential backoff.
    """

    for attempt in range(1, retries + 1):
        try:
            return await func()
        except retry_exceptions as exc:
            if attempt >= retries:
                raise

            sleep_time = backoff_base * (2 ** (attempt - 1))
            logger.warning(
                "Retry attempt %d/%d failed: %s. Retrying in %.2fs",
                attempt,
                retries,
                exc,
                sleep_time,
            )
            await asyncio.sleep(sleep_time)

    raise RuntimeError("Retry failed unexpectedly")
