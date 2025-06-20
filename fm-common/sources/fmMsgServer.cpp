//
// Copyright (c) 2017-2025 Wind River Systems, Inc.
//
// SPDX-License-Identifier: Apache-2.0
//

#include <stdio.h>
#include <errno.h>
#include <list>
#include <new>
#include <vector>
#include <map>
#include <string>
#include <string.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <inttypes.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <algorithm>
#include <functional>
#include <cctype>
#include <locale>
#include <signal.h>
#include <pthread.h>
#include <libpq-fe.h>

#include "fmMsgServer.h"
#include "fmThread.h"
#include "fmSocket.h"
#include "fmAPI.h"
#include "fmMsg.h"
#include "fmAlarmUtils.h"
#include "fmLog.h"
#include "fmMutex.h"
#include "fmDbAlarm.h"
#include "fmSnmpConstants.h"
#include "fmSnmpUtils.h"
#include "fmDbUtils.h"
#include "fmDbEventLog.h"
#include "fmConstants.h"
#include "fmEventSuppression.h"
#include "fmConfig.h"

#define FM_UUID_LENGTH 36

typedef struct{
	int fd;
	fm_buff_t data;
}sFmGetReq;

typedef struct{
	int type;
	bool set;
	SFmAlarmDataT data;
}sFmJobReq;

typedef std::list<sFmGetReq> fmGetList;
typedef std::list<sFmJobReq> fmJobList;

CFmMutex & getJobMutex(){
	static CFmMutex *m = new CFmMutex;
	return *m;
}

CFmMutex & getListMutex(){
	static CFmMutex *m = new CFmMutex;
	return *m;
}

CFmMutex & getSockMutex(){
	static CFmMutex *m = new CFmMutex;
	return *m;
}

// trim from end
static inline std::string &rtrim(std::string &s) {
        s.erase(std::find_if(s.rbegin(), s.rend(),
        std::not1(std::ptr_fun<int, int>(std::isspace))).base(), s.end());
        return s;
}

fmJobList & getJobList(){
	static fmJobList lst;
	return lst;
}

fmGetList& getList(){
	static fmGetList lst;
	return lst;
}

static void enqueue_job(sFmJobReq &req){
	CFmMutexGuard m(getJobMutex());
	getJobList().push_back(req);
}

static bool dequeue_job(sFmJobReq &req){
	if (getJobList().size() == 0){
		//FM_DEBUG_LOG("Job queue is empty\n");
		return false;
	}
	CFmMutexGuard m(getJobMutex());
	fmJobList::iterator it = getJobList().begin();
	req = (*it);
	getJobList().pop_front();
	return true;
}

static void enqueue_get(sFmGetReq &req){
	CFmMutexGuard m(getListMutex());
	getList().push_back(req);
}

static bool dequeue_get(sFmGetReq &req){
	if (getList().size() == 0){
		//FM_DEBUG_LOG("Job queue is empty\n");
		return false;
	}
	CFmMutexGuard m(getListMutex());
	fmGetList::iterator it = getList().begin();
	req = (*it);
	getList().pop_front();
	return true;
}

void create_db_log(sFmJobReq &req){
	SFmAlarmDataT alarm = req.data;

	if (alarm.alarm_state != FM_ALARM_STATE_MSG){
		FM_ERROR_LOG("Unexpected request :(%d) (%s) (%s)", alarm.alarm_state,
				alarm.alarm_id, alarm.entity_instance_id);
		return;
	}

	fmLogAddEventLog(&alarm, false);
	fm_snmp_util_gen_trap(FM_ALARM_MESSAGE, alarm);
}

void get_db_alarm(CFmDBSession &sess, sFmGetReq &req, void *context){

	fm_buff_t buff = req.data;
	SFmMsgHdrT *hdr = (SFmMsgHdrT *)&buff[0];
	void * data = &buff[sizeof(SFmMsgHdrT)];
	AlarmFilter *filter = (AlarmFilter *)data;
	FmSocketServerProcessor *srv = (FmSocketServerProcessor *)context;
	CFmDbAlarmOperation op;
	fm_db_result_t res;
	SFmAlarmDataT alarm;

	memset(&alarm, 0, sizeof(alarm));
	hdr->msg_rc = FM_ERR_OK;
	res.clear();
	if ((op.get_alarm(sess, *filter, res)) != true){
		hdr->msg_rc = FM_ERR_DB_OPERATION_FAILURE;
	}else if (res.size() > 0){
		FM_INFO_LOG("Get  alarm: (%s) (%s)\n", filter->alarm_id,
				filter->entity_instance_id);
		CFmDbAlarm::convert_to(res[0],&alarm);
	}else{
		hdr->msg_rc = FM_ERR_ENTITY_NOT_FOUND;
	}

	if (hdr->msg_rc == FM_ERR_OK) {
		FM_DEBUG_LOG("Send resp: uuid (%s), alarm_id (%s)\n",
				alarm.uuid, alarm.alarm_id);
		srv->send_response(req.fd,hdr,&alarm,sizeof(alarm));
	}else{
		std::string err = fm_error_from_int((EFmErrorT)hdr->msg_rc);
		FM_DEBUG_LOG("Get alarm (%s) (%s) failed,send resp:(%s)\n",
				filter->alarm_id, filter->entity_instance_id, err.c_str());
		srv->send_response(req.fd,hdr,NULL,0);
	}
}

