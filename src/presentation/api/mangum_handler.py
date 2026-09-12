"""AWS Lambda handler entrypoint integrating Mangum ASGI adapter and Lambda Warmer."""

import asyncio
from typing import Any

import lambdawarmer
from mangum import Mangum

from src.presentation.api.main import app

try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

mangum_handler = Mangum(app, lifespan='off')


@lambdawarmer.warmer
def handler(event: dict[str, Any], context: Any) -> Any:
    """
    AWS Lambda handler entrypoint.

    Handles Lambda warmer ping events to prevent cold starts and proxies standard API
    requests to FastAPI via Mangum adapter.

    :param event: AWS Lambda event payload.
    :type event: dict[str, Any]
    :param context: AWS Lambda execution context object.
    :type context: Any
    :returns: Response payload from Mangum ASGI handler or warmer response.
    :rtype: Any
    """
    return mangum_handler(event, context)
