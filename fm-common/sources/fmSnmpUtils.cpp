//
// Copyright (c) 2014-2020 Wind River Systems, Inc.
//
// SPDX-License-Identifier: Apache-2.0
//

#include <assert.h>
#include <iostream>
#include <json-c/json.h>
#include <map>
#include <netdb.h>
#include <sstream>
#include <stdlib.h>
#include <string>
#include <unistd.h>
#include <vector>
#include <arpa/inet.h>

#include "fmAPI.h"
#include "fmConfig.h"
#include "fmDbAPI.h"
#include "fmDb.h"
#include "fmDbUtils.h"
#include "fmFile.h"
#include "fmLog.h"
#include "fmMsg.h"
#include "fmSnmpConstants.h"
#include "fmSnmpUtils.h"
#include "fmSocket.h"

#define JSON_TRAP_TAG_ALARM    "alarm"
#define JSON_TRAP_TAG_OP_TYPE  "operation_type"
#define JSON_TRAP_EMPTY        ""

typedef std::map<int,std::string> int_to_objtype;

static int_to_objtype objtype_map;
static pthread_mutex_t mutex = PTHREAD_RECURSIVE_MUTEX_INITIALIZER_NP;


fm_db_result_t &getTrapDestList(){
    static fm_db_result_t trap_dest_list;
    return trap_dest_list;
}

static void add_to_table(int t, std::string objtype, int_to_objtype &tbl) {
    tbl[t]=objtype;
}

static void init_objtype_table() {
    pthread_mutex_lock(&mutex);
    static bool has_inited=false;
    while (!has_inited){
        add_to_table(FM_ALARM_SEVERITY_CLEAR, ALARM_MSG, objtype_map);
        add_to_table(FM_ALARM_SEVERITY_WARNING, ALARM_WARNING, objtype_map);
        add_to_table(FM_ALARM_SEVERITY_MINOR, ALARM_MINOR, objtype_map);
        add_to_table(FM_ALARM_SEVERITY_MAJOR, ALARM_MAJOR, objtype_map);
        add_to_table(FM_ALARM_SEVERITY_CRITICAL, ALARM_CRITICAL, objtype_map);
        add_to_table(FM_ALARM_CLEAR, ALARM_CLEAR, objtype_map);
        add_to_table(FM_ALARM_HIERARCHICAL_CLEAR, ALARM_HIERARCHICAL_CLEAR, objtype_map);
        add_to_table(FM_ALARM_MESSAGE, ALARM_MSG, objtype_map);
        add_to_table(FM_WARM_START, WARM_START, objtype_map);
        has_inited=true;
    }
    pthread_mutex_unlock(&mutex);
}

/**
* This method creates a json trap with the operation type attribute.

    {
        "operation_type": "your_value",
        "alarm" : {
        }
    }

* Returns the json object representing the new trap.
*/
struct json_object* init_json_trap(std::string op_type){
    struct json_object *json_trap = json_object_new_object();
    struct json_object *json_data_operation_type =
            json_object_new_string(op_type.c_str());
    json_object_object_add(json_trap, JSON_TRAP_TAG_OP_TYPE,
            json_data_operation_type );
    struct json_object *alarm_values = json_object_new_object();
    json_object_object_add(json_trap, JSON_TRAP_TAG_ALARM, alarm_values);
    return json_trap;
}


/**

* This method adds new metadata given an json object that represents a trap.

ie: Given the attributes object_type "v1", value "v2"
the result will be this:

    {
        "operation_type": "alarm",
        "alarm" : { ...
                     "v1": "v2"
        }
    }

* The json object provided has the added metadata after the operation.

*/
void add_value_json_trap(struct json_object* json_trap, std::string obj_type,
    std::string value){

    struct json_object *json_alarm_values = NULL;
    json_object_object_get_ex(json_trap, JSON_TRAP_TAG_ALARM, &json_alarm_values);

    struct json_object *json_value = json_object_new_string(value.c_str());
    json_object_object_add(json_alarm_values, obj_type.c_str(), json_value);

    return;
}