void get_db_alarms(CFmDBSession &sess, sFmGetReq &req, void *context){

	fm_buff_t buff = req.data;
	SFmMsgHdrT *hdr = (SFmMsgHdrT *)&buff[0];
	void * data = &buff[sizeof(SFmMsgHdrT)];
	fm_ent_inst_t *pid = (fm_ent_inst_t *)(data);
	fm_ent_inst_t &id = *pid;
	FmSocketServerProcessor *srv = (FmSocketServerProcessor *)context;
	CFmDbAlarmOperation op;
	fm_db_result_t res;
	std::vector<SFmAlarmDataT> alarmv;

	FM_DEBUG_LOG("handle get_db_alarms:%s\n", id);

	hdr->msg_rc = FM_ERR_OK;
	res.clear();
	if (op.get_alarms(sess, id, res) != true){
		hdr->msg_rc = FM_ERR_DB_OPERATION_FAILURE;
	}else if (res.size() > 0){
		int ix = 0;
		int resp_len = res.size();
		SFmAlarmDataT alarm;
		alarmv.clear();
		for ( ; ix < resp_len ; ++ix ) {
			CFmDbAlarm::convert_to(res[ix],&alarm);
			alarmv.push_back(alarm);
		}
	}else{
		FM_DEBUG_LOG("No alarms found for entity_instance_id (%s)\n", id);
		hdr->msg_rc = FM_ERR_ENTITY_NOT_FOUND;
	}

	if ((hdr->msg_rc==FM_ERR_OK) && (alarmv.size() > 0)){
		int found_num_alarms=alarmv.size();

		int total_len =(found_num_alarms * sizeof(SFmAlarmDataT)) + sizeof(uint32_t);

		void * buffer = malloc(total_len);
		if (buffer==NULL) {
			hdr->msg_rc =FM_ERR_SERVER_NO_MEM;
			srv->send_response(req.fd,hdr,NULL,0);
			return;
		}
		uint32_t *alen = (uint32_t*) buffer;
		*alen =found_num_alarms;

		SFmAlarmDataT * alarms = (SFmAlarmDataT*) ( ((char*)buffer)+sizeof(uint32_t));

		memcpy(alarms,&(alarmv[0]),alarmv.size() * sizeof(SFmAlarmDataT));
		srv->send_response(req.fd,hdr,buffer,total_len);
		free(buffer);
	} else {
		srv->send_response(req.fd,hdr,NULL,0);
	}
}

void get_db_alarms_by_id(CFmDBSession &sess, sFmGetReq &req, void *context){

	fm_buff_t buff = req.data;
	SFmMsgHdrT *hdr = (SFmMsgHdrT *)&buff[0];
	void * data = &buff[sizeof(SFmMsgHdrT)];
	fm_alarm_id *aid = (fm_alarm_id *)(data);
	fm_alarm_id &id = *aid;
	FmSocketServerProcessor *srv = (FmSocketServerProcessor *)context;
	CFmDbAlarmOperation op;
	fm_db_result_t res;
	std::vector<SFmAlarmDataT> alarmv;

	FM_DEBUG_LOG("handle get_db_alarms_by_id:%s\n", id);

	hdr->msg_rc = FM_ERR_OK;
	res.clear();
	if (op.get_alarms_by_id(sess, id, res) != true){
		hdr->msg_rc = FM_ERR_DB_OPERATION_FAILURE;
	}else if (res.size() > 0){
		int ix = 0;
		int resp_len = res.size();
		CFmDbAlarm dbAlm;
		SFmAlarmDataT alarm;
		alarmv.clear();
		for ( ; ix < resp_len ; ++ix ) {
			CFmDbAlarm::convert_to(res[ix],&alarm);
			alarmv.push_back(alarm);
		}
	}else{
		FM_DEBUG_LOG("No alarms found for alarm_id (%s)\n", id);
		hdr->msg_rc = FM_ERR_ENTITY_NOT_FOUND;
	}

	if ((hdr->msg_rc==FM_ERR_OK) && (alarmv.size() > 0)){
		int found_num_alarms=alarmv.size();

		int total_len =(found_num_alarms * sizeof(SFmAlarmDataT)) + sizeof(uint32_t);

		void * buffer = malloc(total_len);
		if (buffer==NULL) {
			hdr->msg_rc =FM_ERR_SERVER_NO_MEM;
			srv->send_response(req.fd,hdr,NULL,0);
			return;
		}
		uint32_t *alen = (uint32_t*) buffer;
		*alen =found_num_alarms;

		SFmAlarmDataT * alarms = (SFmAlarmDataT*) ( ((char*)buffer)+sizeof(uint32_t));

		memcpy(alarms,&(alarmv[0]),alarmv.size() * sizeof(SFmAlarmDataT));
		srv->send_response(req.fd,hdr,buffer,total_len);
		free(buffer);
	} else {
		srv->send_response(req.fd,hdr,NULL,0);
	}
}

