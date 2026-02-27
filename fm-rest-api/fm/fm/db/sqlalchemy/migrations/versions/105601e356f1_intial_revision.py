#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""intial revision

Revision ID: 105601e356f1
Revises:
Create Date: 2025-10-07 08:01:59.588682

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import DATETIME
from oslo_log import log

LOG = log.getLogger(__name__)


# revision identifiers, used by Alembic.
revision: str = '105601e356f1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create event_suppression table first
    op.create_table(
        'event_suppression',
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('deleted_at', sa.DateTime()),
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('uuid', sa.String(36), unique=True, index=True),
        sa.Column('alarm_id', sa.String(15), unique=True, index=True),
        sa.Column('description', sa.String(255)),
        sa.Column('suppression_status', sa.String(15)),
        sa.Column('set_for_deletion', sa.Boolean()),
        sa.Column('mgmt_affecting', sa.String(255)),
        sa.Column('degrade_affecting', sa.String(255)),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    # Determine timestamp column type based on dialect
    bind = op.get_bind()
    if bind.dialect.name == 'mysql':
        LOG.info("alarm dialect is mysql")
        timestamp_type = DATETIME(fsp=6)
    else:
        LOG.info("alarm dialect is others")
        timestamp_type = sa.DateTime(timezone=False)

    # Create alarm table with foreign key
    op.create_table(
        'alarm',
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('deleted_at', sa.DateTime()),
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('uuid', sa.String(255), unique=True, index=True),
        sa.Column('alarm_id', sa.String(255), index=True),
        sa.Column('alarm_state', sa.String(255)),
        sa.Column('entity_type_id', sa.String(255), index=True),
        sa.Column('entity_instance_id', sa.String(255), index=True),
        sa.Column('timestamp', timestamp_type),
        sa.Column('severity', sa.String(255), index=True),
        sa.Column('reason_text', sa.String(255)),
        sa.Column('alarm_type', sa.String(255), index=True),
        sa.Column('probable_cause', sa.String(255)),
        sa.Column('proposed_repair_action', sa.String(255)),
        sa.Column('service_affecting', sa.Boolean()),
        sa.Column('suppression', sa.Boolean()),
        sa.Column('inhibit_alarms', sa.Boolean()),
        sa.Column('masked', sa.Boolean()),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    # Add foreign key constraint for alarm table (skip for SQLite)
    if bind.dialect.name != 'sqlite':
        op.create_foreign_key(
            'fk_alarm_esuppression_alarm_id',
            'alarm', 'event_suppression',
            ['alarm_id'], ['alarm_id']
        )

    # Determine timestamp column type for event_log
    if bind.dialect.name == 'mysql':
        LOG.info("event_log dialect is mysql")
        timestamp_type = DATETIME(fsp=6)
    else:
        LOG.info("event_log dialect is others")
        timestamp_type = sa.DateTime(timezone=False)

    # Create event_log table with foreign key
    op.create_table(
        'event_log',
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('deleted_at', sa.DateTime()),
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('uuid', sa.String(255), unique=True, index=True),
        sa.Column('event_log_id', sa.String(255), index=True),
        sa.Column('state', sa.String(255)),
        sa.Column('entity_type_id', sa.String(255), index=True),
        sa.Column('entity_instance_id', sa.String(255), index=True),
        sa.Column('timestamp', timestamp_type),
        sa.Column('severity', sa.String(255), index=True),
        sa.Column('reason_text', sa.String(255)),
        sa.Column('event_log_type', sa.String(255), index=True),
        sa.Column('probable_cause', sa.String(255)),
        sa.Column('proposed_repair_action', sa.String(255)),
        sa.Column('service_affecting', sa.Boolean()),
        sa.Column('suppression', sa.Boolean()),
        sa.Column('alarm_id', sa.String(255), nullable=True),
        mysql_engine='InnoDB',
        mysql_charset='utf8',
    )

    # Add foreign key constraint for event_log table (skip for SQLite)
    if bind.dialect.name != 'sqlite':
        op.create_foreign_key(
            'fk_elog_alarm_id_esuppression_alarm_id',
            'event_log', 'event_suppression',
            ['alarm_id'], ['alarm_id']
        )


def downgrade():
    raise NotImplementedError('Downgrade from Initial is unsupported.')
