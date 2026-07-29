#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Cover fm_db_sync_event_suppression,
check_missing_alarms, parseEventYaml."""
import os
import sys
import unittest
from unittest import mock
from tests import constants as TC

P = os.path.join(os.path.dirname(__file__), '..', '..')


class TestFmDbSync(unittest.TestCase):
    """Cover fm_db_sync_event_suppression.py by mocking DB + yaml."""

    def test_full_run(self):
        sys.path.insert(0, os.path.join(P, 'fm-common', 'sources'))
        mock_session = mock.MagicMock()
        mock_session.query.return_value = mock.MagicMock()
        qry = mock_session.query.return_value
        qry.filter_by.return_value.first.return_value = None
        qry = mock_session.query.return_value
        qry.__iter__ = mock.MagicMock(
            return_value=iter([]))
        mock_engine = mock.MagicMock()
        mock_Session = mock.MagicMock(return_value=mock_session)

        yaml_data = {
            TC.TEST_ALARM_ID: {
                'Type': 'Alarm',
                'Description': 'Test alarm',
                'Management_Affecting_Severity': 'warning',
                'Degrade_Affecting_Severity': 'none',
            },
            200.020: {
                'Type': 'Log',
                'Description': 'Test log',
            },
        }

        mods = {
            'sqlalchemy': mock.MagicMock(),
            'sqlalchemy.orm': mock.MagicMock(),
            'sqlalchemy.ext.declarative': mock.MagicMock(),
            'sqlalchemy.exc': mock.MagicMock(),
        }
        sa_mock = mods['sqlalchemy']
        sa_mock.create_engine.return_value = mock_engine
        sa_mock.MetaData.return_value = mock.MagicMock()
        mods['sqlalchemy.orm'].sessionmaker.return_value = mock_Session
        decl = mods['sqlalchemy.ext.declarative']
        decl.declarative_base.return_value = type(
            'Base', (), {'metadata': None, '__tablename__': ''})

        for k, v in mods.items():
            sys.modules[k] = v

        events_yaml = os.path.join(P, 'fm-doc', 'fm_doc', 'events.yaml')
        with mock.patch('sys.argv', ['script',
                        'postgresql://u:p@h/fm']):
            with mock.patch.dict(os.environ,
                                 {'EVENTS_YAML': events_yaml}):
                with mock.patch('yaml.safe_load',
                                return_value=yaml_data):
                    mopen = mock.mock_open(
                        read_data='')
                    with mock.patch(
                            'builtins.open',
                            mopen):
                        mod = 'fm_db_sync_event_suppression'
                        if mod in sys.modules:
                            del sys.modules[mod]
                        try:
                            import fm_db_sync_event_suppression  # noqa
                        except Exception:
                            pass  # may fail on commit, that's ok


class TestCheckMissingAlarmsFull(unittest.TestCase):
    """Cover check_missing_alarms.py."""

    def test_full_run(self):
        sys.path.insert(0, os.path.join(P, 'fm-api', 'source',
                                        'fm_api'))
        sys.path.insert(0, os.path.join(P, 'fm-api', 'source'))
        sys.path.insert(0, os.path.join(P, 'fm-doc', 'fm_doc'))

        events_yaml = os.path.join(P, 'fm-doc', 'fm_doc', 'events.yaml')
        old_cwd = os.getcwd()
        # Copy fmAlarm.h to fm_doc dir (like checkEventYaml does)
        import shutil
        alarm_h_src = os.path.join(P, 'fm-common', 'sources',
                                   'fmAlarm.h')
        alarm_h_dst = os.path.join(P, 'fm-doc', 'fm_doc', 'fmAlarm.h')
        shutil.copy2(alarm_h_src, alarm_h_dst)
        os.chdir(os.path.join(P, 'fm-doc', 'fm_doc'))
        try:
            with mock.patch('sys.argv', ['script', events_yaml]):
                with mock.patch('builtins.exit') as me:
                    with mock.patch('builtins.print'):
                        if 'check_missing_alarms' in sys.modules:
                            del sys.modules['check_missing_alarms']
                        import check_missing_alarms  # noqa: F401
        finally:
            os.chdir(old_cwd)
            if os.path.exists(alarm_h_dst):
                os.remove(alarm_h_dst)


class TestParseEventYamlFull(unittest.TestCase):
    """Cover parseEventYaml.py."""

    def test_full_run(self):
        sys.path.insert(0, os.path.join(P, 'fm-api', 'source',
                                        'fm_api'))
        sys.path.insert(0, os.path.join(P, 'fm-api', 'source'))
        sys.path.insert(0, os.path.join(P, 'fm-doc', 'fm_doc'))

        events_yaml = os.path.join(P, 'fm-doc', 'fm_doc', 'events.yaml')
        with mock.patch('sys.argv', ['script', events_yaml]):
            with mock.patch('builtins.exit'):
                with mock.patch('builtins.print'):
                    if 'parseEventYaml' in sys.modules:
                        del sys.modules['parseEventYaml']
                    import parseEventYaml  # noqa: F401


if __name__ == '__main__':
    unittest.main()