/**
 * Retrieves faults from the database based on the specified alarm ID and entity instance ID.
 *
 * This function queries the database for alarms that match the provided alarm ID
 * and entity instance ID. The results are then sent back to the client through
 * the provided socket server processor.
 *
 * **Parameters:**
 * - `sess`: A reference to a `CFmDBSession` object representing the database session.
 * - `req`: A reference to an `sFmGetReq` structure containing the request data.
 * - `context`: A pointer to a context object.
 *
 * **Process Flow:**
 *    - The function initializes a buffer with the request data and extracts the header and data
 * sections.
 *    - It casts the data section to an `AlarmFilter` pointer and the context to an
 * `FmSocketServerProcessor` pointer.
 *    - Database Query
 *    - If alarms are found, it fills a vector with the alarm data.
 *    - Sets the number of alarms found in the buffer and copies the alarm data into the buffer.
 *    - It sends the response back to the client using the `send_response` method of the
 * `FmSocketServerProcessor`.
 *
 *    - If no alarms are found, it logs a message and sets the response code to
 * `FM_ERR_ENTITY_NOT_FOUND`.
 *
 * **Returns:**
 * - The function does not return a value but sends a response back to the client
 * through the provided socket server processor.
 */
void get_db_alarms_by_id_n_eid(CFmDBSession &sess, sFmGetReq &req, void *context){

	fm_buff_t buff = req.data;
	SFmMsgHdrT *hdr = (SFmMsgHdrT *)&buff[0];
	void * data = &buff[sizeof(SFmMsgHdrT)];
	AlarmFilter *filter = (AlarmFilter *)data;
	FmSocketServerProcessor *srv = (FmSocketServerProcessor *)context;
	CFmDbAlarmOperation op;
	fm_db_result_t res;
	std::vector<SFmAlarmDataT> alarmv;

	FM_DEBUG_LOG("handle get_db_alarms_by_id_n_eid:%s\n", filter->alarm_id);

	hdr->msg_rc = FM_ERR_OK;
	res.clear();
	if (op.get_alarms_by_id_n_eid(sess, *filter, res) != true){
		hdr->msg_rc = FM_ERR_DB_OPERATION_FAILURE;
	}else if (res.size() > 0){
		int ix = 0;
		int resp_len = res.size();
		SFmAlarmDataT alarm;
		alarmv.clear();
		// Fill the tuple data vector for the response.
		for ( ; ix < resp_len ; ++ix ) {
			CFmDbAlarm::convert_to(res[ix],&alarm);
			alarmv.push_back(alarm);
		}
	} else {
		FM_DEBUG_LOG("No alarms found for alarm id (%s), "
					 "entity_instance_id (%s)\n",
					 filter->alarm_id, filter->entity_instance_id);
		hdr->msg_rc = FM_ERR_ENTITY_NOT_FOUND;
	}

	if ((hdr->msg_rc==FM_ERR_OK) && (alarmv.size() > 0)){
		int found_num_alarms=alarmv.size();
		FM_DEBUG_LOG("Get faults: found alarms: (%d)", found_num_alarms);

		// (num of alarms found * size of alarm structure) +
		// space to report number of alarms found.
		int total_len =(found_num_alarms * sizeof(SFmAlarmDataT)) + sizeof(uint32_t);

		void * buffer = malloc(total_len);
		if (buffer==NULL) {
			hdr->msg_rc =FM_ERR_SERVER_NO_MEM;
			srv->send_response(req.fd,hdr,NULL,0);
			return;
		}
		uint32_t *alen = (uint32_t*) buffer;
		*alen = found_num_alarms;

		SFmAlarmDataT * alarms = (SFmAlarmDataT*) ( ((char*)buffer)+sizeof(uint32_t));

		memcpy(alarms,&(alarmv[0]),alarmv.size() * sizeof(SFmAlarmDataT));
		srv->send_response(req.fd,hdr,buffer,total_len);
		free(buffer);
	} else {
		srv->send_response(req.fd,hdr,NULL,0);
	}
}

