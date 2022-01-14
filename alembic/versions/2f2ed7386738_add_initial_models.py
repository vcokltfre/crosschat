"""add initial models

Revision ID: 2f2ed7386738
Revises: 
Create Date: 2022-01-14 00:21:00.777493

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "2f2ed7386738"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "channels",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("flags", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("flags", sa.BigInteger(), nullable=True),
        sa.Column("banned", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "channel_map",
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("channel", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["channel"], ["channels.id"], name="fk_channel_map_channels_id_channel"),
        sa.PrimaryKeyConstraint("channel_id"),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("original_id", sa.BigInteger(), nullable=True),
        sa.Column("flags", sa.BigInteger(), nullable=True),
        sa.Column("channel", sa.BigInteger(), nullable=True),
        sa.Column("user", sa.BigInteger(), nullable=True),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["channel"], ["channels.id"], name="fk_messages_channels_id_channel"),
        sa.ForeignKeyConstraint(["user"], ["users.id"], name="fk_messages_users_id_user"),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("messages")
    op.drop_table("channel_map")
    op.drop_table("users")
    op.drop_table("channels")
    # ### end Alembic commands ###
