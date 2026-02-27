#
# Copyright (c) 2018, 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


import os

import sqlalchemy
from oslo_db.sqlalchemy import enginefacade

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext

from fm.common import exceptions
from fm.common.i18n import _


LEGACY_TO_ALEMBIC_REVISION = {
    1: "105601e356f1",
}

get_engine = enginefacade.get_legacy_facade().get_engine


def db_sync(version=None):
    # Reject old sqlalchemy-migrate style numeric versions
    if version is not None and str(version).isdigit():
        raise exceptions.Invalid(
            'You requested an sqlalchemy-migrate database version; this is '
            'no longer supported'
        )

    engine = get_engine()

    with engine.begin() as connection:
        config = _get_alembic_config(connection)

        # Ensure database is under Alembic control, or bridge from migrate_version
        db_version(connection=connection)

        if version is None:
            command.upgrade(config, "head")
        else:
            command.upgrade(config, version)


def db_version(connection=None):
    if connection is None:
        with get_engine().begin() as conn:
            return db_version(connection=conn)

    try:
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()
    except Exception as exc:
        raise exceptions.SysinvException(
            _("Failed to determine Alembic revision: %s") % exc
        )

    if current_rev is not None:
        return current_rev

    inspector = sqlalchemy.inspect(connection)
    tables = inspector.get_table_names()

    if len(tables) == 0:
        cfg = _get_alembic_config(connection)
        command.stamp(cfg, "base")
        return "base"

    if "migrate_version" not in tables:
        raise exceptions.ApiError(
            _("Upgrade to 25.09 or 26.03 first")
        )

    legacy_version = connection.execute(
        sqlalchemy.text("SELECT version FROM migrate_version")
    ).scalar()

    alembic_revision = LEGACY_TO_ALEMBIC_REVISION[legacy_version]

    cfg = _get_alembic_config(connection)
    command.stamp(cfg, alembic_revision)
    return alembic_revision


def db_version_control(version=None, connection=None):
    if connection is None:
        with get_engine().begin() as conn:
            return db_version_control(version=version, connection=conn)

    cfg = _get_alembic_config(connection)
    revision = "base" if version is None else version
    command.stamp(cfg, revision)
    return revision


def _get_alembic_config(connection=None):
    """
    Get Alembic configuration.
    """
    config_path = os.path.join(os.path.dirname(__file__), 'alembic.ini')
    config = Config(config_path)
    raw_url = (
        f"postgresql+psycopg2://{get_engine().url.username}:"
        f"{get_engine().url.password}@{get_engine().url.host}/fm"
    )
    config.set_main_option('sqlalchemy.url', raw_url)

    if connection is not None:
        config.attributes['connection'] = connection

    return config
