"""Unit tests for Logger singleton, log_execution decorator, and mask_string utility."""

import pytest

from src.core.logging import Logger, log_execution, logger, mask_string


class CustomDomainError(Exception):
    """Custom domain exception for testing."""

    pass


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
    async def async_fail(self) -> None:
        """Sample async failing method."""
        raise KeyError('Generic key error')


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