void fm_handle_job_request(CFmDBSession &sess, sFmJobReq &req){
	CFmDbAlarmOperation op;
	CFmEventSuppressionOperation event_suppression_op;

	//check if it is a customer log request
	if (req.type == FM_CUSTOMER_LOG) {
		return create_db_log(req);
	}

	// check to see if there are any alarms need to be masked/unmasked
	if (req.type != FM_ALARM_HIERARCHICAL_CLEAR){
		if (req.data.inhibit_alarms){
			FM_INFO_LOG("%s alarms: (%s)\n", req.set ? "Mask" : "Unmask",
					req.data.entity_instance_id);
			op.mask_unmask_alarms(sess, req.data, req.set);
		}
	}
	if (!op.add_alarm_history(sess, req.data, req.set)){
		FM_ERROR_LOG("Failed to add historical alarm to DB (%s) (%s",
				req.data.alarm_id, req.data.entity_instance_id);
	}

	bool is_event_suppressed = false;

	if ((req.type != FM_ALARM_HIERARCHICAL_CLEAR) &&
			(!event_suppression_op.get_event_suppressed(sess, req.data, is_event_suppressed))) {
		FM_ERROR_LOG("Failed to retrieve event suppression status in DB for (%s)",
				req.data.alarm_id);
	} else {
        if (!is_event_suppressed)
		    fm_snmp_util_gen_trap(req.type, req.data);
	}

	fmLogAddEventLog(&req.data, is_event_suppressed);

}

void fm_handle_get_request(CFmDBSession &sess, sFmGetReq &req,
		void *context){
	fm_buff_t buff = req.data;
	SFmMsgHdrT *hdr = (SFmMsgHdrT *)&buff[0];
	switch(hdr->action) {
	case EFmGetFault:get_db_alarm(sess,req,context); break;
	case EFmGetFaults:get_db_alarms(sess,req,context); break;
	case EFmGetFaultsById:get_db_alarms_by_id(sess,req,context); break;
	case EFmGetFaultsByIdnEid:get_db_alarms_by_id_n_eid(sess,req,context); break;
	default:
		FM_ERROR_LOG("Unexpected job request, action:%u\n",hdr->action);
		break;
	}
}
inline void * prep_msg_buffer(std::vector<char> &buff, int reserved_size,
		SFmMsgHdrT *&hdr) {
	buff.resize(sizeof(SFmMsgHdrT) + reserved_size);
	hdr = (SFmMsgHdrT*)&(buff[0]);
	hdr->msg_size = reserved_size;
	hdr->version = EFmMsgV1;
	hdr->msg_rc = 0;
	return  &(buff[sizeof(SFmMsgHdrT)]);
}

#define is_request_valid(len,structdata) \
	if (len != sizeof(structdata)) { \
		hdr->msg_rc = FM_ERR_INVALID_REQ; 	\
		send_response(fd,hdr,NULL,0);	\
		return;	\
	}


void FmSocketServerProcessor::send_response(int fd, SFmMsgHdrT *hdr, void *data, size_t len) {
	fm_buff_t resp;
	CFmMutexGuard m(getSockMutex());
	if (fm_msg_utils_prep_requet_msg(resp,hdr->action,data,len)!=FM_ERR_OK) {
		rm_socket(fd);
		FM_INFO_LOG("Failed to prepare response, close fd:(%d)", fd);
		::close(fd);
		return;
	}
	ptr_to_hdr(resp)->msg_rc = hdr->msg_rc;
	if (!write_packet(fd,resp)){
		FM_INFO_LOG("Failed to send response, close fd:(%d)", fd);
		rm_socket(fd);
		::close(fd);
		return;
	}
}

void FmSocketServerProcessor::handle_create_fault(int fd,
		SFmMsgHdrT *hdr, std::vector<char> &rdata, CFmDBSession &sess, bool send_response_flag) {

	is_request_valid(hdr->msg_size,SFmAlarmDataT);
	void * data = &(rdata[sizeof(SFmMsgHdrT)]);
	CFmDbAlarmOperation op;
	CFmDbEventLogOperation log_op;
	CFmDbEventLog dbLog;
	CFmDbAlarm a;
	sFmJobReq req;

	SFmAlarmDataT *alarm = (SFmAlarmDataT *)(data);
	FM_DEBUG_LOG("Time stamp in the alarm message: (%lld)", alarm->timestamp);
	if ((strlen(alarm->uuid)) != FM_UUID_LENGTH) {
		fm_uuid_create(alarm->uuid);
	}
	hdr->msg_rc = FM_ERR_OK;

	req.data = *alarm;
	req.set = true;

	FM_INFO_LOG("Raising Alarm/Log, (%s) (%s)", alarm->alarm_id, alarm->entity_instance_id);
	//enqueue the customer log request after writing it the DB
	if (alarm->alarm_state == FM_ALARM_STATE_MSG) {
		alarm->alarm_state = FM_ALARM_STATE_LOG;
		dbLog.create_data(alarm);
		if (log_op.create_event_log(sess, dbLog)) {
				FM_INFO_LOG("Log generated in DB:  (%s) (%s) (%d)\n",
						alarm->alarm_id, alarm->entity_instance_id, alarm->severity);
				req.type = FM_CUSTOMER_LOG;
				enqueue_job(req);
		}else{
			FM_ERROR_LOG("Fail to create customer log: (%s) (%s)\n",
					alarm->alarm_id, alarm->entity_instance_id);
			hdr->msg_rc = FM_ERR_DB_OPERATION_FAILURE;
		}
		FM_INFO_LOG("Send response for create log, uuid:(%s) (%u)\n",
					alarm->uuid, hdr->msg_rc);
		if (send_response_flag)
			send_response(fd,hdr,alarm->uuid,sizeof(alarm->uuid));
	} else {
		a.create_data(alarm);
		//a.print();
		if (op.create_alarm(sess, a)) {
			std::string uuid_str = a.find_field(FM_ALARM_COLUMN_UUID);
			strncpy(alarm->uuid, uuid_str.c_str(), sizeof(alarm->uuid));
			FM_INFO_LOG("Alarm created/updated/kept: (%s) (%s) (%d) (%s)\n",
						alarm->alarm_id, alarm->entity_instance_id, alarm->severity, alarm->uuid);
			req.type = alarm->severity;
			enqueue_job(req);
		} else {
			FM_ERROR_LOG("Fail to create/update alarm: (%s) (%s)\n",
						alarm->alarm_id, alarm->entity_instance_id);
			hdr->msg_rc = FM_ERR_DB_OPERATION_FAILURE;
		}

		if (send_response_flag) {
			FM_INFO_LOG("Send response for create fault, uuid:(%s) (%u)\n",
						alarm->uuid, hdr->msg_rc);
			send_response(fd, hdr, alarm->uuid, sizeof(alarm->uuid));
		}
	}
}