/**
This method opens an socket and writes a message given a server name,
port number and the number of bytes of the message.

Returns True if message is write succesfully else returns False.

*/
bool send_data(const char * server_name, int portno, const void * message,
    int message_len){

    char addr[INET6_ADDRSTRLEN];
    static bool m_connected = false;
    static CFmSocket m_client;
    struct addrinfo hints;
    struct addrinfo *res = NULL;
    memset(&hints,0,sizeof(hints));
    hints.ai_family = AF_UNSPEC;     /* Allow IPv4 or IPv6 */
    hints.ai_socktype = SOCK_STREAM; /* Datagram socket */
    hints.ai_flags = 0;              /* For wildcard IP address */
    hints.ai_protocol = 0;           /* Any protocol */
    hints.ai_canonname = NULL;
    hints.ai_addr = NULL;
    hints.ai_next = NULL;
    bool result = false;

    int rc = getaddrinfo(server_name, NULL, &hints, &res);
    if (rc != 0) {
      FM_ERROR_LOG("ERROR failed to get SNMP trap server address info :%d", errno);
    } else {
        if (res->ai_family == AF_INET || res->ai_family==AF_INET6) {
          if(res->ai_family == AF_INET) {
            inet_ntop(AF_INET, &(((sockaddr_in*)res->ai_addr)->sin_addr),
                        addr, sizeof(addr));
          } else if (res->ai_family == AF_INET6) {
            inet_ntop(AF_INET6, &(((sockaddr_in6*)res->ai_addr)->sin6_addr),
                        addr, sizeof(addr));
          }
          m_connected = m_client.connect(addr, portno, res->ai_family);
          if (m_connected == true) {
            result = m_client.write_packet(message, message_len);
            if (result){
                FM_INFO_LOG("SNMP sent data successfully");
            }
          } else {
            FM_ERROR_LOG("ERROR failed to connect with SNMP trap server: %d", errno);
          }
        }
    }
    freeaddrinfo(res);
    return result;
}

static std::string get_trap_objtype(int type){
    init_objtype_table();
    return objtype_map[type];
}

static void add_to_list(std::vector<std::string> &trap_strings) {
    std::string delimiter = " ";

    std::vector<std::string>::iterator it = trap_strings.begin();
    std::vector<std::string>::iterator end = trap_strings.end();
    getTrapDestList().clear();
    for (; it != end; ++it){
        size_t pos = 0;
        fm_db_single_result_t entry;
        pos = (*it).find(delimiter);
        entry[FM_TRAPDEST_IP] = (*it).substr(0, pos);
        entry[FM_TRAPDEST_COMM] = (*it).erase(0, pos + delimiter.length());
        getTrapDestList().push_back(entry);
    }
}

void set_trap_dest_list(std::string value){

    std::vector<std::string> entries;
    std::istringstream f(value);
    std::string s;
    while (getline(f, s, ',')) {
        std::cout << s << std::endl;
        FM_INFO_LOG("Add entry: (%s)", s.c_str());
        entries.push_back(s);
    }
    add_to_list(entries);
    FM_INFO_LOG("Set trap entries: (%d)", getTrapDestList().size());
}


