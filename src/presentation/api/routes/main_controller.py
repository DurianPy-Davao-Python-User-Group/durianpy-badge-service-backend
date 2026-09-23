"""Main application API route controller."""

from fastapi import APIRouter

from src.presentation.api.routes.docs_controller import (
    router as docs_router,
)
from src.presentation.api.routes.public_catalog_controller import (
    router as public_catalog_router,
)
from src.presentation.api.routes.test_techtix_gateway import (
    router as techtix_test_router,
)

api_router = APIRouter()
api_router.include_router(public_catalog_router)
api_router.include_router(docs_router)
api_router.include_router(techtix_test_router)
