#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for fm_log and fm_doc modules."""
# pylint: disable=protected-access,unused-argument

import os
import unittest
from unittest import mock


class TestFmLog(unittest.TestCase):
    """Test fm_log module."""

    def test_get_logger_creates_logger(self):
        """Test get_logger creates a new logger."""
        import fm_log
        logger = fm_log.get_logger('test_logger_1')
        self.assertIsNotNone(logger)

    def test_get_logger_returns_same(self):
        """Test get_logger returns same logger for same name."""
        import fm_log
        logger1 = fm_log.get_logger('test_logger_2')
        logger2 = fm_log.get_logger('test_logger_2')
        self.assertIs(logger1, logger2)

    def test_get_logger_different_names(self):
        """Test get_logger returns different
loggers for different names."""
        import fm_log
        logger1 = fm_log.get_logger('test_a')
        logger2 = fm_log.get_logger('test_b')
        self.assertIsNot(logger1, logger2)

    @mock.patch.dict(os.environ, {'RUNNING_IN_CONTAINER': 'true'})
    def test_setup_logger_container(self):
        """Test setup_logger in container mode uses StreamHandler."""
        import fm_log
        import logging
        logger = logging.getLogger('container_test')
        fm_log.setup_logger(logger)
        has_stream = any(
            isinstance(h, logging.StreamHandler)
            for h in logger.handlers
        )
        self.assertTrue(has_stream)

    def test_setup_logger_sets_level(self):
        """Test setup_logger sets INFO level."""
        import fm_log
        import logging
        logger = logging.getLogger('level_test')
        fm_log.setup_logger(logger)
        self.assertEqual(logger.level, logging.INFO)


class TestFmClientExc(unittest.TestCase):
    """Test fmclient exc module."""

    def test_base_exception_message(self):
        """Test BaseException with message."""
        from fmclient.exc import BaseException as FmBaseException
        exc = FmBaseException("test error")
        self.assertEqual(str(exc), "test error")

    def test_base_exception_no_message(self):
        """Test BaseException without message."""
        from fmclient.exc import BaseException as FmBaseException
        exc = FmBaseException()
        result = str(exc).lower()
        has_expected = ("none" in result or "error" in result)
        self.assertTrue(has_expected)

    def test_command_error(self):
        """Test CommandError."""
        from fmclient.exc import CommandError
        exc = CommandError("bad command")
        self.assertEqual(str(exc), "bad command")

    def test_invalid_endpoint(self):
        """Test InvalidEndpoint."""
        from fmclient.exc import InvalidEndpoint
        exc = InvalidEndpoint("bad endpoint")
        self.assertEqual(str(exc), "bad endpoint")

    def test_communication_error(self):
        """Test CommunicationError."""
        from fmclient.exc import CommunicationError
        exc = CommunicationError("conn failed")
        self.assertEqual(str(exc), "conn failed")

    def test_http_exception_code(self):
        """Test HTTPException has code N/A."""
        from fmclient.exc import HTTPException
        exc = HTTPException("details")
        self.assertEqual(exc.code, 'N/A')
        self.assertIn("details", str(exc))

    def test_http_multiple_choices(self):
        """Test HTTPMultipleChoices."""
        from fmclient.exc import HTTPMultipleChoices
        exc = HTTPMultipleChoices()
        self.assertEqual(exc.code, 300)
        self.assertIn("300", str(exc))

    def test_unauthorized(self):
        """Test Unauthorized."""
        from fmclient.exc import Unauthorized
        exc = Unauthorized()
        self.assertEqual(exc.code, 401)

    def test_not_found(self):
        """Test NotFound."""
        from fmclient.exc import NotFound
        exc = NotFound()
        self.assertEqual(exc.code, 404)

    def test_http_not_found(self):
        """Test HTTPNotFound inherits from NotFound."""
        from fmclient.exc import HTTPNotFound, NotFound
        exc = HTTPNotFound()
        self.assertIsInstance(exc, NotFound)

    def test_http_method_not_allowed(self):
        """Test HTTPMethodNotAllowed."""
        from fmclient.exc import HTTPMethodNotAllowed
        exc = HTTPMethodNotAllowed()
        self.assertEqual(exc.code, 405)

    def test_http_internal_server_error(self):
        """Test HTTPInternalServerError."""
        from fmclient.exc import HTTPInternalServerError
        exc = HTTPInternalServerError()
        self.assertEqual(exc.code, 500)

    def test_http_not_implemented(self):
        """Test HTTPNotImplemented."""
        from fmclient.exc import HTTPNotImplemented
        exc = HTTPNotImplemented()
        self.assertEqual(exc.code, 501)

    def test_http_bad_gateway(self):
        """Test HTTPBadGateway."""
        from fmclient.exc import HTTPBadGateway
        exc = HTTPBadGateway()
        self.assertEqual(exc.code, 502)

    def test_auth_system(self):
        """Test AuthSystem."""
        from fmclient.exc import AuthSystem
        exc = AuthSystem("auth failed")
        self.assertEqual(str(exc), "auth failed")

    def test_endpoint_exception(self):
        """Test EndpointException."""
        from fmclient.exc import EndpointException
        exc = EndpointException("endpoint error")
        self.assertEqual(str(exc), "endpoint error")

    def test_http_unauthorized(self):
        """Test HTTPUnauthorized inherits from Unauthorized."""
        from fmclient.exc import HTTPUnauthorized, Unauthorized
        exc = HTTPUnauthorized()
        self.assertIsInstance(exc, Unauthorized)


