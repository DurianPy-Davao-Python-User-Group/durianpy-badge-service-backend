"""Badge design database table model."""

from pynamodb.attributes import JSONAttribute, UnicodeAttribute
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex

from src.infrastructure.db.models.base_table import BaseTableEntity


class GSI1Index(GlobalSecondaryIndex):
    """GSI1 for querying badge designs by year and date."""

    class Meta:
        index_name = 'GSI1'
        projection = AllProjection()

    gsi1pk = UnicodeAttribute(hash_key=True)
    gsi1sk = UnicodeAttribute(range_key=True)


class BadgeDesign(BaseTableEntity, discriminator='BADGEDESIGN'):
    """
    Badge design entity representation in DynamoDB.

    Partition Key format (pk): MEETUP#<meetupId>
    Sort Key format (sk): BADGEDESIGN#<designId>
    GSI1 Partition Key format (gsi1pk): YEAR#<YYYY>
    GSI1 Sort Key format (gsi1sk): MEETUPDATE#<iso_date>
    """

    query_by_year_index = GSI1Index()

    gsi1pk = UnicodeAttribute(null=True)
    gsi1sk = UnicodeAttribute(null=True)

    design_id = UnicodeAttribute(null=True)
    meetup_id = UnicodeAttribute(null=True)
    name = UnicodeAttribute(null=True)
    storage_path = UnicodeAttribute(null=True)
    role = UnicodeAttribute(null=True)
    speakers = JSONAttribute(null=True)
    meetup_name = UnicodeAttribute(null=True)
    meetup_date = UnicodeAttribute(null=True)
    venue = UnicodeAttribute(null=True)
