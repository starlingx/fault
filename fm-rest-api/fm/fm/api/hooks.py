#
# Copyright (c) 2018-2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import re
import time
from six.moves.urllib.parse import urlparse
import webob
from pecan import hooks
from oslo_config import cfg
from oslo_log import log
from oslo_serialization import jsonutils
from oslo_utils import uuidutils
from webob import exc

from fm.common import context
from fm.db import api as dbapi
from fm.common.i18n import _

CONF = cfg.CONF

LOG = log.getLogger(__name__)

audit_log_name = "{}.{}".format(__name__, "auditor")
auditLOG = log.getLogger(audit_log_name)


def generate_request_id():
    return 'req-%s' % uuidutils.generate_uuid()


class ContextHook(hooks.PecanHook):
    """Configures a request context and attaches it to the request.

    The following HTTP request headers are used:

    X-User-Name:
        Used for context.user_name.

    X-User-Id:
        Used for context.user_id.

    X-Project-Name:
        Used for context.project.

    X-Project-Id:
        Used for context.project_id.

    X-Auth-Token:
        Used for context.auth_token.# Copyright (c) 2013-2014 Wind River Systems, Inc.

    X-Roles:
        Used for context.roles.
    """

    def before(self, state):
        headers = state.request.headers
        environ = state.request.environ
        user_name = headers.get('X-User-Name')
        user_id = headers.get('X-User-Id')
        project_name = headers.get('X-Project-Name')
        project_id = headers.get('X-Project-Id')
        domain_id = headers.get('X-User-Domain-Id')
        domain_name = headers.get('X-User-Domain-Name')
        auth_token = headers.get('X-Auth-Token')
        roles = headers.get('X-Roles', '').split(',')
        catalog_header = headers.get('X-Service-Catalog')
        service_catalog = None
        if catalog_header:
            try:
                service_catalog = jsonutils.loads(catalog_header)
            except ValueError:
                raise webob.exc.HTTPInternalServerError(
                    _('Invalid service catalog json.'))

        auth_token_info = environ.get('keystone.token_info')
        auth_url = CONF.keystone_authtoken.auth_uri

        state.request.context = context.make_context(
            auth_token=auth_token,
            auth_url=auth_url,
            auth_token_info=auth_token_info,
            user_name=user_name,
            user_id=user_id,
            project_name=project_name,
            project_id=project_id,
            domain_id=domain_id,
            domain_name=domain_name,
            roles=roles,
            service_catalog=service_catalog
        )


class DBHook(hooks.PecanHook):
    """Attach the dbapi object to the request so controllers can get to it."""

    def before(self, state):
        state.request.dbapi = dbapi.get_instance()


class AuditLogging(hooks.PecanHook):
    """
        Performs audit logging of all Fault Manager
        ["POST", "PUT", "PATCH", "DELETE"] REST requests.
    """

    def __init__(self):
        self.log_methods = ["POST", "PUT", "PATCH", "DELETE"]

    def before(self, state):
        state.request.start_time = time.time()

    def __after(self, state):

        method = state.request.method
        if method not in self.log_methods:
            return

        now = time.time()
        try:
            elapsed = now - state.request.start_time
        except AttributeError:
            LOG.info("Start time is not in request, setting it to 0.")
            elapsed = 0

        environ = state.request.environ
        server_protocol = environ["SERVER_PROTOCOL"]

        response_content_length = state.response.content_length

        user_id = state.request.headers.get('X-User-Id')
        user_name = state.request.headers.get('X-User', user_id)
        tenant_id = state.request.headers.get('X-Tenant-Id')
        tenant = state.request.headers.get('X-Tenant', tenant_id)
        domain_name = state.request.headers.get('X-User-Domain-Name')
        try:
            request_id = state.request.context.request_id
        except AttributeError:
            LOG.info("Request id is not in request, setting it to an "
                     "auto generated id.")
            request_id = generate_request_id()

        url_path = urlparse(state.request.path_qs).path

        def json_post_data(rest_state):
            if 'form-data' in rest_state.request.headers.get('Content-Type'):
                return " POST: {}".format(rest_state.request.params)
            try:
                if not hasattr(rest_state.request, 'json'):
                    return ""
            except Exception:
                return ""
            return " POST: {}".format(rest_state.request.json)

        # Filter password from log
        filtered_json = re.sub(r'{[^{}]*(passwd_hash|community|password)[^{}]*},*',
                               '',
                               json_post_data(state))

        log_data = \
            "{} \"{} {} {}\" status: {} len: {} time: {}{} host:{}" \
            " agent:{} user: {} tenant: {} domain: {}".format(
                state.request.remote_addr,
                state.request.method,
                url_path,
                server_protocol,
                state.response.status_int,
                response_content_length,
                elapsed,
                filtered_json,
                state.request.host,
                state.request.user_agent,
                user_name,
                tenant,
                domain_name)

        # The following ctx object will be output in the logger as
        # something like this:
        # [req-088ed3b6-a2c9-483e-b2ad-f1b2d03e06e6
        #  3d76d3c1376744e8ad9916a6c3be3e5f
        #  ca53e70c76d847fd860693f8eb301546]
        # When the ctx is defined, the formatter (defined in common/log.py) requires that keys
        # request_id, user, tenant be defined within the ctx
        ctx = {'request_id': request_id,
               'user': user_id,
               'tenant': tenant_id}

        auditLOG.info("{}".format(log_data), context=ctx)

    def after(self, state):
        try:
            self.__after(state)
        except Exception:
            # Logging and then swallowing exception to ensure
            # rest service does not fail even if audit logging fails
            auditLOG.exception("Exception in AuditLogging on event 'after'")

    def on_error(self, state, e):
        auditLOG.exception("Exception in AuditLogging passed to event 'on_error': " + str(e))


class AccessPolicyHook(hooks.PecanHook):
    """Verify that the user has the needed privilege to execute the action."""
    def before(self, state):
        is_public_api = state.request.environ.get('is_public_api', False)
        if not is_public_api:
            controller = state.controller.__self__
            if hasattr(controller, 'enforce_policy'):
                try:
                    controller_method = state.controller.__name__
                    controller.enforce_policy(controller_method, state.request)
                except Exception:
                    raise exc.HTTPForbidden()
            else:
                raise exc.HTTPForbidden()
