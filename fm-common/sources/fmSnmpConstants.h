//
// Copyright (c) 2017-2020 Wind River Systems, Inc.
//
// SPDX-License-Identifier: Apache-2.0
//

#include <string>

#define FM_ALARM_CLEAR  6
#define FM_ALARM_HIERARCHICAL_CLEAR 7
#define FM_ALARM_MESSAGE 8

#define FM_WARM_START 9

#define FM_CUSTOMER_LOG 10

/* MIB Trap definitions */
const std::string WRS_ALARM_MIB = "WRS-ALARM-MIB";

const std::string ALARM_CRITICAL = "wrsAlarmCritical";
const std::string ALARM_MAJOR = "wrsAlarmMajor";
const std::string ALARM_MINOR = "wrsAlarmMinor";
const std::string ALARM_WARNING = "wrsAlarmWarning";
const std::string ALARM_MSG = "wrsAlarmMessage";
const std::string ALARM_CLEAR = "wrsAlarmClear";
const std::string ALARM_HIERARCHICAL_CLEAR = "wrsAlarmHierarchicalClear";

const std::string ALARM_ID = "wrsAlarmActiveAlarmId";
const std::string ALARM_INSTANCE_ID = "wrsAlarmActiveEntityInstanceId";
const std::string ALARM_DATE_TIME = "wrsAlarmActiveDateAndTime";
const std::string ALARM_SEVERITY = "wrsAlarmActiveAlarmSeverity";
const std::string ALARM_REASON_TEXT = "wrsAlarmActiveReasonText";
const std::string ALARM_EVENT_TYPE = "wrsAlarmActiveEventType";
const std::string ALARM_CAUSE = "wrsAlarmActiveProbableCause";
const std::string ALARM_REPAIR_ACTION = "wrsAlarmActiveProposedRepairAction";
const std::string ALARM_SERVICE_AFFECTING = "wrsAlarmActiveServiceAffecting";
const std::string ALARM_SUPPRESSION = "wrsAlarmActiveSuppressionAllowed";

const std::string EVENT_ID = "wrsEventEventId";
const std::string EVENT_INSTANCE_ID = "wrsEventEntityInstanceId";
const std::string EVENT_DATE_TIME = "wrsEventDateAndTime";
const std::string EVENT_SEVERITY = "wrsEventSeverity";
const std::string EVENT_REASON_TEXT = "wrsEventReasonText";
const std::string EVENT_EVENT_TYPE = "wrsEventEventType";
const std::string EVENT_CAUSE = "wrsEventProbableCause";
const std::string EVENT_SERVICE_AFFECTING = "wrsEventServiceAffecting";

const std::string SNMPv2_MIB = "SNMPv2-MIB";
const std::string WARM_START = "warmStart";

const std::string CLEAR_REASON_TEXT = "System initiated hierarchical alarm clear";

