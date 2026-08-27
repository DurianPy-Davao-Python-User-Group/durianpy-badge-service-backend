"""Logging module providing singleton Logger, decorator, and mask_string utility."""

import datetime
import functools
import inspect
import logging
import sys
import threading
from typing import Any, Callable, Optional, Type, TypeVar, Union

from src.core.settings import LogLevel, Settings

F = TypeVar('F', bound=Callable[..., Any])


class _ISOFormatter(logging.Formatter):
    """Logging formatter that outputs timestamps in ISO 8601 format."""

    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        """
        Format record timestamp into ISO 8601 string representation.

        :param record: Log record containing timestamp.
        :type record: logging.LogRecord
        :param datefmt: Optional date format string (ignored in favor of ISO 8601).
        :type datefmt: Optional[str]
        :returns: ISO 8601 formatted timestamp string.
        :rtype: str
        """
        dt = datetime.datetime.fromtimestamp(record.created).astimezone()
        return dt.isoformat()


class Logger:
    """Singleton Logger class wrapping Python's standard logging module."""

    __instance: Optional['Logger'] = None
    __lock: threading.Lock = threading.Lock()

    def __new__(cls, *_args: Any, **_kwargs: Any) -> 'Logger':
        """
        Create or return the singleton Logger instance.

        :returns: The singleton Logger instance.
        :rtype: Logger
        """
        if cls.__instance is None:
            with cls.__lock:
                if cls.__instance is None:
                    instance = super().__new__(cls)
                    instance.__initialized = False
                    cls.__instance = instance
        return cls.__instance

    def __init__(
        self,
        name: Optional[str] = None,
        level: Optional[Union[str, int, LogLevel]] = None,
    ) -> None:
        """
        Initialize the Logger instance if not already initialized.

        :param name: Optional logger name identifier.
        :type name: Optional[str]
        :param level: Optional log severity level threshold.
        :type level: Optional[Union[str, int, LogLevel]]
        :returns: None
        :rtype: None
        """
        if self.__initialized:
            return

        settings = Settings()
        logger_name = name or settings.APP_NAME
        raw_level = level if level is not None else settings.LOG_LEVEL

        if isinstance(raw_level, LogLevel):
            str_level = raw_level.value
        elif isinstance(raw_level, str):
            str_level = raw_level
        else:
            str_level = None

        if str_level is not None:
            int_level = getattr(logging, str_level.upper(), logging.INFO)
        else:
            int_level = int(raw_level)

        self.__logger = logging.getLogger(logger_name)
        self.__logger.setLevel(int_level)

        if not self.__logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = _ISOFormatter('%(asctime)s [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.__logger.addHandler(handler)

        self.__initialized = True

    @classmethod
    def get_logger(
        cls,
        logger_name: Optional[str] = None,
        log_level: Optional[Union[str, int, LogLevel]] = None,
    ) -> 'Logger':
        """
        Initialize and return the configured singleton Logger instance.

        :param logger_name: Optional logger name identifier.
        :type logger_name: Optional[str]
        :param log_level: Optional log level threshold.
        :type log_level: Optional[Union[str, int, LogLevel]]
        :returns: Configured singleton Logger instance.
        :rtype: Logger
        """
        return cls(name=logger_name, level=log_level)

    @staticmethod
    def log_execution(domain_exception: Optional[Any] = None) -> Any:
        """
        Log function/method entrypoint and optional domain exception mapping.

        :param domain_exception: Optional domain exception class to re-raise upon
            error, or decorated target function.
        :type domain_exception: Optional[Any]
        :returns: Decorated target function or decorator wrapper.
        :rtype: Any
        """
        return log_execution(domain_exception)

    @staticmethod
    def mask_string(
        value: Optional[str],
        visible_prefix: int = 2,
        visible_suffix: int = 2,
        mask_char: str = '*',
    ) -> str:
        """
        Mask sensitive string data while preserving visible prefix and suffix.

        :param value: The string value to mask.
        :type value: Optional[str]
        :param visible_prefix: Number of characters to leave visible at the start.
        :type visible_prefix: int
        :param visible_suffix: Number of characters to leave visible at the end.
        :type visible_suffix: int
        :param mask_char: Masking character used to hide middle content.
        :type mask_char: str
        :returns: The masked string representation.
        :rtype: str
        """
        return mask_string(
            value,
            visible_prefix=visible_prefix,
            visible_suffix=visible_suffix,
            mask_char=mask_char,
        )

    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to underlying logging.Logger instance.

        :param name: Attribute or method name to access.
        :type name: str
        :returns: Attribute from underlying logger instance.
        :rtype: Any
        """
        logger_inst = self.__dict__.get('_Logger__logger')
        if logger_inst is not None:
            return getattr(logger_inst, name)
        raise AttributeError(f"'Logger' object has no attribute '{name}'")


def __extract_class_name(func: Callable[..., Any], args: tuple[Any, ...]) -> str:
    """Extract class name or module name for logging format."""
    if args:
        first_arg = args[0]
        if inspect.isclass(first_arg):
            return first_arg.__name__
        if hasattr(first_arg, '__class__') and '.' in getattr(func, '__qualname__', ''):
            return first_arg.__class__.__name__

    qualname = getattr(func, '__qualname__', '')
    if '.' in qualname:
        return qualname.rsplit('.', 1)[0]

    return getattr(func, '__module__', 'App')


def __decorate(
    func: Callable[..., Any],
    domain_exception: Optional[Type[BaseException]],
) -> Any:
    """Apply entrypoint logging and domain exception mapping to a function."""
    logger = Logger()

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            classname = __extract_class_name(func, args)
            methodname = getattr(func, '__name__', str(func))
            logger.info(f'[ {classname} ] Executing {methodname}')
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                logger.error(f'[ {classname} ] Exception in {methodname}: {exc}')
                if domain_exception is not None:
                    if isinstance(exc, domain_exception):
                        raise
                    try:
                        raise domain_exception(str(exc)) from exc
                    except TypeError:
                        raise domain_exception() from exc
                raise

        return async_wrapper

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        classname = __extract_class_name(func, args)
        methodname = getattr(func, '__name__', str(func))
        logger.info(f'[ {classname} ] Executing {methodname}')
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            logger.error(f'[ {classname} ] Exception in {methodname}: {exc}')
            if domain_exception is not None:
                if isinstance(exc, domain_exception):
                    raise
                try:
                    raise domain_exception(str(exc)) from exc
                except TypeError:
                    raise domain_exception() from exc
            raise

    return sync_wrapper


def log_execution(
    domain_exception: Optional[Any] = None,
) -> Any:
    """
    Log function/method entrypoint and optional domain exception mapping.

    :param domain_exception: Optional domain exception class to re-raise upon
        error, or decorated target function.
    :type domain_exception: Optional[Any]
    :returns: Decorated target function or decorator wrapper.
    :rtype: Any
    """
    if callable(domain_exception) and not (
        inspect.isclass(domain_exception) and issubclass(domain_exception, BaseException)
    ):
        func = domain_exception
        return __decorate(func, None)

    def decorator(func: F) -> F:
        return __decorate(func, domain_exception)

    return decorator


def mask_string(
    value: Optional[str],
    visible_prefix: int = 2,
    visible_suffix: int = 2,
    mask_char: str = '*',
) -> str:
    """
    Mask sensitive string data while preserving visible prefix and suffix characters.

    :param value: The string value to mask.
    :type value: Optional[str]
    :param visible_prefix: Number of characters to leave visible at the start.
    :type visible_prefix: int
    :param visible_suffix: Number of characters to leave visible at the end.
    :type visible_suffix: int
    :param mask_char: Masking character used to hide middle content.
    :type mask_char: str
    :returns: The masked string representation.
    :rtype: str
    """
    if not value:
        return ''

    str_val = str(value)
    length = len(str_val)

    prefix_len = max(0, visible_prefix)
    suffix_len = max(0, visible_suffix)

    if length <= prefix_len + suffix_len:
        return mask_char * length

    prefix = str_val[:prefix_len]
    suffix = str_val[length - suffix_len :] if suffix_len > 0 else ''
    masked_part = mask_char * (length - prefix_len - suffix_len)

    return f'{prefix}{masked_part}{suffix}'


logger = Logger()
