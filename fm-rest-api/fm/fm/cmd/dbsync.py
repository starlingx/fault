#
# Copyright (c) 2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


import sys
from oslo_config import cfg
cfg.CONF(sys.argv[1:], project='fm')
from fm.db import migration
CONF = cfg.CONF


def main():
    migration.db_sync()
