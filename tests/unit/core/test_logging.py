"""Unit tests for Logger singleton, log_execution decorator, and mask_string utility."""

import logging

import pytest

from src.core.logging import Logger, log_execution, logger, mask_string


class CustomDomainError(Exception):
    """Custom domain exception for testing."""

    pass


class ZeroArgDomainError(Exception):
    """Exception whose constructor takes no arguments."""

    def __init__(self) -> None:
        """Initialize ZeroArgDomainError without arguments."""
        super().__init__('Zero argument domain error')


class SampleService:
    """Sample class to test method decoration."""

    @log_execution
    def do_something(self) -> str:
        """Sample method."""
        return 'success'

    @log_execution(domain_exception=CustomDomainError)
    def fail_with_generic_exception(self) -> None:
        """Sample failing method."""
        raise ValueError('Generic database error')

    @log_execution(domain_exception=CustomDomainError)
    def fail_with_same_domain_exception(self) -> None:
        """Sample failing method with existing domain exception."""
        raise CustomDomainError('Already domain error')

    @log_execution(domain_exception=ZeroArgDomainError)
    def fail_with_zero_arg_domain_exception(self) -> None:
        """Sample failing method with zero-argument domain exception."""
        raise ValueError('Generic error to map to zero-arg')

    @log_execution(domain_exception=CustomDomainError)
    async def async_fail(self) -> None:
        """Sample async failing method."""
        raise KeyError('Generic key error')

    @log_execution(domain_exception=CustomDomainError)
    async def async_succeed(self) -> str:
        """Sample async successful method."""
        return 'async_success'

    @log_execution(domain_exception=CustomDomainError)
    async def async_fail_with_same_domain_exception(self) -> None:
        """Sample async failing method with existing domain exception."""
        raise CustomDomainError('Already async domain error')

    @log_execution(domain_exception=ZeroArgDomainError)
    async def async_fail_with_zero_arg_domain_exception(self) -> None:
        """Sample async failing method with zero-argument domain exception."""
        raise KeyError('Generic key error to map to zero-arg')


class SampleClassWithClassMethod:
    """Sample class with decorated classmethod."""

    @classmethod
    @log_execution
    def sample_classmethod(cls) -> str:
        """Sample classmethod."""
        return 'classmethod_success'


@log_execution
def standalone_function() -> str:
    """Standalone decorated function."""
    return 'standalone_success'


@Logger.log_execution
def static_logger_decorated_function() -> str:
    """Execute decorated function using Logger.log_execution static method."""
    return 'static_decorator_success'


def test_logger_singleton() -> None:
    """Verify that Logger is a singleton and loads defaults from Settings."""
    logger1 = Logger()
    logger2 = Logger.get_logger()
    assert logger1 is logger2


def test_logger_dynamic_delegation(caplog: pytest.LogCaptureFixture) -> None:
    """Verify Logger delegates logging methods to underlying stdlib logger."""
    with caplog.at_level('INFO'):
        logger.info('Test info log')
        logger.warning('Test warning log')

    assert 'Test info log' in caplog.text
    assert 'Test warning log' in caplog.text


def test_logger_level_initialization_branches() -> None:
    """Verify Logger initialization with string and integer log levels."""
    l_str = object.__new__(Logger)
    l_str._Logger__initialized = False
    l_str.__init__(name='test_str_logger', level='DEBUG')
    assert l_str.level == logging.DEBUG

    l_int = object.__new__(Logger)
    l_int._Logger__initialized = False
    l_int.__init__(name='test_int_logger', level=30)
    assert l_int.level == 30

    # Ensure global singleton is in INFO state
    singleton = Logger()
    singleton.setLevel(logging.INFO)


def test_logger_getattr_uninitialized_raises_attribute_error() -> None:
    """Verify accessing attributes on uninitialized Logger raises AttributeError."""
    l_uninit = object.__new__(Logger)
    with pytest.raises(AttributeError) as exc_info:
        _ = l_uninit.some_missing_attribute
    assert "'Logger' object has no attribute 'some_missing_attribute'" in str(exc_info.value)