/**

*This method creates a JSON string representing a trap from the attributes
type and data.

an example of a JSON string:

    {
        "operation_type": "alarm_type_from_type_arg",
        "alarm": {
                ...
                "obj_type1":"value1"
                "obj_type2":"value2"
                ...
        }
    }

* Returns the JSON string created representing the trap.

*/
static std::string format_trap_json(int type, SFmAlarmDataT &data){

    std::string operation_type = get_trap_objtype(type);
    struct json_object *result = init_json_trap(operation_type);
    std::string result_json;
    std::string time_str;

    if(operation_type.empty() || result == NULL){
        return JSON_TRAP_EMPTY;
    }

    if (operation_type == ALARM_CLEAR){
        add_value_json_trap(result, ALARM_ID, data.alarm_id);
        add_value_json_trap(result, ALARM_INSTANCE_ID,
                data.entity_instance_id);
        fm_db_util_make_timestamp_string(time_str, data.timestamp, true);
        add_value_json_trap(result, ALARM_DATE_TIME, time_str);
        add_value_json_trap(result, ALARM_REASON_TEXT, data.reason_text);
    } else if (operation_type == ALARM_HIERARCHICAL_CLEAR){
        add_value_json_trap(result, ALARM_INSTANCE_ID,
                data.entity_instance_id);
        fm_db_util_make_timestamp_string(time_str, 0, true);
        add_value_json_trap(result, ALARM_DATE_TIME, time_str);
        add_value_json_trap(result, ALARM_REASON_TEXT, CLEAR_REASON_TEXT);
    } else if (operation_type == ALARM_MSG){
        add_value_json_trap(result, EVENT_ID, data.alarm_id);
        add_value_json_trap(result, EVENT_INSTANCE_ID,
                data.entity_instance_id);
        fm_db_util_make_timestamp_string(time_str, data.timestamp, true);
        add_value_json_trap(result, EVENT_DATE_TIME, time_str);
        add_value_json_trap(result, EVENT_SEVERITY,
                fm_db_util_int_to_string(data.severity));
        add_value_json_trap(result, EVENT_REASON_TEXT, data.reason_text);
        add_value_json_trap(result, EVENT_EVENT_TYPE,
                fm_db_util_int_to_string(data.alarm_type));
        add_value_json_trap(result, EVENT_CAUSE,
                fm_db_util_int_to_string(data.probable_cause));
        add_value_json_trap(result, EVENT_SERVICE_AFFECTING,
                fm_db_util_int_to_string(data.service_affecting));
    } else if (operation_type == WARM_START){
        // nothing to add to cmd
    } else {
        add_value_json_trap(result, ALARM_ID, data.alarm_id);
        add_value_json_trap(result, ALARM_INSTANCE_ID,
                data.entity_instance_id );
        fm_db_util_make_timestamp_string(time_str, data.timestamp, true);
        add_value_json_trap(result, ALARM_DATE_TIME, time_str);
        add_value_json_trap(result, ALARM_SEVERITY,
                fm_db_util_int_to_string(data.severity));
        add_value_json_trap(result, ALARM_REASON_TEXT, data.reason_text);
        add_value_json_trap(result, ALARM_EVENT_TYPE,
                fm_db_util_int_to_string(data.alarm_type));
        add_value_json_trap(result, ALARM_CAUSE,
                fm_db_util_int_to_string(data.probable_cause));
        add_value_json_trap(result, ALARM_REPAIR_ACTION,
                data.proposed_repair_action);
        add_value_json_trap(result, ALARM_SERVICE_AFFECTING,
                fm_db_util_int_to_string(data.service_affecting));
        add_value_json_trap(result, ALARM_SUPPRESSION,
                fm_db_util_int_to_string(data.suppression));
    }
    result_json = std::string(json_object_to_json_string_ext(result,
        JSON_C_TO_STRING_SPACED | JSON_C_TO_STRING_PRETTY));
    int freed_json = json_object_put(result);
    FM_DEBUG_LOG("JSON freed succesfully: %d", freed_json);
    return result_json;
}


