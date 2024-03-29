#
# Copyright (c) 2018-2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from oslo_utils import importutils
from keystoneauth1 import loading

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
               **ignored_kwargs):
    """Get an authenticated client, based on the credentials."""
    kwargs = {}
    interface = endpoint_type or 'publicURL'
    endpoint = endpoint or fm_url
    if auth_token and endpoint:
        kwargs.update({
            'token': auth_token,
        })
        if timeout:
            kwargs.update({
                'timeout': timeout,
            })
    elif auth_url:
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
