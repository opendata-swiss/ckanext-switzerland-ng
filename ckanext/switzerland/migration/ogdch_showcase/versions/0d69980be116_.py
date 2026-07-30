"""empty message

Revision ID: 0d69980be116
Revises:
Create Date: 2026-07-30 09:22:55.827668

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0d69980be116"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    inspector = sa.inspect(engine)
    tables = inspector.get_table_names()
    if "showcase_package_association" not in tables:
        op.create_table(
            "showcase_package_association",
            sa.Column(
                "package_id",
                sa.UnicodeText,
                sa.ForeignKey("package.id", ondelete="CASCADE", onupdate="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "showcase_id",
                sa.UnicodeText,
                sa.ForeignKey("package.id", ondelete="CASCADE", onupdate="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
        )
    if "showcase_package_association" not in tables:
        op.create_table(
            "showcase_admin",
            sa.Column(
                "user_id",
                sa.UnicodeText,
                sa.ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
        )


def downgrade():
    op.drop_table("showcase_package_association")
    op.drop_table("showcase_admin")