def test_log_execution_success(caplog: pytest.LogCaptureFixture) -> None:
    """Verify log_execution logs the entrypoint in expected format."""
    service = SampleService()
    with caplog.at_level('INFO'):
        result = service.do_something()

    assert result == 'success'
    assert '[ SampleService ] Executing do_something' in caplog.text


def test_log_execution_domain_exception(caplog: pytest.LogCaptureFixture) -> None:
    """Verify log_execution re-raises the specified domain exception."""
    service = SampleService()
    with caplog.at_level('INFO'):
        with pytest.raises(CustomDomainError) as exc_info:
            service.fail_with_generic_exception()

    assert 'Generic database error' in str(exc_info.value)
    assert '[ SampleService ] Executing fail_with_generic_exception' in caplog.text
    assert '[ SampleService ] Exception in fail_with_generic_exception' in caplog.text


def test_log_execution_existing_domain_exception(caplog: pytest.LogCaptureFixture) -> None:
    """Verify log_execution directly re-raises if exception is already target domain exception."""
    service = SampleService()
    with caplog.at_level('INFO'):
        with pytest.raises(CustomDomainError) as exc_info:
            service.fail_with_same_domain_exception()

    assert 'Already domain error' in str(exc_info.value)


def test_log_execution_zero_arg_domain_exception(caplog: pytest.LogCaptureFixture) -> None:
    """Verify log_execution handles domain exception requiring 0 constructor arguments."""
    service = SampleService()
    with caplog.at_level('INFO'):
        with pytest.raises(ZeroArgDomainError):
            service.fail_with_zero_arg_domain_exception()


def test_log_execution_classmethod_and_standalone(caplog: pytest.LogCaptureFixture) -> None:
    """Verify log_execution extracts correct class/function names for classmethods and functions."""
    with caplog.at_level('INFO'):
        cls_result = SampleClassWithClassMethod.sample_classmethod()
        fn_result = standalone_function()
        static_result = static_logger_decorated_function()

    assert cls_result == 'classmethod_success'
    assert fn_result == 'standalone_success'
    assert static_result == 'static_decorator_success'
    assert '[ SampleClassWithClassMethod ] Executing sample_classmethod' in caplog.text
    assert 'Executing standalone_function' in caplog.text


@pytest.mark.anyio
async def test_log_execution_async_domain_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify async function decoration and domain exception re-raising."""
    service = SampleService()
    with caplog.at_level('INFO'):
        with pytest.raises(CustomDomainError) as exc_info:
            await service.async_fail()

    assert 'Generic key error' in str(exc_info.value)
    assert '[ SampleService ] Executing async_fail' in caplog.text


@pytest.mark.anyio
async def test_log_execution_async_success(caplog: pytest.LogCaptureFixture) -> None:
    """Verify async function decoration logs and returns on success."""
    service = SampleService()
    with caplog.at_level('INFO'):
        result = await service.async_succeed()

    assert result == 'async_success'
    assert '[ SampleService ] Executing async_succeed' in caplog.text


@pytest.mark.anyio
async def test_log_execution_async_existing_domain_exception() -> None:
    """Verify async function decoration directly re-raises if already domain exception."""
    service = SampleService()
    with pytest.raises(CustomDomainError) as exc_info:
        await service.async_fail_with_same_domain_exception()
    assert 'Already async domain error' in str(exc_info.value)


@pytest.mark.anyio
async def test_log_execution_async_zero_arg_domain_exception() -> None:
    """Verify async function decoration handles zero-arg domain exceptions."""
    service = SampleService()
    with pytest.raises(ZeroArgDomainError):
        await service.async_fail_with_zero_arg_domain_exception()


def test_mask_string() -> None:
    """Verify mask_string behavior with various inputs and custom parameters."""
    assert mask_string('1234567890') == '12******90'
    assert mask_string('secret_token', visible_prefix=3, visible_suffix=3) == 'sec******ken'
    assert mask_string('abc', visible_prefix=2, visible_suffix=2) == '***'
    assert mask_string('', visible_prefix=2, visible_suffix=2) == ''
    assert mask_string(None) == ''
    assert mask_string('password', visible_prefix=0, visible_suffix=0) == '********'
    assert mask_string('token', visible_prefix=1, visible_suffix=1, mask_char='#') == 't###n'
    assert Logger.mask_string('1234567890') == '12******90'
