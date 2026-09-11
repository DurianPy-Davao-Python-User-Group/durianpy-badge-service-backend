"""Badge issuance database table model."""

from pynamodb.attributes import JSONAttribute, UnicodeAttribute
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex

from src.infrastructure.db.models.base_table import BaseTableEntity


class GSI1Index(GlobalSecondaryIndex):
    """GSI1 index for querying badge issuances."""

    class Meta:
        index_name = 'GSI1'
        projection = AllProjection()

    gsi1pk = UnicodeAttribute(hash_key=True, attr_name='GSI1PK')
    gsi1sk = UnicodeAttribute(range_key=True, attr_name='GSI1SK')


class GSI2Index(GlobalSecondaryIndex):
    """GSI2 index for querying badge issuances."""

    class Meta:
        index_name = 'GSI2'
        projection = AllProjection()

    gsi2pk = UnicodeAttribute(hash_key=True, attr_name='GSI2PK')
    gsi2sk = UnicodeAttribute(range_key=True, attr_name='GSI2SK')


class BadgeIssuance(BaseTableEntity, discriminator='BADGEISSUANCE'):
    """
    Badge issuance entity representation in DynamoDB.

    Partition Key format (pk): BADGEISSUANCE#<email>
    Sort Key format (sk): ISSUEDATE#<iso_date>#ISSUANCEID#<issuanceId>
    GSI1 Partition Key format (gsi1pk): MEETUPID#<meetupId>
    GSI1 Sort Key format (gsi1sk): BADGEISSUANCE#<email>
    GSI2 Partition Key format (gsi2pk): ISSUANCEID#<issuanceId>
    GSI2 Sort Key format (gsi2sk): STATUS#<status>
    """

    query_by_meetup_index = GSI1Index()
    query_by_email_issuance_index = GSI2Index()

    gsi1pk = UnicodeAttribute(null=True, attr_name='GSI1PK')
    gsi1sk = UnicodeAttribute(null=True, attr_name='GSI1SK')
    gsi2pk = UnicodeAttribute(null=True, attr_name='GSI2PK')
    gsi2sk = UnicodeAttribute(null=True, attr_name='GSI2SK')

    issuance_id = UnicodeAttribute(null=True)
    design_id = UnicodeAttribute(null=True)
    meetup_id = UnicodeAttribute(null=True)
    role = UnicodeAttribute(null=True)
    updated_by = UnicodeAttribute(null=True)
    previous_assignments = JSONAttribute(null=True)
