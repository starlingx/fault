#
# Copyright (c) 2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#   under the License.

"""Database setup and migration commands."""

import os
from oslo_config import cfg
from oslo_db import options

from stevedore import driver
from fm.db.sqlalchemy import api as db_api

options.set_defaults(cfg.CONF)


_IMPL = None

MIGRATE_REPO_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'sqlalchemy',
    'migrations',
)


def get_backend():
    global _IMPL
    if not _IMPL:
        _IMPL = driver.DriverManager("fm.database.migration_backend",
                                     cfg.CONF.database.backend).driver
    return _IMPL


def db_sync(version=None, engine=None):
    """Migrate the database to `version` or the most recent version."""

    if engine is None:
        engine = db_api.get_engine()

    from fm.db.sqlalchemy import migration as alembic_migration
    return alembic_migration.db_sync(version=version)


def upgrade(version=None):
    """Migrate the database to `version` or the most recent version."""
    return get_backend().upgrade(version)


def version():
    return get_backend().version()


def create_schema():
    return get_backend().create_schema()