void FmSocketServerProcessor::handle_create_fault_list(int fd,
	SFmMsgHdrT *hdr, std::vector<char> &rdata, CFmDBSession &sess) {

	// Validate the basic message size first
	// We cannot use is_request_valid because the size is variable based
	// on the number of alarms, so we just verify if the sent size is a
	// multiple of sizeof(SFmAlarmDataT)
	if (hdr->msg_size % sizeof(SFmAlarmDataT) != 0) {
		FM_ERROR_LOG("Invalid message size: %u, expected multiple of %zu",
			hdr->msg_size, sizeof(SFmAlarmDataT));
		hdr->msg_rc = FM_ERR_INVALID_REQ;
		send_response(fd, hdr, NULL, 0);
		return;
	}

	const size_t num_alarms = hdr->msg_size / sizeof(SFmAlarmDataT);

	FM_INFO_LOG("Processing create fault list with %u entries", num_alarms);

	size_t offset = sizeof(SFmMsgHdrT);
	for (uint32_t i = 0; i < num_alarms; ++i) {
		// Create a new message header and data to isolate each alarm information when
		// passing to the handle_create_fault function
		SFmMsgHdrT alarm_hdr = *hdr;
		alarm_hdr.msg_size = sizeof(SFmAlarmDataT);
		std::vector<char> alarm_data(sizeof(SFmMsgHdrT) + sizeof(SFmAlarmDataT));
		memcpy(alarm_data.data(), &alarm_hdr, sizeof(SFmMsgHdrT));
		memcpy(alarm_data.data() + sizeof(SFmMsgHdrT), &rdata[offset], sizeof(SFmAlarmDataT));

		// We don't want for handle_create_fault to send any response back to the client or else it
		// will receive the response for the first call only, so we set send_response_flag to false
		handle_create_fault(fd, &alarm_hdr, alarm_data, sess, false);

		if (alarm_hdr.msg_rc != FM_ERR_OK) {
			FM_ERROR_LOG("Failed to create fault entry %u, stopping processing", i);
			hdr->msg_rc = alarm_hdr.msg_rc;
			send_response(fd, hdr, NULL, 0);
			return;
		}

		// Move the offset to the next alarm
		offset += sizeof(SFmAlarmDataT);
	}

	FM_INFO_LOG("Successfully processed all %u fault entries", num_alarms);
	send_response(fd, hdr, NULL, 0);
}

void FmSocketServerProcessor::handle_delete_faults(int fd,
		SFmMsgHdrT *hdr, std::vector<char> &rdata, CFmDBSession &sess) {

	CFmDbAlarmOperation op;
	sFmJobReq req;
	is_request_valid(hdr->msg_size,fm_ent_inst_t);
	void * data = &(rdata[sizeof(SFmMsgHdrT)]);
	fm_ent_inst_t *pid = (fm_ent_inst_t *)(data);
	fm_ent_inst_t &id = *pid;
	int rc = 0;

	hdr->msg_rc = FM_ERR_OK;
	rc = op.delete_alarms(sess,id);
	if (rc > 0){
		FM_DEBUG_LOG("Deleted alarms (%s)\n", id);
		SFmAlarmDataT alarm;
		memset(&alarm, 0, sizeof(alarm));
		//only cares about entity_instance_id in hierarchical alarm clear trap
		strncpy(alarm.entity_instance_id, id, sizeof(alarm.entity_instance_id)-1);
		strncpy(alarm.reason_text,CLEAR_ALL_REASON_TEXT,
				sizeof(alarm.reason_text)-1);
		fm_uuid_create(alarm.uuid);
		req.type = FM_ALARM_HIERARCHICAL_CLEAR;
		req.set = false;
		req.data = alarm;
		enqueue_job(req);
	} else if (rc == 0){
		hdr->msg_rc = FM_ERR_ENTITY_NOT_FOUND;
	} else {
		hdr->msg_rc = FM_ERR_DB_OPERATION_FAILURE;
	}

	FM_INFO_LOG("Deleted alarms status: (%s) (%s)\n",
		id,
		fm_error_from_int((EFmErrorT)hdr->msg_rc).c_str());

	send_response(fd,hdr,NULL,0);
}

