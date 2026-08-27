"""Base database table entity module for PynamoDB models."""

from pynamodb.attributes import (
    DiscriminatorAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.models import Model

from src.core.audit import current_utc_time
from src.core.settings import settings


class DurianPyAuditTableMixin:
    """Mixin for PynamoDB table models providing audit metadata attributes."""

    durianpy_created_at = UTCDateTimeAttribute(default=current_utc_time)
    durianpy_updated_at = UTCDateTimeAttribute(default=current_utc_time)
    durianpy_created_by = UnicodeAttribute()
    durianpy_updated_by = UnicodeAttribute(null=True)


class BaseTableEntity(Model, DurianPyAuditTableMixin):
    """Base PynamoDB table model for single-table DynamoDB design."""

    class Meta:
        table_name = f'{settings.ENVIRONMENT.value}-{settings.APP_NAME}-main-table'

        region = settings.REGION
        billing_mode = 'PAY_PER_REQUEST'

    pk = UnicodeAttribute(hash_key=True)
    sk = UnicodeAttribute(range_key=True)
    cls = DiscriminatorAttribute()
