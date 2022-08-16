#
# Copyright (c) 2018-2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


import datetime
import json
import pecan
from pecan import rest

import wsme
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan
from oslo_utils._i18n import _
from oslo_log import log

from fm_api import fm_api

from fm.api.controllers.v1 import base
from fm.api.controllers.v1 import collection
from fm.api.controllers.v1 import link
from fm.api.controllers.v1 import types
from fm.api.controllers.v1 import utils as api_utils
from fm.common import exceptions
from fm.common import constants
from fm.common import policy
from fm import objects
from fm.api.policies import alarm as alarm_policy
from fm.api.controllers.v1.query import Query

from fm_api import constants as fm_constants


LOG = log.getLogger(__name__)


class AlarmPatchType(types.JsonPatchType):
    pass


class Alarm(base.APIBase):
    """API representation of an alarm.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of
    an alarm.
    """

    uuid = types.uuid
    "The UUID of the alarm"

    alarm_id = wsme.wsattr(wtypes.text, mandatory=True)
    "structured id for the alarm;   AREA_ID  ID;   300-001"

    alarm_state = wsme.wsattr(wtypes.text, mandatory=True)
    "The state of the alarm"

    entity_type_id = wtypes.text
    "The type of the object raising alarm"

    entity_instance_id = wsme.wsattr(wtypes.text, mandatory=True)
    "The original instance information of the object raising alarm"

    timestamp = datetime.datetime
    "The time in UTC at which the alarm state is last updated"

    severity = wsme.wsattr(wtypes.text, mandatory=True)
    "The severity of the alarm"

    reason_text = wtypes.text
    "The reason why the alarm is raised"

    alarm_type = wsme.wsattr(wtypes.text, mandatory=True)
    "The type of the alarm"

    probable_cause = wsme.wsattr(wtypes.text, mandatory=True)
    "The probable cause of the alarm"

    proposed_repair_action = wtypes.text
    "The action to clear the alarm"

    service_affecting = bool
    "Whether the alarm affects the service"

    suppression = bool
    "'allowed' or 'not-allowed'"

    suppression_status = wtypes.text
    "'suppressed' or 'unsuppressed'"

    mgmt_affecting = wtypes.text
    "Whether the alarm prevents software management actions"

    degrade_affecting = wtypes.text
    "Whether the alarm prevents filesystem resize actions"

    links = [link.Link]
    "A list containing a self link and associated alarm links"

    def __init__(self, **kwargs):
        self.fields = list(objects.alarm.fields.keys())
        for k in self.fields:
            setattr(self, k, kwargs.get(k))

    @classmethod
    def convert_with_links(cls, rpc_ialarm, expand=True):
        if isinstance(rpc_ialarm, tuple):
            alarms = rpc_ialarm[0]
            suppress_status = rpc_ialarm[constants.DB_SUPPRESS_STATUS]
            mgmt_affecting = rpc_ialarm[constants.DB_MGMT_AFFECTING]
            degrade_affecting = rpc_ialarm[constants.DB_DEGRADE_AFFECTING]
        else:
            alarms = rpc_ialarm
            suppress_status = rpc_ialarm.suppression_status
            mgmt_affecting = rpc_ialarm.mgmt_affecting
            degrade_affecting = rpc_ialarm.degrade_affecting

        alarms['service_affecting'] = alarms['service_affecting']
        alarms['suppression'] = alarms['suppression']

        alm = Alarm(**alarms.as_dict())
        if not expand:
            alm.unset_fields_except(['uuid', 'alarm_id', 'entity_instance_id',
                                     'severity', 'timestamp', 'reason_text',
                                     'mgmt_affecting ', 'degrade_affecting'])

        alm.entity_instance_id = \
            api_utils.make_display_id(alm.entity_instance_id, replace=False)

        alm.suppression_status = str(suppress_status)

        alm.mgmt_affecting = str(
            not fm_api.FaultAPIs.alarm_allowed(alm.severity, mgmt_affecting))

        alm.degrade_affecting = str(
            not fm_api.FaultAPIs.alarm_allowed(alm.severity,
                                               degrade_affecting))

        return alm


