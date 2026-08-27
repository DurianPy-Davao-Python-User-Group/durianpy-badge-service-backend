"""Unit tests for core audit mixin and helper utilities."""

from datetime import datetime, timezone

from pydantic import BaseModel

from src.core.audit import DurianPyAuditMixin, current_utc_time


class SampleAuditModel(DurianPyAuditMixin, BaseModel):
    """Sample Pydantic model inheriting audit mixin."""

    name: str


def test_current_utc_time() -> None:
    """Verify current_utc_time returns timezone-aware UTC datetime."""
    now = current_utc_time()
    assert isinstance(now, datetime)
    assert now.tzinfo == timezone.utc


def test_durianpy_audit_mixin_defaults() -> None:
    """Verify DurianPyAuditMixin populates created_at and updated_at automatically."""
    model = SampleAuditModel(name='test', durianpy_created_by='user_123')
    assert model.name == 'test'
    assert model.durianpy_created_by == 'user_123'
    assert model.durianpy_updated_by is None
    assert isinstance(model.durianpy_created_at, datetime)
    assert isinstance(model.durianpy_updated_at, datetime)
    assert model.durianpy_created_at.tzinfo == timezone.utc
    assert model.durianpy_updated_at.tzinfo == timezone.utc


def test_durianpy_audit_mixin_explicit_values() -> None:
    """Verify DurianPyAuditMixin accepts explicit values for all fields."""
    created_at = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    updated_at = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    model = SampleAuditModel(
        name='test',
        durianpy_created_at=created_at,
        durianpy_updated_at=updated_at,
        durianpy_created_by='admin',
        durianpy_updated_by='editor',
    )
    assert model.durianpy_created_at == created_at
    assert model.durianpy_updated_at == updated_at
    assert model.durianpy_created_by == 'admin'
    assert model.durianpy_updated_by == 'editor'