/**
 * Handles the deletion of faults based on the specified filter.
 *
 * This function processes the request to delete faults from the database.
 * It first validates the request, then retrieves matching alarms and deletes
 * them from the database. If multiple alarms are found, it handles each
 * alarm separately and enqueues a job for each cleared alarm.
 *
 * **Parameters:**
 * - `fd`: The file descriptor for the client connection.
 * - `hdr`: A pointer to an `SFmMsgHdrT` structure containing the message header.
 * - `rdata`: A reference to a vector of characters containing the request data.
 * - `sess`: A reference to a `CFmDBSession` object representing the database session.
 *
 * **Returns:**
 * - The function does not return a value but sends a response back to the client through
 * the provided file descriptor.
 */
void FmSocketServerProcessor::handle_delete_fault(
	int fd,
	SFmMsgHdrT *hdr,
	std::vector<char> &rdata,
	CFmDBSession &sess,
    bool send_response_flag) {

	CFmDbAlarmOperation op;
	sFmJobReq req;
	CFmDbAlarm dbAlm;
	SFmAlarmDataT alarm;
	fm_db_result_t res;

	is_request_valid(hdr->msg_size, AlarmFilter);
	void * data = &(rdata[sizeof(SFmMsgHdrT)]);
	AlarmFilter *filter = (AlarmFilter *)(data);
	hdr->msg_rc = FM_ERR_OK;
	res.clear();
	if ((op.get_alarms_eid_not_strict(sess, *filter, res)) != true) {
		hdr->msg_rc = FM_ERR_DB_OPERATION_FAILURE;
	} else {
		if (res.size() > 0) {
			if (op.delete_alarm(sess, *filter) > 0) {
				FM_INFO_LOG("Deleted alarm(s): (%s) (%s)\n",
				            filter->alarm_id, filter->entity_instance_id);
				if (res.size() == 1) {
					// normal workflow, just one alarm match
					CFmDbAlarm::convert_to(res[0], &alarm);
					fm_uuid_create(alarm.uuid);
					req.type = FM_ALARM_CLEAR;
					req.set = false;
					req.data = alarm;
					enqueue_job(req);
				} else {
					//  Multiple alarms received
					for (const auto &entry : res) {
						SFmAlarmDataT alarm;
						CFmDbAlarm::data_type entry_copy = entry;
						CFmDbAlarm::convert_to(entry_copy, &alarm);
						fm_uuid_create(alarm.uuid);
						req.type = FM_ALARM_CLEAR;
						req.set = false;
						req.data = alarm;
						enqueue_job(req);
					}
				}
			} else {
				hdr->msg_rc = FM_ERR_DB_OPERATION_FAILURE;
				FM_INFO_LOG("Deleted alarm failed: (%s) (%s) (%s)\n",
				            filter->alarm_id, filter->entity_instance_id,
				            fm_error_from_int((EFmErrorT)hdr->msg_rc).c_str());
			}
		} else {
			hdr->msg_rc = FM_ERR_ENTITY_NOT_FOUND;
			FM_INFO_LOG("Deleted alarm failed: (%s) (%s) (%s)\n",
			            filter->alarm_id, filter->entity_instance_id,
			            fm_error_from_int((EFmErrorT)hdr->msg_rc).c_str());
		}
	}
	FM_INFO_LOG("Response to delete fault: %u\n", hdr->msg_rc);
	if (send_response_flag)
		send_response(fd, hdr, NULL, 0);
}

