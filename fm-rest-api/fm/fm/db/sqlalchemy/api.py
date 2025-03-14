#
# Copyright (c) 2018, 2025 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

"""SQLAlchemy storage backend."""

import functools
import sys
import threading

import eventlet
from oslo_log import log
from oslo_config import cfg
from oslo_utils import uuidutils

from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import enginefacade
from oslo_db.sqlalchemy import utils as db_utils
from oslo_db.sqlalchemy import session as db_session

from sqlalchemy import asc, desc, or_
from sqlalchemy.orm.exc import NoResultFound

from fm.api import config
from fm.common import constants
from fm.common import exceptions
from fm.db import api
from fm.db.sqlalchemy import models
from fm import objects


CONF = cfg.CONF

LOG = log.getLogger(__name__)

_LOCK = threading.Lock()
_FACADE = None

context_manager = enginefacade.transaction_context()
context_manager.configure()


def _create_facade_lazily():
    global _LOCK
    with _LOCK:
        global _FACADE
        if _FACADE is None:
            _FACADE = db_session.EngineFacade(
                CONF.database.connection,
                **dict(CONF.database)
            )
        return _FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)


def get_backend():
    """The backend is this module itself."""
    return Connection()


def _session_for_read():
    _context = eventlet.greenthread.getcurrent()
    return enginefacade.reader.using(_context)


def _session_for_write():
    _context = eventlet.greenthread.getcurrent()
    LOG.debug("_session_for_write CONTEXT=%s" % _context)
    return enginefacade.writer.using(_context)


def _paginate_query(model, limit=None, marker=None, sort_key=None,
                    sort_dir=None, query=None):
    if not query:
        query = model_query(model)

    if not sort_key:
        sort_keys = []
    elif not isinstance(sort_key, list):
        sort_keys = [sort_key]
    else:
        sort_keys = sort_key

    if 'id' not in sort_keys:
        sort_keys.append('id')
    query = db_utils.paginate_query(query, model, limit, sort_keys,
                                    marker=marker, sort_dir=sort_dir)
    return query.all()


def db_session_cleanup(cls):
    """Class decorator that automatically adds session cleanup to all non-special methods."""

    def method_decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            _context = eventlet.greenthread.getcurrent()
            exc_info = (None, None, None)

            try:
                return method(self, *args, **kwargs)
            except Exception:
                exc_info = sys.exc_info()
                raise
            finally:
                if (
                    hasattr(_context, "_db_session_context") and
                    _context._db_session_context is not None
                ):
                    try:
                        _context._db_session_context.__exit__(*exc_info)
                    except Exception as e:
                        LOG.warning(f"Error closing database session: {e}")

                    # Clear the session
                    _context._db_session = None
                    _context._db_session_context = None

        return wrapper

    for attr_name in dir(cls):
        # Skip special methods
        if not attr_name.startswith("__"):
            attr = getattr(cls, attr_name)
            if callable(attr):
                setattr(cls, attr_name, method_decorator(attr))

    return cls


def model_query(model, *args, **kwargs):
    """Query helper for simpler session usage.

    If the session is already provided in the kwargs, use it. Otherwise,
    try to get it from thread context. If it's not there, create a new one.

    :param session: if present, the session to use
    """
    session = kwargs.get('session')
    if not session:
        _context = eventlet.greenthread.getcurrent()
        if hasattr(_context, '_db_session') and _context._db_session is not None:
            session = _context._db_session
        else:
            session_context = _session_for_read()
            session = session_context.__enter__()
            _context._db_session = session
            # Need to store the session context to call __exit__ method later
            _context._db_session_context = session_context

        query = session.query(model, *args)

    return session.query(model, *args)


def add_event_log_filter_by_event_suppression(query, include_suppress):
    """Adds an event_suppression filter to a query.

    Filters results by suppression status

    :param query: Initial query to add filter to.
    :param include_suppress: Value for filtering results by.
    :return: Modified query.
    """
    query = query.outerjoin(models.EventSuppression,
                            models.EventLog.event_log_id == models.EventSuppression.alarm_id)

    query = query.add_columns(models.EventSuppression.suppression_status)

    if include_suppress:
        return query

    return query.filter(or_(models.EventLog.state == 'log',
                            models.EventSuppression.suppression_status ==
                            constants.FM_UNSUPPRESSED))


