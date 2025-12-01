# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# Copyright (c) 2018-2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


import re

from keystonemiddleware import auth_token
from oslo_log import log
from platform_util.oidc import oidc_utils
import webob

from fm.common import exceptions
from fm.common import utils
from fm.common.i18n import _

LOG = log.getLogger(__name__)


class AuthTokenMiddleware(auth_token.AuthProtocol):
    """A wrapper on Keystone auth_token middleware.

    Does not perform verification of authentication tokens
    for public routes in the API.

    """
    def __init__(self, app, conf, public_api_routes=None):
        if public_api_routes is None:
            public_api_routes = []
        route_pattern_tpl = '%s(\.json)?$'

        try:
            self.public_api_routes = [re.compile(route_pattern_tpl % route_tpl)
                                      for route_tpl in public_api_routes]
        except re.error as e:
            msg = _('Cannot compile public API routes: %s') % e

            LOG.error(msg)
            raise exceptions.ConfigInvalid(error_msg=msg)

        self.oidc_token_cache = {}
        self.oidc_auth_params = None

        super(AuthTokenMiddleware, self).__init__(app, conf)

    def __call__(self, env, start_response):
        path = utils.safe_rstrip(env.get('PATH_INFO'), '/')

        # The information whether the API call is being performed against the
        # public API is required for some other components. Saving it to the
        # WSGI environment is reasonable thereby.
        env['is_public_api'] = any([re.match(pattern, path) for pattern in self.public_api_routes])

        if env['is_public_api']:
            return self._app(env, start_response)

        if 'HTTP_OIDC_TOKEN' in env:
            if self.oidc_auth_params is None:
                self.oidc_auth_params = oidc_utils.get_apiserver_oidc_args()
            # if it's still None, then the system isn't configured correctly
            # some or all of the oidc-related params are missing
            if self.oidc_auth_params is None:
                error_response = webob.Response(status=401)
                return error_response(env, start_response)

            try:
                claims = oidc_utils.validate_oidc_token(
                    env['HTTP_OIDC_TOKEN'],
                    self.oidc_token_cache,
                    self.oidc_auth_params['oidc-issuer-url'],
                    self.oidc_auth_params['oidc-client-id'])
                if claims is None:
                    error_response = webob.Response(status=401)
                    return error_response(env, start_response)

                username = oidc_utils.get_username_from_oidc_token(
                    claims,
                    self.oidc_auth_params['oidc-username-claim'])
                roles = oidc_utils.get_keystone_roles_for_oidc_token(
                    claims,
                    self.oidc_auth_params['oidc-username-claim'],
                    self.oidc_auth_params['oidc-groups-claim'])
                env['oidc_token_roles'] = roles
                return self._app(env, start_response)
            except Exception as e:
                error_response = webob.Response(status=401)
                return error_response(env, start_response)

        return super(AuthTokenMiddleware, self).__call__(env, start_response)

    @classmethod
    def factory(cls, global_config, **local_conf):
        public_routes = local_conf.get('acl_public_routes', '')
        public_api_routes = [path.strip() for path in public_routes.split(',')]

        def _factory(app):
            return cls(app, global_config, public_api_routes=public_api_routes)
        return _factory