class AlarmCollection(collection.Collection):
    """API representation of a collection of alarm."""

    alarms = [Alarm]
    "A list containing alarm objects"

    def __init__(self, **kwargs):
        self._type = 'alarms'

    @classmethod
    def convert_with_links(cls, ialm, limit, url=None,
                           expand=False, **kwargs):
        # filter masked alarms
        ialms = []
        for a in ialm:
            if isinstance(a, tuple):
                ialm_instance = a[0]
            else:
                ialm_instance = a
            if str(ialm_instance['masked']) != 'True':
                ialms.append(a)

        collection = AlarmCollection()
        collection.alarms = [Alarm.convert_with_links(ch, expand)
                             for ch in ialms]
        # url = url or None
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection


LOCK_NAME = 'AlarmController'


class AlarmSummary(base.APIBase):
    """API representation of an alarm summary object."""

    critical = wsme.wsattr(int, mandatory=True)
    "The count of critical alarms"

    major = wsme.wsattr(int, mandatory=True)
    "The count of major alarms"

    minor = wsme.wsattr(int, mandatory=True)
    "The count of minor alarms"

    warnings = wsme.wsattr(int, mandatory=True)
    "The count of warnings"

    status = wsme.wsattr(wtypes.text, mandatory=True)
    "The status of the system"

    @classmethod
    def convert_with_links(cls, ialm_sum):
        summary = AlarmSummary()
        summary.critical = ialm_sum[fm_constants.FM_ALARM_SEVERITY_CRITICAL]
        summary.major = ialm_sum[fm_constants.FM_ALARM_SEVERITY_MAJOR]
        summary.minor = ialm_sum[fm_constants.FM_ALARM_SEVERITY_MINOR]
        summary.warnings = ialm_sum[fm_constants.FM_ALARM_SEVERITY_WARNING]
        summary.status = ialm_sum['status']
        return summary


