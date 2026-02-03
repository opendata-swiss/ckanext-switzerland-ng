"""This is a copy of migration 62e202866fb5 in for the subscribe plugin:
https://github.com/bellisk/ckanext-subscribe/blob/master/ckanext/subscribe/migration/subscribe/versions/62e202866fb5_create_subscribe_tables.py

ogdch_subscribe needs the same migrations to run as subscribe does, and for the moment it
seems that copying them directly is the best way to handle this.

Revision ID: 2123b60c6e38
Revises:
Create Date: 2025-07-29 14:22:10.610467

"""

import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from ckan.model.types import make_uuid

# revision identifiers, used by Alembic.
revision = "2123b60c6e38"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    engine = op.get_bind()
    inspector = sa.inspect(engine)
    tables = inspector.get_table_names()
    if "subscription" not in tables:
        op.create_table(
            "subscription",
            sa.Column("id", sa.UnicodeText, primary_key=True, default=make_uuid),
            sa.Column("email", sa.UnicodeText, nullable=False),
            sa.Column("object_type", sa.UnicodeText, nullable=False),
            sa.Column("object_id", sa.UnicodeText, nullable=False),
            sa.Column("verified", sa.Boolean, default=False),
            sa.Column("verification_code", sa.UnicodeText),
            sa.Column("verification_code_expires", sa.DateTime),
            sa.Column("created", sa.DateTime, default=datetime.datetime.utcnow),
            sa.Column("frequency", sa.Integer),
        )
    if "subscribe_login_code" not in tables:
        op.create_table(
            "subscribe_login_code",
            sa.Column("id", sa.UnicodeText, primary_key=True, default=make_uuid),
            sa.Column("email", sa.UnicodeText, nullable=False),
            sa.Column("code", sa.UnicodeText, nullable=False),
            sa.Column("expires", sa.DateTime),
        )
    if "subscribe" not in tables:
        op.create_table(
            "subscribe",
            sa.Column("id", sa.UnicodeText, primary_key=True, default=make_uuid),
            sa.Column("frequency", sa.Integer),
            sa.Column("emails_last_sent", sa.DateTime, nullable=False),
        )


def downgrade() -> None:
    op.drop_table("subscription")
    op.drop_table("subscribe_login_code")
    op.drop_table("subscribe")
