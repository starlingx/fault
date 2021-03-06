#
# Copyright (c) 2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy import Boolean, Integer, DateTime
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.schema import ForeignKeyConstraint
from oslo_log import log
LOG = log.getLogger(__name__)
ENGINE = 'InnoDB'
CHARSET = 'utf8'


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    event_suppression = Table(
        'event_suppression',
        meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),

        Column('id', Integer, primary_key=True, nullable=False),
        Column('uuid', String(36), unique=True, index=True),
        Column('alarm_id', String(15), unique=True, index=True),
        Column('description', String(255)),
        Column('suppression_status', String(15)),
        Column('set_for_deletion', Boolean),
        Column('mgmt_affecting', String(255)),
        Column('degrade_affecting', String(255)),

        mysql_engine=ENGINE,
        mysql_charset=CHARSET,
    )
    event_suppression.create()
    if migrate_engine.url.get_dialect().name == 'mysql':
        LOG.info("alarm dialect is mysql")
        timestamp_column = Column('timestamp', DATETIME(fsp=6))
    else:
        LOG.info("alarm dialect is others")
        timestamp_column = Column('timestamp', DateTime(timezone=False))
    alarm = Table(
        'alarm',
        meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('id', Integer, primary_key=True, nullable=False),
        Column('uuid', String(255), unique=True, index=True),
        Column('alarm_id', String(255), index=True),
        Column('alarm_state', String(255)),
        Column('entity_type_id', String(255), index=True),
        Column('entity_instance_id', String(255), index=True),
        timestamp_column,
        Column('severity', String(255), index=True),
        Column('reason_text', String(255)),
        Column('alarm_type', String(255), index=True),
        Column('probable_cause', String(255)),
        Column('proposed_repair_action', String(255)),
        Column('service_affecting', Boolean),
        Column('suppression', Boolean),
        Column('inhibit_alarms', Boolean),
        Column('masked', Boolean),
        ForeignKeyConstraint(
            ['alarm_id'],
            ['event_suppression.alarm_id'],
            use_alter=True,
            name='fk_alarm_esuppression_alarm_id'
        ),

        mysql_engine=ENGINE,
        mysql_charset=CHARSET,
    )
    alarm.create()
    if migrate_engine.url.get_dialect().name == 'mysql':
        LOG.info("event_log dialect is mysql")
        timestamp_column = Column('timestamp', DATETIME(fsp=6))
    else:
        LOG.info("event_log dialect is others")
        timestamp_column = Column('timestamp', DateTime(timezone=False))

    event_log = Table(
        'event_log',
        meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),

        Column('id', Integer, primary_key=True, nullable=False),
        Column('uuid', String(255), unique=True, index=True),
        Column('event_log_id', String(255), index=True),
        Column('state', String(255)),
        Column('entity_type_id', String(255), index=True),
        Column('entity_instance_id', String(255), index=True),
        timestamp_column,
        Column('severity', String(255), index=True),
        Column('reason_text', String(255)),
        Column('event_log_type', String(255), index=True),
        Column('probable_cause', String(255)),
        Column('proposed_repair_action', String(255)),
        Column('service_affecting', Boolean),
        Column('suppression', Boolean),
        Column('alarm_id', String(255), nullable=True),
        ForeignKeyConstraint(
            ['alarm_id'],
            ['event_suppression.alarm_id'],
            use_alter=True,
            name='fk_elog_alarm_id_esuppression_alarm_id'
        ),

        mysql_engine=ENGINE,
        mysql_charset=CHARSET,
    )
    event_log.create()


def downgrade(migrate_engine):
    raise NotImplementedError('Downgrade from Initial is unsupported.')