def add_alarm_filter_by_event_suppression(query, include_suppress):
    """Adds an event_suppression filter to a query.

    Filters results by suppression status

    :param query: Initial query to add filter to.
    :param include_suppress: Value for filtering results by.
    :return: Modified query.
    """
    query = query.join(models.EventSuppression,
                       models.Alarm.alarm_id == models.EventSuppression.alarm_id)

    query = query.add_columns(models.EventSuppression.suppression_status)

    if include_suppress:
        return query

    return query.filter(models.EventSuppression.suppression_status ==
                        constants.FM_UNSUPPRESSED)


def add_alarm_mgmt_affecting_by_event_suppression(query):
    """Adds a mgmt_affecting attribute from event_suppression to query.

    :param query: Initial query.
    :return: Modified query.
    """
    query = query.add_columns(models.EventSuppression.mgmt_affecting)
    return query


def add_alarm_degrade_affecting_by_event_suppression(query):
    """Adds a degrade_affecting attribute from event_suppression to query.

    :param query: Initial query.
    :return: Modified query.
    """
    query = query.add_columns(models.EventSuppression.degrade_affecting)
    return query


@db_session_cleanup
class Connection(api.Connection):
    """SqlAlchemy connection."""

    def __init__(self):
        pass

    def get_session(self, autocommit=True):
        return get_session(autocommit)

    def alarm_create(self, values):
        if not values.get('uuid'):
            values['uuid'] = uuidutils.generate_uuid()
        alarm = models.Alarm()
        alarm.update(values)
        with _session_for_write() as session:
            try:
                session.add(alarm)
                session.flush()
            except db_exc.DBDuplicateEntry:
                raise exceptions.AlarmAlreadyExists(uuid=values['uuid'])
            return alarm

    @objects.objectify(objects.alarm)
    def alarm_get(self, uuid):
        query = model_query(models.Alarm)

        if uuid:
            query = query.filter_by(uuid=uuid)

        query = add_alarm_filter_by_event_suppression(query, include_suppress=True)
        query = add_alarm_mgmt_affecting_by_event_suppression(query)
        query = add_alarm_degrade_affecting_by_event_suppression(query)

        try:
            result = query.one()
        except NoResultFound:
            raise exceptions.AlarmNotFound(alarm=uuid)

        alarm = result[0]
        alarm.suppression_status = result[1]
        alarm.mgmt_affecting = result[2]
        alarm.degrade_affecting = result[3]

        return alarm

    def alarm_get_by_ids(self, alarm_id, entity_instance_id):
        query = model_query(models.Alarm)
        if alarm_id and entity_instance_id:
            query = query.filter_by(alarm_id=alarm_id)
            query = query.filter_by(entity_instance_id=entity_instance_id)

            query = query.join(models.EventSuppression,
                               models.Alarm.alarm_id ==
                               models.EventSuppression.alarm_id)
            query = add_alarm_mgmt_affecting_by_event_suppression(query)
            query = add_alarm_degrade_affecting_by_event_suppression(query)

        try:
            result = query.one()
        except NoResultFound:
            return None

        alarm = result[0]
        alarm.mgmt_affecting = result[1]
        alarm.degrade_affecting = result[2]

        return alarm

    @objects.objectify(objects.alarm)
    def alarm_get_all(self, uuid=None, alarm_id=None, entity_type_id=None,
                      entity_instance_id=None, severity=None, alarm_type=None,
                      limit=None, include_suppress=False):
        query = model_query(models.Alarm, read_deleted="no")
        query = query.order_by(asc(models.Alarm.severity),
                               asc(models.Alarm.entity_instance_id),
                               asc(models.Alarm.id))
        if uuid is not None:
            query = query.filter(models.Alarm.uuid.contains(uuid))
        if alarm_id is not None:
            query = query.filter(models.Alarm.alarm_id.contains(alarm_id))
        if entity_type_id is not None:
            query = query.filter(models.Alarm.entity_type_id.contains(
                entity_type_id))
        if entity_instance_id is not None:
            query = query.filter(models.Alarm.entity_instance_id.contains(
                entity_instance_id))
        if severity is not None:
            query = query.filter(models.Alarm.severity.contains(severity))
        if alarm_type is not None:
            query = query.filter(models.Alarm.alarm_type.contains(alarm_type))
        query = add_alarm_filter_by_event_suppression(query, include_suppress)
        query = add_alarm_mgmt_affecting_by_event_suppression(query)
        query = add_alarm_degrade_affecting_by_event_suppression(query)
        if limit is not None:
            query = query.limit(limit)
        alarm_list = []
        try:
            results = query.all()
            for result in results:
                alarm = result[0]
                alarm.suppression_status = result[1]
                alarm.mgmt_affecting = result[2]
                alarm.degrade_affecting = result[3]
                alarm_list.append(alarm)
        except UnicodeDecodeError:
            LOG.error("UnicodeDecodeError occurred, "
                      "return an empty alarm list.")
        return alarm_list

    @objects.objectify(objects.alarm)
    def alarm_get_list(self, limit=None, marker=None,
                       sort_key=None, sort_dir=None,
                       include_suppress=False):
        query = model_query(models.Alarm)
        query = add_alarm_filter_by_event_suppression(query, include_suppress)
        query = add_alarm_mgmt_affecting_by_event_suppression(query)
        query = add_alarm_degrade_affecting_by_event_suppression(query)

        return _paginate_query(models.Alarm, limit, marker,
                               sort_key, sort_dir, query)

    def alarm_update(self, id, values):
        with _session_for_write() as session:
            query = model_query(models.Alarm, session=session)
            query = query.filter_by(id=id)

            count = query.update(values, synchronize_session='fetch')
            if count != 1:
                raise exceptions.AlarmNotFound(alarm=id)
            return query.one()

    def alarm_destroy(self, id):
        with _session_for_write() as session:
            query = model_query(models.Alarm, session=session)
            query = query.filter_by(uuid=id)
            try:
                query.one()
            except NoResultFound:
                raise exceptions.AlarmNotFound(alarm=id)
            query.delete()

    def alarm_destroy_by_ids(self, alarm_id, entity_instance_id):
        with _session_for_write() as session:
            query = model_query(models.Alarm, session=session)
            if alarm_id and entity_instance_id:
                query = query.filter_by(alarm_id=alarm_id)
                query = query.filter_by(entity_instance_id=entity_instance_id)
            try:
                query.one()
            except NoResultFound:
                raise exceptions.AlarmNotFound(alarm=alarm_id)
            query.delete()

    def event_log_create(self, values):
        if not values.get('uuid'):
            values['uuid'] = uuidutils.generate_uuid()
        event_log = models.EventLog()
        event_log.update(values)
        count = self.event_log_get_count()
        max_log = config.get_max_event_log()
        if count >= int(max_log):
            self.delete_oldest_event_log()
        with _session_for_write() as session:
            try:
                session.add(event_log)
                session.flush()
            except db_exc.DBDuplicateEntry:
                raise exceptions.EventLogAlreadyExists(id=values['id'])
            return event_log

    def event_log_get_count(self):
        query = model_query(models.EventLog)
        return query.count()

    def delete_oldest_event_log(self):
        result = self.event_log_get_oldest()
        self.event_log_delete(result['id'])

    def event_log_delete(self, id):
        with _session_for_write() as session:
            query = model_query(models.EventLog, session=session)
            query = query.filter_by(id=id)
            try:
                query.one()
            except NoResultFound:
                raise exceptions.EventLogNotFound(eventLog=id)
            query.delete()

    def event_log_get_oldest(self):
        query = model_query(models.EventLog)
        result = query.order_by(asc(models.EventLog.created_at)).limit(1).one()
        return result

    @objects.objectify(objects.event_log)
    def event_log_get(self, uuid):
        query = model_query(models.EventLog)

        if uuid:
            query = query.filter_by(uuid=uuid)

        query = add_event_log_filter_by_event_suppression(query,
                                                          include_suppress=True)

        try:
            result = query.one()
        except NoResultFound:
            raise exceptions.EventLogNotFound(eventLog=uuid)

        event = result[0]
        event.suppression_status = result[1]

        return event

    def _addEventTypeToQuery(self, query, evtType="ALL"):
        if evtType is None or not (evtType in ["ALL", "ALARM", "LOG"]):
            evtType = "ALL"

        if evtType == "ALARM":
            query = query.filter(or_(models.EventLog.state == "set",
                                     models.EventLog.state == "clear"))
        if evtType == "LOG":
            query = query.filter(models.EventLog.state == "log")

        return query

    @objects.objectify(objects.event_log)
    def event_log_get_all(self, uuid=None, event_log_id=None,
                          entity_type_id=None, entity_instance_id=None,
                          severity=None, event_log_type=None, start=None,
                          end=None, limit=None, evtType="ALL", include_suppress=False):
        query = model_query(models.EventLog, read_deleted="no")
        query = query.order_by(desc(models.EventLog.timestamp))
        if uuid is not None:
            query = query.filter_by(uuid=uuid)

        query = self._addEventTypeToQuery(query, evtType)

        if event_log_id is not None:
            query = query.filter(models.EventLog.event_log_id.contains(
                event_log_id))
        if entity_type_id is not None:
            query = query.filter(models.EventLog.entity_type_id.contains(
                entity_type_id))
        if entity_instance_id is not None:
            query = query.filter(models.EventLog.entity_instance_id.contains(
                entity_instance_id))
        if severity is not None:
            query = query.filter(models.EventLog.severity.contains(severity))

        if event_log_type is not None:
            query = query.filter_by(event_log_type=event_log_type)
        if start is not None:
            query = query.filter(models.EventLog.timestamp >= start)
        if end is not None:
            query = query.filter(models.EventLog.timestamp <= end)
        if include_suppress is not None:
            query = add_event_log_filter_by_event_suppression(query,
                                                              include_suppress)
        if limit is not None:
            query = query.limit(limit)

        hist_list = []
        try:
            result = query.all()
            for hist in result:
                event = hist[0]
                event.suppression_status = hist[1]
                hist_list.append(event)
        except UnicodeDecodeError:
            LOG.error("UnicodeDecodeError occurred, "
                      "return an empty event log list.")
        return hist_list

    @objects.objectify(objects.event_log)
    def event_log_get_list(self, limit=None, marker=None,
                           sort_key=None, sort_dir=None, evtType="ALL",
                           include_suppress=False):
        query = model_query(models.EventLog)
        query = self._addEventTypeToQuery(query, evtType)
        query = add_event_log_filter_by_event_suppression(query,
                                                          include_suppress)

        return _paginate_query(models.EventLog, limit, marker,
                               sort_key, sort_dir, query)

    @objects.objectify(objects.event_suppression)
    def event_suppression_get(self, id):
        query = model_query(models.EventSuppression)
        if uuidutils.is_uuid_like(id):
            query = query.filter_by(uuid=id)
        else:
            query = query.filter_by(id=id)

        try:
            result = query.one()
        except NoResultFound:
            raise exceptions.InvalidParameterValue(
                err="No event suppression entry found for %s" % id)

        return result

    @objects.objectify(objects.event_suppression)
    def event_suppression_get_all(self, uuid=None, alarm_id=None,
                                  description=None, suppression_status=None, limit=None,
                                  sort_key=None, sort_dir=None):
        query = model_query(models.EventSuppression, read_deleted="no")
        if uuid is not None:
            query = query.filter_by(uuid=uuid)
        if alarm_id is not None:
            query = query.filter_by(alarm_id=alarm_id)
        if description is not None:
            query = query.filter_by(description=description)
        if suppression_status is not None:
            query = query.filter_by(suppression_status=suppression_status)

        query = query.filter_by(set_for_deletion=False)

        return _paginate_query(models.EventSuppression, limit, None,
                               sort_key, sort_dir, query)

    @objects.objectify(objects.event_suppression)
    def event_suppression_update(self, uuid, values):
        with _session_for_write() as session:
            query = model_query(models.EventSuppression, session=session)
            query = query.filter_by(uuid=uuid)

            count = query.update(values, synchronize_session='fetch')
            if count != 1:
                raise exceptions.NotFound(id)
            return query.one()
