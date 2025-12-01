#
# Copyright (c) 2018-2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import six.moves.urllib.parse as urlparse

from oslo_utils import importutils
from keystoneauth1 import loading
from platform_util.oidc import oidc_utils

from fmclient.common.i18n import _
from fmclient import exc


SERVICE_TYPE = 'faultmanagement'


def get_client(version, endpoint=None, session=None, auth_token=None,
               fm_url=None, username=None, password=None, auth_url=None,
               project_id=None, project_name=None,
               region_name=None, timeout=None,
               user_domain_id=None, user_domain_name=None,
               project_domain_id=None, project_domain_name=None,
               service_type=SERVICE_TYPE, endpoint_type=None, insecure=None,
               stx_auth_type='keystone',
               **ignored_kwargs):
    """Get an authenticated client, based on the credentials."""
    kwargs = {}
    interface = endpoint_type or 'publicURL'
    endpoint = endpoint or fm_url
    if auth_token and endpoint and stx_auth_type == 'keystone':
        kwargs.update({
            'token': auth_token,
        })
        if timeout:
            kwargs.update({
                'timeout': timeout,
            })
    elif auth_url and stx_auth_type == 'keystone':
        auth_kwargs = {}
        auth_type = 'password'
        auth_kwargs.update({
            'auth_url': auth_url,
            'project_id': project_id,
            'project_name': project_name,
            'user_domain_id': user_domain_id,
            'user_domain_name': user_domain_name,
            'project_domain_id': project_domain_id,
            'project_domain_name': project_domain_name,
        })
        if username and password:
            auth_kwargs.update({
                'username': username,
                'password': password
            })
        elif auth_token:
            auth_type = 'token'
            auth_kwargs.update({
                'token': auth_token,
            })

        # Create new session only if it was not passed in
        if not session:
            loader = loading.get_plugin_loader(auth_type)
            auth_plugin = loader.load_from_options(**auth_kwargs)
            session = loading.session.Session().load_from_options(
                auth=auth_plugin, timeout=timeout, insecure=insecure)

    exception_msg = _('Must provide Keystone credentials or user-defined '
                      'endpoint and token')
    if (stx_auth_type == 'oidc' and auth_url is not None and
       username is not None):
        # build endpoint
        endpoint_protocol = 'https://'
        if interface.lower() == 'internalurl':
            endpoint_protocol = 'http://'
        endpoint_ipaddress_parsed = urlparse.urlparse(auth_url)
        endpoint = endpoint_protocol + endpoint_ipaddress_parsed.hostname
        if endpoint_ipaddress_parsed.port is not None:
            endpoint = endpoint + ':18002'

        # get oidc token from kubeconfig
        oidc_token = oidc_utils.get_oidc_token(username)
        if oidc_token is None:
            raise exc.AuthSystem('Unable to get OIDC token from kubeconfig')
        kwargs['oidc_token'] = oidc_token
        kwargs['stx_auth_type'] = stx_auth_type

    if not endpoint:
        if session:
            try:
                endpoint = session.get_endpoint(
                    service_type=service_type,
                    interface=interface,
                    region_name=region_name
                )
            except Exception as e:
                raise exc.AuthSystem(
                    _('%(message)s, error was: %(error)s') %
                    {'message': exception_msg, 'error': e})
        else:
            # Neither session, nor valid auth parameters provided
            raise exc.AuthSystem(exception_msg)

    kwargs['endpoint_override'] = endpoint
    kwargs['service_type'] = service_type
    kwargs['interface'] = interface
    kwargs['version'] = version
    kwargs['insecure'] = insecure

    fm_module = importutils.import_versioned_module('fmclient',
                                                    version, 'client')
    client_class = getattr(fm_module, 'Client')
    return client_class(endpoint, session=session, **kwargs)
