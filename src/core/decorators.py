import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

http_retry = retry(
    stop=stop_after_attempt(3),                          
    wait=wait_exponential(multiplier=1, min=2, max=10), 
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    reraise=True                                         
)
  
def log_execution(level: int = logging.INFO) -> Callable:
    """Logging start, end event, elapsed time and optional exceptions"""
    def decorator(func: Callable) -> Callable:
        logger = logging.getLogger(func.__module__)
        
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            func_name = func.__name__
            logger.log(level, "Executing %s...", func_name)
            start_time = time.perf_counter()

            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                logger.log(level, "Finished %s in %.4fs", func_name, duration)
                return result
            except Exception as exc:
                duration = time.perf_counter() - start_time
                logger.exception(
                    "Failed %s after %.4fs with error: %s", func_name, duration, exc
                )
                raise exc

        return wrapper
    return decorator