void FmSocketServerProcessor::handle_delete_fault_list(int fd,
	SFmMsgHdrT *hdr, std::vector<char> &rdata, CFmDBSession &sess) {

	// Validate the basic message size first
	// We cannot use is_request_valid because the size is variable based
	// on the number of entities, so we just verify if the sent size is a
	// multiple of sizeof(AlarmFilter)
	if (hdr->msg_size % sizeof(AlarmFilter) != 0) {
		FM_ERROR_LOG("Invalid message size: %u, expected multiple of %zu",
			hdr->msg_size, sizeof(AlarmFilter));
		hdr->msg_rc = FM_ERR_INVALID_REQ;
		send_response(fd, hdr, NULL, 0);
		return;
	}

	const size_t num_alarms = hdr->msg_size / sizeof(AlarmFilter);

	FM_INFO_LOG("Processing delete fault list with %u entries", num_alarms);

	size_t offset = sizeof(SFmMsgHdrT);

	// Process each alarm entry
	for (uint32_t i = 0; i < num_alarms; ++i) {
		// Create a new message header and data to isolate each alarm information when
		// passing to the handle_delete_fault function
		SFmMsgHdrT alarm_hdr = *hdr;
		alarm_hdr.msg_size = sizeof(AlarmFilter);
		std::vector<char> alarm_data(sizeof(SFmMsgHdrT) + sizeof(AlarmFilter));
		memcpy(alarm_data.data(), &alarm_hdr, sizeof(SFmMsgHdrT));
		memcpy(alarm_data.data() + sizeof(SFmMsgHdrT), &rdata[offset], sizeof(AlarmFilter));

		// We don't want for handle_delete_fault to send any response, so we set
		// send_response_flag to false
		handle_delete_fault(fd, &alarm_hdr, alarm_data, sess, false);

		// Ignore FM_ERR_ENTITY_NOT_FOUND since an absent alarm doesn't raise API errors
		if (alarm_hdr.msg_rc != FM_ERR_OK &&
		    alarm_hdr.msg_rc != FM_ERR_ENTITY_NOT_FOUND) {
			FM_ERROR_LOG("Failed to delete fault entry %u with rc %u, stopping processing",
				i, alarm_hdr.msg_rc);
			hdr->msg_rc = alarm_hdr.msg_rc;
			send_response(fd, hdr, NULL, 0);
			return;
		}

		// Move the offset to the next alarm
		offset += sizeof(AlarmFilter);
	}

	FM_INFO_LOG("Successfully deleted all %u fault entries", num_alarms);
	send_response(fd, hdr, NULL, 0);
}

void FmSocketServerProcessor::handle_get_faults_by_id(int fd,
		SFmMsgHdrT *hdr, std::vector<char> &rdata) {

	is_request_valid(hdr->msg_size,fm_alarm_id);
	sFmGetReq req;
	req.fd = fd;
	req.data = rdata;
	enqueue_get(req);
}

void FmSocketServerProcessor::handle_get_faults_by_id_n_eid(int fd,
		SFmMsgHdrT *hdr, std::vector<char> &rdata) {

	is_request_valid(hdr->msg_size,AlarmFilter);
	sFmGetReq req;
	req.fd = fd;
	req.data = rdata;
	enqueue_get(req);
}

void FmSocketServerProcessor::handle_get_faults(int fd,
		SFmMsgHdrT *hdr, std::vector<char> &rdata) {

	is_request_valid(hdr->msg_size,fm_ent_inst_t);
	sFmGetReq req;
	req.fd = fd;
	req.data = rdata;
	enqueue_get(req);
}

void FmSocketServerProcessor::handle_get_fault(int fd,
		SFmMsgHdrT *hdr, std::vector<char> &rdata) {

	is_request_valid(hdr->msg_size,AlarmFilter);
	sFmGetReq req;
	req.fd = fd;
	req.data = rdata;
	enqueue_get(req);
}

void FmSocketServerProcessor::handle_socket_data(int fd,
		std::vector<char> &rdata, CFmDBSession &sess) {

	SFmMsgHdrT *hdr = (SFmMsgHdrT *)&(rdata[0]);

	FM_DEBUG_LOG("Processor: handler socket data, action:%u\n",hdr->action);
	switch(hdr->action) {
	case EFmCreateFault:handle_create_fault(fd,hdr,rdata, sess); break;
	case EFmDeleteFault:handle_delete_fault(fd, hdr,rdata, sess); break;
	case EFmDeleteFaults:handle_delete_faults(fd,hdr,rdata,sess); break;
	case EFmGetFault:handle_get_fault(fd,hdr,rdata); break;
	case EFmGetFaults:handle_get_faults(fd,hdr,rdata); break;
	case EFmGetFaultsById:handle_get_faults_by_id(fd,hdr,rdata); break;
	case EFmGetFaultsByIdnEid:handle_get_faults_by_id_n_eid(fd,hdr,rdata); break;
	case EFmCreateFaultList:handle_create_fault_list(fd,hdr,rdata, sess); break;
	case EFmDeleteFaultList:handle_delete_fault_list(fd,hdr,rdata,sess); break;
	default:
		FM_ERROR_LOG("Unexpected client request, action:%u\n",hdr->action);
		break;
	}
}

