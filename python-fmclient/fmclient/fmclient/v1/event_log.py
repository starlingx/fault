#
# Copyright (c) 2018-2019 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


from fmclient.common import options
from fmclient.common import base


class EventLog(base.Resource):
    def __repr__(self):
        return "<EventLog %s>" % self._info


class EventLogManager(base.Manager):
    resource_class = EventLog

    @staticmethod
    def _path(id=None):
        return '/v1/event_log/%s' % id if id else '/v1/event_log'

    def list(self, q=None, limit=None, marker=None, alarms=False, logs=False,
             include_suppress=False, expand=False):
        params = []
        if limit:
            params.append('limit=%s' % str(limit))
        if marker:
            params.append('marker=%s' % str(marker))
        if include_suppress:
            params.append('include_suppress=True')
        if expand:
            params.append('expand=True')
        if alarms is True and logs is False:
            params.append('alarms=True')
        elif alarms is False and logs is True:
            params.append('logs=True')

        restAPIURL = options.build_url(self._path(), q, params)

        return self._list(restAPIURL, 'event_log')

    def get(self, iid):
        try:
            return self._list(self._path(iid))[0]
        except IndexError:
            return None
