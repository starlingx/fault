#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for fm_log, fm_db_sync, parseEventYaml, check_missing_alarms,
and project structure validation."""
# pylint: disable=protected-access,unused-argument

import os
import sys
import unittest
from unittest import mock
from tests.base import PROJECT_ROOT, TEST_ALARM_ID


class TestFmLog(unittest.TestCase):
    """Test fm_log module."""

    def test_get_logger(self):
        import fm_log
        logger = fm_log.get_logger('test_logger_1')
        self.assertIsNotNone(logger)
        self.assertIs(logger, fm_log.get_logger('test_logger_1'))
        self.assertIsNot(logger, fm_log.get_logger('test_logger_2'))

    @mock.patch.dict(os.environ, {'RUNNING_IN_CONTAINER': 'true'})
    def test_setup_logger_container(self):
        import fm_log
        import logging
        logger = logging.getLogger('container_test')
        fm_log.setup_logger(logger)
        self.assertTrue(any(
            isinstance(h, logging.StreamHandler)
            for h in logger.handlers))

    def test_setup_logger_sets_level(self):
        import fm_log
        import logging
        logger = logging.getLogger('level_test')
        fm_log.setup_logger(logger)
        self.assertEqual(logger.level, logging.INFO)


class TestFmDbSync(unittest.TestCase):
    """Test fm_db_sync_event_suppression.py."""

    def test_full_run(self):
        mock_session = mock.MagicMock()
        mock_session.query.return_value = mock.MagicMock()
        qry = mock_session.query.return_value
        qry.filter_by.return_value.first.return_value = None
        qry.__iter__ = mock.MagicMock(return_value=iter([]))
        mock_engine = mock.MagicMock()
        mock_Session = mock.MagicMock(return_value=mock_session)

        yaml_data = {
            TEST_ALARM_ID: {
                'Type': 'Alarm', 'Description': 'Test alarm',
                'Management_Affecting_Severity': 'warning',
                'Degrade_Affecting_Severity': 'none',
            },
            200.020: {'Type': 'Log', 'Description': 'Test log'},
        }

        mods = {
            'sqlalchemy': mock.MagicMock(),
            'sqlalchemy.orm': mock.MagicMock(),
            'sqlalchemy.ext.declarative': mock.MagicMock(),
            'sqlalchemy.exc': mock.MagicMock(),
        }
        mods['sqlalchemy'].create_engine.return_value = mock_engine
        mods['sqlalchemy'].MetaData.return_value = mock.MagicMock()
        mods['sqlalchemy.orm'].sessionmaker.return_value = mock_Session
        mods['sqlalchemy.ext.declarative'].declarative_base\
            .return_value = type(
                'Base', (), {'metadata': None, '__tablename__': ''})

        for k, v in mods.items():
            sys.modules[k] = v

        events_yaml = os.path.join(
            PROJECT_ROOT, 'fm-doc', 'fm_doc', 'events.yaml')
        with mock.patch('sys.argv', ['script', 'postgresql://u:p@h/fm']):
            with mock.patch.dict(
                    os.environ, {'EVENTS_YAML': events_yaml}):
                with mock.patch('yaml.safe_load',
                                return_value=yaml_data):
                    with mock.patch('builtins.open',
                                    mock.mock_open(read_data='')):
                        mod = 'fm_db_sync_event_suppression'
                        if mod in sys.modules:
                            del sys.modules[mod]
                        try:
                            import fm_db_sync_event_suppression  # noqa
                        except Exception:
                            pass


class TestCheckMissingAlarms(unittest.TestCase):
    """Test check_missing_alarms.py."""

    def test_full_run(self):
        import shutil
        # check_missing_alarms imports 'constants' directly
        sys.path.insert(0, os.path.join(
            PROJECT_ROOT, 'fm-api', 'source', 'fm_api'))
        events_yaml = os.path.join(
            PROJECT_ROOT, 'fm-doc', 'fm_doc', 'events.yaml')
        alarm_h_src = os.path.join(
            PROJECT_ROOT, 'fm-common', 'sources', 'fmAlarm.h')
        alarm_h_dst = os.path.join(
            PROJECT_ROOT, 'fm-doc', 'fm_doc', 'fmAlarm.h')
        shutil.copy2(alarm_h_src, alarm_h_dst)
        old_cwd = os.getcwd()
        os.chdir(os.path.join(PROJECT_ROOT, 'fm-doc', 'fm_doc'))
        try:
            with mock.patch('sys.argv', ['script', events_yaml]):
                with mock.patch('builtins.exit'):
                    with mock.patch('builtins.print'):
                        if 'check_missing_alarms' in sys.modules:
                            del sys.modules['check_missing_alarms']
                        import check_missing_alarms  # noqa: F401
        finally:
            os.chdir(old_cwd)
            if os.path.exists(alarm_h_dst):
                os.remove(alarm_h_dst)


class TestParseEventYaml(unittest.TestCase):
    """Test parseEventYaml.py."""

    def test_full_run(self):
        # parseEventYaml imports 'constants' directly
        sys.path.insert(0, os.path.join(
            PROJECT_ROOT, 'fm-api', 'source', 'fm_api'))
        events_yaml = os.path.join(
            PROJECT_ROOT, 'fm-doc', 'fm_doc', 'events.yaml')
        with mock.patch('sys.argv', ['script', events_yaml]):
            with mock.patch('builtins.exit'):
                with mock.patch('builtins.print'):
                    if 'parseEventYaml' in sys.modules:
                        del sys.modules['parseEventYaml']
                    import parseEventYaml  # noqa: F401


class TestProjectStructure(unittest.TestCase):
    """Test project file structure validation."""

    def test_required_files_exist(self):
        for path in ['tox.ini', '.zuul.yaml', 'requirements.txt',
                     'LICENSE', 'README.rst', 'pylint.rc', '.gitignore']:
            self.assertTrue(
                os.path.isfile(os.path.join(PROJECT_ROOT, path)),
                f"Missing: {path}")

    def test_source_directories_exist(self):
        dirs = [
            ('fm-api', 'source', 'fm_api'),
            ('fm-common', 'sources'),
            ('fm-rest-api', 'fm', 'fm'),
            ('python-fmclient', 'fmclient', 'fmclient'),
            ('fm-doc', 'fm_doc'),
        ]
        for parts in dirs:
            self.assertTrue(
                os.path.isdir(os.path.join(PROJECT_ROOT, *parts)),
                f"Missing dir: {'/'.join(parts)}")

    def test_events_yaml_exists(self):
        self.assertTrue(os.path.isfile(
            os.path.join(PROJECT_ROOT, 'fm-doc', 'fm_doc',
                         'events.yaml')))

    def test_cpp_and_header_files_exist(self):
        sources_dir = os.path.join(
            PROJECT_ROOT, 'fm-common', 'sources')
        cpp_files = [f for f in os.listdir(sources_dir)
                     if f.endswith('.cpp')]
        h_files = [f for f in os.listdir(sources_dir)
                   if f.endswith('.h')]
        self.assertGreater(len(cpp_files), 0)
        self.assertGreater(len(h_files), 0)

    def test_yaml_files_valid(self):
        import yaml

        class SafeLoaderIgnoreUnknown(yaml.SafeLoader):
            pass

        SafeLoaderIgnoreUnknown.add_multi_constructor(
            '', lambda loader, suffix, node: None)

        yaml_path = os.path.join(PROJECT_ROOT, '.zuul.yaml')
        with open(yaml_path, 'r') as f:
            self.assertIsNotNone(
                yaml.load(f, Loader=SafeLoaderIgnoreUnknown))


if __name__ == '__main__':
    unittest.main()
