"""Unit tests for the AWS Lambda Mangum handler entrypoint and warmer integration."""

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

from src.presentation.api.mangum_handler import handler


def test_mangum_handler_warmer_event() -> None:
    """
    Verify Lambda Warmer event is intercepted and returns without executing ASGI application.

    :returns: None
    """
    event: dict[str, Any] = {'warmer': True}
    context = MagicMock()
    with patch('src.presentation.api.mangum_handler.mangum_handler') as mock_mangum:
        result = handler(event, context)
        assert result is None
        mock_mangum.assert_not_called()


def test_mangum_handler_http_event() -> None:
    """
    Verify API Gateway HTTP API v2 event is processed by Mangum and routed to FastAPI.

    :returns: None
    """
    event: dict[str, Any] = {
        'version': '2.0',
        'routeKey': 'GET /health',
        'rawPath': '/health',
        'rawQueryString': '',
        'headers': {
            'host': 'api.example.com',
            'x-forwarded-proto': 'https',
        },
        'requestContext': {
            'http': {
                'method': 'GET',
                'path': '/health',
                'protocol': 'HTTP/1.1',
                'sourceIp': '127.0.0.1',
                'userAgent': 'pytest',
            },
            'stage': '$default',
        },
        'isBase64Encoded': False,
    }
    context = MagicMock()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        response = handler(event, context)
    finally:
        loop.close()
        asyncio.set_event_loop(None)

    assert response['statusCode'] == 200
    assert '"OK"' in response['body']
