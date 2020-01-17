# Copyright 2020 Intel Corporation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""Base classes for API tests."""

from oslo_config import cfg
import pecan
import pecan.testing

from fm.tests import base
from fm.common import context as fm_context


PATH_PREFIX = '/v1'


class FunctionalTest(base.TestCase):
    """Used for functional tests of Pecan controllers where you need to
    test your literal application and its integration with the
    framework.
    """

    SOURCE_DATA = {'test_source': {'somekey': '666'}}

    def setUp(self):
        super(FunctionalTest, self).setUp()
        self.context = fm_context.RequestContext(is_admin=True)
        self.app = self._make_app()

    def _make_app(self):
        cfg.CONF.set_override("debug", True)

        self.config = {
            'app': {
                'root': 'fm.api.controllers.root.RootController',
                'modules': ['fm.api'],
                'acl_public_routes': ['/', '/v1'],
            },
        }

        return pecan.testing.load_test_app(self.config)

    def tearDown(self):
        super(FunctionalTest, self).tearDown()
        pecan.set_config({}, overwrite=True)

    def get_json(self, path, expect_errors=False, headers=None,
                 extra_environ=None, q=[], path_prefix=PATH_PREFIX, **params):
        full_path = path_prefix + path
        query_params = {'q.field': [],
                        'q.value': [],
                        'q.op': [],
                        }
        for query in q:
            for name in ['field', 'op', 'value']:
                query_params['q.%s' % name].append(query.get(name, ''))
        all_params = {}
        all_params.update(params)
        if q:
            all_params.update(query_params)
        response = self.app.get(full_path,
                                params=all_params,
                                headers=headers,
                                extra_environ=extra_environ,
                                expect_errors=expect_errors)
        if not expect_errors:
            response = response.json
        return response
