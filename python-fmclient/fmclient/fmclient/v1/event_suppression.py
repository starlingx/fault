#
# Copyright (c) 2018 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


import json
from fmclient.common import options
from fmclient.common import base


class EventSuppression(base.Resource):
    def __repr__(self):
        return "<EventSuppression %s>" % self._info


class EventSuppressionManager(base.Manager):
    resource_class = EventSuppression

    @staticmethod
    def _path(iid=None):
        return '/v1/event_suppression/%s' % iid if iid else '/v1/event_suppression'

    def list(self, q=None):
        params = []

        restAPIURL = options.build_url(self._path(), q, params)

        return self._list(restAPIURL, 'event_suppression')

    def get(self, iid):
        try:
            return self._list(self._path(iid))[0]
        except IndexError:
            return None

    def update(self, event_suppression_uuid, patch):
        return self._update(self._path(event_suppression_uuid),
                            data=json.dumps(patch))
