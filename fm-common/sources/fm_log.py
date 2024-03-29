#
# Copyright (c) 2021 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


"""
Logging
"""

import logging
import logging.handlers
import os
import sys

_loggers = {}


def get_logger(name):
    """ Get a logger or create one  """

    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
        setup_logger(_loggers[name])
    return _loggers[name]


def setup_logger(logger):
    """ Setup a logger """

    # Send logs to /var/log/platform.log
    syslog_facility = logging.handlers.SysLogHandler.LOG_LOCAL1

    formatter = logging.Formatter("configassistant[%(process)d] " +
                                  "%(pathname)s:%(lineno)s " +
                                  "%(levelname)8s [%(name)s] %(message)s")

    running_in_container = os.getenv("RUNNING_IN_CONTAINER", "False").strip().lower()
    if running_in_container == "true":
        handler = logging.StreamHandler(stream=sys.stdout)
    else:
        handler = logging.handlers.SysLogHandler(address='/dev/log',
                                                 facility=syslog_facility)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
