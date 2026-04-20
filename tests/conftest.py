#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
# pylint: disable=redefined-outer-name
"""Shared test fixtures for fault project tests."""

import os
import sys
import pytest


@pytest.fixture(autouse=True)
def project_root():
    """Return the absolute path to the project root.

    :returns: str -- path to the fault project root
    """
    return os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(autouse=True)
def setup_sys_path(project_root):
    """Add source directories to sys.path.

    :param project_root: path to the project root
    :returns: None
    """
    paths = [
        os.path.join(
            project_root, 'fm-api', 'source'),
        os.path.join(
            project_root, 'fm-common', 'sources'),
        os.path.join(
            project_root, 'fm-doc', 'fm_doc'),
        os.path.join(
            project_root,
            'python-fmclient', 'fmclient'),
    ]
    for path in paths:
        if path not in sys.path:
            sys.path.insert(0, path)