class AlarmController(rest.RestController):
    """REST controller for alarm."""

    _custom_actions = {
        'detail': ['GET'],
        'summary': ['GET'],
    }

    def _get_alarm_summary(self, include_suppress):
        kwargs = {}
        kwargs["include_suppress"] = include_suppress
        ialm = pecan.request.dbapi.alarm_get_all(**kwargs)
        ialm_counts = {fm_constants.FM_ALARM_SEVERITY_CRITICAL: 0,
                       fm_constants.FM_ALARM_SEVERITY_MAJOR: 0,
                       fm_constants.FM_ALARM_SEVERITY_MINOR: 0,
                       fm_constants.FM_ALARM_SEVERITY_WARNING: 0}
        # filter masked alarms and sum by severity
        for a in ialm:
            ialm_instance = a[0]
            if str(ialm_instance['masked']) != 'True':
                if ialm_instance['severity'] in ialm_counts:
                    ialm_counts[ialm_instance['severity']] += 1

        # Generate the status
        status = fm_constants.FM_ALARM_OK_STATUS
        if (ialm_counts[fm_constants.FM_ALARM_SEVERITY_MAJOR] > 0) or \
                (ialm_counts[fm_constants.FM_ALARM_SEVERITY_MINOR] > 0):
            status = fm_constants.FM_ALARM_DEGRADED_STATUS
        if ialm_counts[fm_constants.FM_ALARM_SEVERITY_CRITICAL] > 0:
            status = fm_constants.FM_ALARM_CRITICAL_STATUS
        ialm_counts['status'] = status

        return AlarmSummary.convert_with_links(ialm_counts)

    def _get_alarm_collection(self, marker, limit, sort_key, sort_dir,
                              expand=False, resource_url=None,
                              q=None, include_suppress=False):
        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)
        if isinstance(sort_key, str) and ',' in sort_key:
            sort_key = sort_key.split(',')

        kwargs = {}
        if q is not None:
            for i in q:
                if i.op == 'eq':
                    kwargs[i.field] = i.value

        kwargs["include_suppress"] = include_suppress

        if marker:

            marker_obj = objects.alarm.get_by_uuid(pecan.request.context,
                                                   marker)
            ialm = pecan.request.dbapi.alarm_get_list(
                limit, marker_obj,
                sort_key=sort_key,
                sort_dir=sort_dir,
                include_suppress=include_suppress)
        else:
            kwargs['limit'] = limit
            ialm = pecan.request.dbapi.alarm_get_all(**kwargs)

        return AlarmCollection.convert_with_links(ialm, limit,
                                                  url=resource_url,
                                                  expand=expand,
                                                  sort_key=sort_key,
                                                  sort_dir=sort_dir)

    def _get_event_log_data(self, alarm_dict):
        """ Retrive a dictionary to create an event_log object

        :param alarm_dict: Dictionary obtained from an alarm object.
        """
        event_log_dict = {}
        for key in list(alarm_dict.keys()):
            if key == 'alarm_id':
                event_log_dict['event_log_id'] = alarm_dict[key]
            elif key == 'alarm_state':
                event_log_dict['state'] = alarm_dict[key]
            elif key == 'alarm_type':
                event_log_dict['event_log_type'] = alarm_dict[key]
            elif (
                key == 'inhibit_alarms' or key == 'inhibit_alarms' or
                key == 'updated_at' or key == 'updated_at' or key == 'masked'
            ):
                continue
            else:
                event_log_dict[key] = alarm_dict[key]
        return event_log_dict

    @wsme_pecan.wsexpose(AlarmCollection, [Query],
                         types.uuid, int, wtypes.text, wtypes.text, bool, bool)
    def get_all(self, q=[], marker=None, limit=None, sort_key='id',
                sort_dir='asc', include_suppress=False, expand=False):
        """Retrieve a list of alarm.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        :param include_suppress: filter on suppressed alarms. Default: False
        :param expand: filter for getting all the data of the alarm.
               Default: False
        """
        return self._get_alarm_collection(marker, limit, sort_key,
                                          sort_dir, expand=expand, q=q,
                                          include_suppress=include_suppress)

    @wsme_pecan.wsexpose(AlarmCollection, types.uuid, int,
                         wtypes.text, wtypes.text)
    def detail(self, marker=None, limit=None, sort_key='id', sort_dir='asc'):
        """Retrieve a list of alarm with detail.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        # /detail should only work agaist collections
        parent = pecan.request.path.split('/')[:-1][-1]
        if parent != "alarm":
            raise exceptions.HTTPNotFound

        expand = True
        resource_url = '/'.join(['alarm', 'detail'])
        return self._get_alarm_collection(marker, limit, sort_key, sort_dir,
                                          expand, resource_url)

    @wsme_pecan.wsexpose(Alarm, wtypes.text)
    def get_one(self, id):
        """Retrieve information about the given alarm.

        :param id: UUID of an alarm.
        """
        rpc_ialarm = objects.alarm.get_by_uuid(
            pecan.request.context, id)
        if str(rpc_ialarm['masked']) == 'True':
            raise exceptions.HTTPNotFound

        return Alarm.convert_with_links(rpc_ialarm)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        """Delete an alarm.

        :param id: uuid of an alarm.
        """
        data = pecan.request.dbapi.alarm_get(id)
        if data is None:
            raise wsme.exc.ClientSideError(_("can not find record to clear!"))
        pecan.request.dbapi.alarm_destroy(id)
        alarm_state = fm_constants.FM_ALARM_STATE_CLEAR
        tmp_dict = data.as_dict()
        self._alarm_save2event_log(tmp_dict, alarm_state, empty_uuid=True)

    @wsme_pecan.wsexpose(AlarmSummary, bool)
    def summary(self, include_suppress=False):
        """Retrieve a summery of alarms.

        :param include_suppress: filter on suppressed alarms. Default: False
        """
        return self._get_alarm_summary(include_suppress)

    def _alarm_save2event_log(self, data_dict, fm_state, empty_uuid=False):
        event_log_data = self._get_event_log_data(data_dict)
        event_log_data['state'] = fm_state
        event_log_data['id'] = None
        if empty_uuid is True:
            event_log_data['uuid'] = None
        if (event_log_data['timestamp'] is None or
                fm_state == fm_constants.FM_ALARM_STATE_CLEAR):
            event_log_data['timestamp'] = datetime.datetime.utcnow()
        event_data = pecan.request.dbapi.event_log_create(event_log_data)
        return event_data

    @wsme_pecan.wsexpose(wtypes.text, body=Alarm)
    def post(self, alarm_data):
        """Create an alarm/event log.
        :param alarm_data: All information required to create an
         alarm or eventlog.
        """

        alarm_data_dict = alarm_data.as_dict()
        alarm_state = alarm_data_dict['alarm_state']
        try:
            if alarm_state == fm_constants.FM_ALARM_STATE_SET:
                data = pecan.request.dbapi.alarm_create(alarm_data_dict)
                tmp_dict = data.as_dict()
                self._alarm_save2event_log(tmp_dict, alarm_state)
            elif (
                alarm_state == fm_constants.FM_ALARM_STATE_LOG or
                alarm_state == fm_constants.FM_ALARM_STATE_MSG
            ):
                data = self._alarm_save2event_log(alarm_data_dict, 'log')
            # This is same action as DELETE Method if para is uuid
            # keep this RESTful for future use to clear/delete alarm with parameters
            # are alarm_id and entity_instance_id
            elif alarm_state == fm_constants.FM_ALARM_STATE_CLEAR:
                clear_uuid = alarm_data_dict['uuid']
                alarm_id = alarm_data_dict['alarm_id']
                entity_instance_id = alarm_data_dict['entity_instance_id']
                if clear_uuid is not None:
                    data = pecan.request.dbapi.alarm_get(clear_uuid)
                    pecan.request.dbapi.alarm_destroy(clear_uuid)
                    tmp_dict = data.as_dict()
                    self._alarm_save2event_log(tmp_dict, alarm_state, empty_uuid=True)
                elif alarm_id is not None and entity_instance_id is not None:
                    data = pecan.request.dbapi.alarm_get_by_ids(alarm_id, entity_instance_id)
                    if data is None:
                        raise wsme.exc.ClientSideError(_("can not find record to clear!"))
                    pecan.request.dbapi.alarm_destroy_by_ids(alarm_id, entity_instance_id)
                    tmp_dict = data.as_dict()
                    self._alarm_save2event_log(tmp_dict, alarm_state, empty_uuid=True)
            else:
                msg = _("The alarm_state %s does not support!")
                raise wsme.exc.ClientSideError(msg % alarm_state)
        except Exception as err:
            return err
        alarm_dict = data.as_dict()
        return json.dumps({"uuid": alarm_dict['uuid']})

    @wsme_pecan.wsexpose(wtypes.text, wtypes.text, body=Alarm)
    def put(self, id, alarm_data):
        """ Update an alarm

        :param id: uuid of an alarm.
        :param alarm_data: Information to be updated
        """

        alarm_data_dict = alarm_data.as_dict()
        try:
            alm = pecan.request.dbapi.alarm_update(id, alarm_data_dict)
        except Exception as err:
            return err
        alarm_dict = alm.as_dict()
        return json.dumps({"uuid": alarm_dict['uuid']})

    def enforce_policy(self, method_name, request):
        """Check policy rules for each action of this controller."""
        context_dict = request.context.to_dict()
        if method_name == "delete":
            policy.authorize(alarm_policy.POLICY_ROOT % "delete", {},
                             context_dict)
        elif method_name in ["detail", "get_all", "get_one", "summary"]:
            policy.authorize(alarm_policy.POLICY_ROOT % "get", {},
                             context_dict)
        elif method_name == "post":
            policy.authorize(alarm_policy.POLICY_ROOT % "create", {},
                             context_dict)
        elif method_name == "put":
            policy.authorize(alarm_policy.POLICY_ROOT % "modify", {},
                             context_dict)
        else:
            raise exceptions.PolicyNotFound()