/**

This method sends a JSON string representing the trap
to a trap server listening in a specific port.

The server name and port are readed from fm.conf file.

*/
bool fm_snmp_util_gen_trap(int type, SFmAlarmDataT &data) {

    bool send_json_success = false;
    std::string eid = "";
    std::string trap_server_ip = "";
    std::string trap_server_port = "";
    std::string trap_server_snmp_enabled = "";
    std::string key_ip = FM_TRAP_SERVER_IP;
    std::string key_port = FM_TRAP_SERVER_PORT;
    std::string key_enabled = FM_TRAP_SNMP_ENABLED;
    std::string json_trap = "";

    if (get_trap_objtype(type) != WARM_START) {
        eid.assign(data.entity_instance_id);
        std::string region_name = fm_db_util_get_region_name();
        std::string sys_name = fm_db_util_get_system_name();
        if (sys_name.length() != 0){
            eid = sys_name + "."+ eid;
        }
        if (region_name.length() != 0){
            eid = region_name + "."+ eid;
        }
        strncpy(data.entity_instance_id, eid.c_str(),
                        sizeof(data.entity_instance_id)-1);
    }

    if (!fm_get_config_key(key_ip, trap_server_ip)) {
        FM_ERROR_LOG("Fail to get config value for (%s)\n", key_ip.c_str());
        return false;
    };
    if (!fm_get_config_key(key_port, trap_server_port)){
        FM_ERROR_LOG("Fail to get config value for (%s)\n", key_port.c_str());
        return false;
    };
    if (!fm_get_config_key(key_enabled, trap_server_snmp_enabled)){
        FM_ERROR_LOG("Fail to get config value for (%s)\n", key_enabled.c_str());
        return false;
    };

    if (trap_server_snmp_enabled == "1"){
        json_trap = format_trap_json(type, data);

        if(json_trap.empty()){
            FM_ERROR_LOG("ERROR creating SNMP trap with type: %d", type);
            return false;
        }

        send_json_success = send_data(trap_server_ip.c_str(),
                atoi(trap_server_port.c_str()), json_trap.c_str(),
                        json_trap.length());

        if(send_json_success){
            FM_INFO_LOG("SNMP trap metadata sent succesfully %s %d",
                    json_trap.c_str(), json_trap.length());
        } else {
            FM_ERROR_LOG("ERROR failed to send SNMP trap metadata %s %d",
                    json_trap.c_str(), json_trap.length());
        }
    }else{
        FM_INFO_LOG("Fail to send SNMP trap metadata because snmp_trap_enabled"
                    " is not setted as 1, actual value: %s \n",
                    trap_server_snmp_enabled.c_str());
        return false;
    }
    return send_json_success;
}

static bool fm_snmp_get_db_connection(std::string &connection){
    const char *fn = "/etc/fm/fm.conf";
    std::string key = FM_SQL_CONNECTION;

    fm_conf_set_file(fn);
    return fm_get_config_key(key, connection);
}


extern "C" {
bool fm_snmp_util_create_session(TFmAlarmSessionT *handle, const char* db_conn){

    std::string conn;
    CFmDBSession *sess = new CFmDBSession;
    if (sess==NULL) return false;;

    if (db_conn == NULL){
        if (fm_snmp_get_db_connection(conn) != true){
            FM_ERROR_LOG("Fail to get db connection uri\n");
            delete sess;
            return false;
        }
        db_conn = conn.c_str();
    }

    if (sess->connect(db_conn) != true){
        FM_ERROR_LOG("Fail to connect to (%s)\n", db_conn);
        delete sess;
        return false;
    }
    *handle = sess;
    return true;
}

void fm_snmp_util_destroy_session(TFmAlarmSessionT handle) {
    CFmDBSession *sess = (CFmDBSession *)handle;

    if (sess != NULL){
        delete sess;
    }
}

bool fm_snmp_util_get_all_alarms(TFmAlarmSessionT handle, SFmAlarmQueryT *query) {

    assert(handle!=NULL);

    CFmDbAlarmOperation op;
    fm_db_result_t res;

    CFmDBSession &sess = *((CFmDBSession*)handle);

    if (!op.get_all_alarms(sess, &(query->alarm), &(query->num))) return false;

    return true;
}

bool fm_snmp_util_get_all_event_logs(TFmAlarmSessionT handle, SFmAlarmQueryT *query) {

    assert(handle!=NULL);

    CFmDbEventLogOperation op;
    fm_db_result_t res;

    CFmDBSession &sess = *((CFmDBSession*)handle);

    if (!op.get_all_event_logs(sess, &(query->alarm), &(query->num))) return false;

    return true;
}

}