extern "C" {
EFmErrorT fm_server_create(const char *fn) {
		signal(SIGPIPE,SIG_IGN);
		FmSocketServerProcessor srv;
		size_t retries = 5, count = 0, my_sleep = 2000;//2 seconds
		const std::string host = "controller";
		int rc = 0;
        bool rt = false;
        struct addrinfo hints;
        struct addrinfo *result=NULL, *rp;
        char addr[INET6_ADDRSTRLEN];
        memset(&hints,0,sizeof(hints));
        hints.ai_family = AF_UNSPEC;    /* Allow IPv4 or IPv6 */
        hints.ai_socktype = SOCK_STREAM; /* Datagram socket */
        hints.ai_flags = 0;    /* For wildcard IP address */
        hints.ai_protocol = 0;          /* Any protocol */
        hints.ai_canonname = NULL;
        hints.ai_addr = NULL;
        hints.ai_next = NULL;

        fm_conf_set_file(fn);

        fmLoggingInit();

        if (!fm_db_util_sync_event_suppression()){
        	exit(-1);
        }

        if (!fmCreateThread(fmJobHandlerThread,NULL)) {
        	exit(-1);
        }

        if (!fmCreateThread(fmRegHandlerThread,&srv)) {
        	exit(-1);
        }

        if (!fmCreateThread(fmEventSuppressionMonitorThread,NULL)) {
        	exit(-1);
        }

        FM_INFO_LOG("Starting fmManager...\n");

        while (true) {
        	rc = getaddrinfo(host.c_str(),NULL, &hints,&result);
        	if (rc == 0){
        		for (rp = result; rp != NULL; rp = rp->ai_next) {
        			if (rp->ai_family==AF_INET||rp->ai_family==AF_INET6) {
                                        if(rp->ai_family==AF_INET) {
                                            inet_ntop(AF_INET, &(((sockaddr_in*)rp->ai_addr)->sin_addr), addr, sizeof(addr));
                                        } else if (rp->ai_family==AF_INET6) {
                                            inet_ntop(AF_INET6, &(((sockaddr_in6*)rp->ai_addr)->sin6_addr), addr, sizeof(addr));
                                        }
        				rt = srv.server_sock(addr,8001,rp->ai_family);
        				if (rt == true) break;
        				if (count < retries){
        					FM_INFO_LOG("Bind (%s) (%s) address failed, error: (%d) (%s)",
        							host.c_str(), addr, errno, strerror(errno));
        				}
        			}
        		}
        		freeaddrinfo(result);
        	}else{
        		FM_INFO_LOG("(%s) address lookup failed, error: (%d) (%s)",
        		        	host.c_str(),errno, strerror(errno));
        	}

        	if (rt ==true) break;

        	if (count > retries){
        		FM_ERROR_LOG("Failed to bind to controller IP, exit...");
        		exit(-1);
        	}

           	fmThreadSleep(my_sleep);
        	count++;
        }

        if ( rt == false)
        	return (EFmErrorT)-1;

        srv.run();
        return FM_ERR_OK;
}

void fmJobHandlerThread(void *context){

	CFmDBSession *sess;

	if (fm_db_util_create_session(&sess) != true){
		FM_ERROR_LOG("Fail to create DB session, exit ...\n");
		exit (-1);
	}

	while (true){
		sFmJobReq req;
		while (dequeue_job(req)){
			fm_handle_job_request(*sess,req);
		}
		fmThreadSleep(200);
	}
}

void fmRegHandlerThread(void *context){

	CFmDBSession *sess;
	if (fm_db_util_create_session(&sess) != true){
		FM_ERROR_LOG("Fail to create DB session, exit ...\n");
		exit (-1);
	}
	while (true){
		sFmGetReq req;
		while (dequeue_get(req)){
			fm_handle_get_request(*sess, req, context);
		}
		fmThreadSleep(100);
	}
}

bool fm_handle_event_suppress_changes(CFmDBSession &sess){

    int sock_fd;
    fd_set  readset;
    PGconn  *pgconn = NULL;
    PGnotify  *notify;

    pgconn = sess.get_pgconn();
    sock_fd = PQsocket(pgconn);

    FD_ZERO(&readset);
    FD_SET(sock_fd, &readset);

    // Wait for event_suppression update to occur
    if (select(sock_fd + 1, &readset, NULL, NULL, NULL) < 0)
    {
		FM_ERROR_LOG("select() failed: %s\n", strerror(errno));

		if (errno!=EINTR)
			return false;
    }

    // Now check for input. This will clear the queue
    PQconsumeInput(pgconn);
    while ((notify = PQnotifies(pgconn)) != NULL)
    {
        PQfreemem(notify);
    }

    SFmAlarmDataT *alarm = NULL;
    fm_snmp_util_gen_trap(FM_WARM_START, *alarm);

    return true;
}

void fmEventSuppressionMonitorThread(void *context){

	CFmDBSession *sess;
	CFmEventSuppressionOperation event_suppression_op;

	if (fm_db_util_create_session(&sess) != true){
		FM_ERROR_LOG("Fail to create DB session, exit ...\n");
		exit (-1);
	}

	if (event_suppression_op.set_table_notify_listen(*sess) != true){
		FM_ERROR_LOG("Fail to set DB table notify and listen, exit ...\n");
		exit (-1);
	}

	while (true){
		fm_handle_event_suppress_changes(*sess);
		fmThreadSleep(30000);   // 30 second wait allows some time to buffer in multiple notify events
		                        // and send only 1 Warm Start trap as a result
	}
}

}