class TestProjectStructure(unittest.TestCase):
    """Test project file structure validation."""

    def setUp(self):
        """Set project root."""
        self.root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def test_tox_ini_exists(self):
        """Verify tox.ini exists."""
        self.assertTrue(os.path.isfile(
            os.path.join(self.root, 'tox.ini')))

    def test_zuul_yaml_exists(self):
        """Verify .zuul.yaml exists."""
        self.assertTrue(os.path.isfile(
            os.path.join(self.root, '.zuul.yaml')))

    def test_requirements_exists(self):
        """Verify requirements.txt exists."""
        self.assertTrue(os.path.isfile(
            os.path.join(self.root, 'requirements.txt')))

    def test_fm_api_source_exists(self):
        """Verify fm-api source directory exists."""
        self.assertTrue(os.path.isdir(
            os.path.join(self.root, 'fm-api', 'source', 'fm_api')))

    def test_fm_common_sources_exists(self):
        """Verify fm-common sources directory exists."""
        self.assertTrue(os.path.isdir(
            os.path.join(self.root, 'fm-common', 'sources')))

    def test_fm_rest_api_exists(self):
        """Verify fm-rest-api directory exists."""
        self.assertTrue(os.path.isdir(
            os.path.join(self.root, 'fm-rest-api', 'fm', 'fm')))

    def test_python_fmclient_exists(self):
        """Verify python-fmclient directory exists."""
        self.assertTrue(os.path.isdir(
            os.path.join(self.root, 'python-fmclient', 'fmclient',
                         'fmclient')))

    def test_fm_doc_exists(self):
        """Verify fm-doc directory exists."""
        self.assertTrue(os.path.isdir(
            os.path.join(self.root, 'fm-doc', 'fm_doc')))

    def test_events_yaml_exists(self):
        """Verify events.yaml exists."""
        self.assertTrue(os.path.isfile(
            os.path.join(self.root, 'fm-doc', 'fm_doc', 'events.yaml')))

    def test_license_exists(self):
        """Verify LICENSE file exists."""
        self.assertTrue(os.path.isfile(
            os.path.join(self.root, 'LICENSE')))

    def test_readme_exists(self):
        """Verify README.rst exists."""
        self.assertTrue(os.path.isfile(
            os.path.join(self.root, 'README.rst')))

    def test_pylint_rc_exists(self):
        """Verify pylint.rc exists."""
        self.assertTrue(os.path.isfile(
            os.path.join(self.root, 'pylint.rc')))

    def test_cpp_sources_exist(self):
        """Verify C++ source files exist in fm-common."""
        sources_dir = os.path.join(self.root, 'fm-common', 'sources')
        cpp_files = [f for f in os.listdir(sources_dir)
                     if f.endswith('.cpp')]
        self.assertGreater(len(cpp_files), 0)

    def test_header_files_exist(self):
        """Verify header files exist in fm-common."""
        sources_dir = os.path.join(self.root, 'fm-common', 'sources')
        h_files = [f for f in os.listdir(sources_dir)
                   if f.endswith('.h')]
        self.assertGreater(len(h_files), 0)

    def test_yaml_files_valid(self):
        """Verify YAML files are parseable (skip encrypted tags)."""
        import yaml

        class SafeLoaderIgnoreUnknown(yaml.SafeLoader):
            """SafeLoader that ignores unknown tags."""

        SafeLoaderIgnoreUnknown.add_multi_constructor(
            '', lambda loader, suffix, node: None)

        yaml_path = os.path.join(self.root, '.zuul.yaml')
        with open(yaml_path, 'r') as f:
            data = yaml.load(f, Loader=SafeLoaderIgnoreUnknown)
        self.assertIsNotNone(data)

    def test_gitignore_exists(self):
        """Verify .gitignore exists."""
        self.assertTrue(os.path.isfile(
            os.path.join(self.root, '.gitignore')))


if __name__ == '__main__':
    unittest.main()
