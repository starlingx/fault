#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for fm_api constants module."""
# pylint: disable=protected-access,unused-argument

import unittest


class TestFmApiConstants(unittest.TestCase):
    """Test fm_api constants definitions."""

    def setUp(self):
        """Import constants module."""
        from fm_api import constants as c
        self.c = c

    def test_entity_types_defined(self):
        """Verify entity type constants are strings."""
        self.assertEqual(self.c.FM_ENTITY_TYPE_SYSTEM, 'system')
        self.assertEqual(self.c.FM_ENTITY_TYPE_HOST, 'host')
        self.assertEqual(self.c.FM_ENTITY_TYPE_PORT, 'port')
        self.assertEqual(self.c.FM_ENTITY_TYPE_INTERFACE, 'interface')
        self.assertEqual(self.c.FM_ENTITY_TYPE_SERVICE, 'service')
        self.assertEqual(self.c.FM_ENTITY_TYPE_CLUSTER, 'cluster')
        self.assertEqual(self.c.FM_ENTITY_TYPE_K8S, 'kubernetes')

    def test_alarm_groups_defined(self):
        """Verify alarm group constants."""
        self.assertEqual(self.c.ALARM_GROUP_GENERAL, "100")
        self.assertEqual(self.c.ALARM_GROUP_MAINTENANCE, "200")
        self.assertEqual(self.c.ALARM_GROUP_NETWORK, "300")
        self.assertEqual(self.c.ALARM_GROUP_HA, "400")
        self.assertEqual(self.c.ALARM_GROUP_SECURITY, "500")
        self.assertEqual(self.c.ALARM_GROUP_VM, "700")
        self.assertEqual(self.c.ALARM_GROUP_STORAGE, "800")
        self.assertEqual(self.c.ALARM_GROUP_SW_MGMT, "900")

    def test_alarm_ids_format(self):
        """Verify alarm IDs follow group.event format."""
        self.assertTrue(self.c.FM_ALARM_ID_FS_USAGE.startswith("100."))
        self.assertTrue(
            self.c.FM_ALARM_ID_NETWORK_PORT.startswith("300."))
        self.assertTrue(
            self.c
            .FM_ALARM_ID_HA_SERVICE_GROUP_STATE
            .startswith("400."))
        self.assertTrue(
            self.c.FM_ALARM_ID_VM_FAILED.startswith("700."))

    def test_alarm_states(self):
        """Verify alarm state constants."""
        self.assertEqual(self.c.FM_ALARM_STATE_SET, 'set')
        self.assertEqual(self.c.FM_ALARM_STATE_CLEAR, 'clear')
        self.assertEqual(self.c.FM_ALARM_STATE_MSG, 'msg')
        self.assertEqual(self.c.FM_ALARM_STATE_LOG, 'log')

    def test_alarm_state_list(self):
        """Verify ALARM_STATE list contains all states."""
        self.assertIn('set', self.c.ALARM_STATE)
        self.assertIn('clear', self.c.ALARM_STATE)
        self.assertIn('msg', self.c.ALARM_STATE)
        self.assertIn('log', self.c.ALARM_STATE)
        self.assertEqual(len(self.c.ALARM_STATE), 4)

    def test_alarm_severity_constants(self):
        """Verify severity constants."""
        self.assertEqual(self.c.FM_ALARM_SEVERITY_CLEAR, 'clear')
        self.assertEqual(self.c.FM_ALARM_SEVERITY_WARNING, 'warning')
        self.assertEqual(self.c.FM_ALARM_SEVERITY_MINOR, 'minor')
        self.assertEqual(self.c.FM_ALARM_SEVERITY_MAJOR, 'major')
        self.assertEqual(self.c.FM_ALARM_SEVERITY_CRITICAL, 'critical')

    def test_alarm_severity_list(self):
        """Verify ALARM_SEVERITY list."""
        expected = ['clear', 'warning', 'minor', 'major', 'critical']
        self.assertEqual(self.c.ALARM_SEVERITY, expected)

    def test_alarm_types(self):
        """Verify alarm type constants."""
        self.assertEqual(self.c.FM_ALARM_TYPE_0, 'other')
        self.assertEqual(self.c.FM_ALARM_TYPE_1, 'communication')
        self.assertEqual(self.c.FM_ALARM_TYPE_3, 'processing-error')
        self.assertEqual(self.c.FM_ALARM_TYPE_4, 'equipment')

    def test_alarm_type_list(self):
        """Verify ALARM_TYPE list has 12 entries."""
        self.assertEqual(len(self.c.ALARM_TYPE), 12)
        self.assertIn('other', self.c.ALARM_TYPE)
        self.assertIn('communication', self.c.ALARM_TYPE)

    def test_alarm_status_constants(self):
        """Verify alarm status constants."""
        self.assertEqual(self.c.FM_ALARM_OK_STATUS, "OK")
        self.assertEqual(self.c.FM_ALARM_DEGRADED_STATUS, "degraded")
        self.assertEqual(self.c.FM_ALARM_CRITICAL_STATUS, "critical")

    def test_alarm_status_list(self):
        """Verify ALARM_STATUS list."""
        self.assertEqual(len(self.c.ALARM_STATUS), 3)
        self.assertIn("OK", self.c.ALARM_STATUS)

    def test_alarm_context_constants(self):
        """Verify alarm context constants."""
        self.assertEqual(self.c.FM_ALARM_CONTEXT_STARLINGX, 'starlingx')
        self.assertEqual(self.c.FM_ALARM_CONTEXT_OPENSTACK, 'openstack')
        self.assertEqual(self.c.FM_ALARM_CONTEXT_NONE, 'none')

    def test_alarm_context_list(self):
        """Verify ALARM_CONTEXT list."""
        self.assertEqual(len(self.c.ALARM_CONTEXT), 3)

    def test_probable_cause_list(self):
        """Verify ALARM_PROBABLE_CAUSE list has all entries."""
        self.assertGreater(len(self.c.ALARM_PROBABLE_CAUSE), 70)
        self.assertIn('software-error', self.c.ALARM_PROBABLE_CAUSE)
        self.assertIn('unknown', self.c.ALARM_PROBABLE_CAUSE)

    def test_client_commands(self):
        """Verify FM client command strings."""
        self.assertIn('fmClientCli', self.c.FM_CLIENT_SET_FAULT)
        self.assertIn('-c', self.c.FM_CLIENT_SET_FAULT)
        self.assertIn('-d', self.c.FM_CLIENT_CLEAR_FAULT)
        self.assertIn('-g', self.c.FM_CLIENT_GET_FAULT)

    def test_client_str_sep(self):
        """Verify separator constant."""
        self.assertEqual(self.c.FM_CLIENT_STR_SEP, "###")

    def test_alarm_attribute_indices(self):
        """Verify alarm attribute index constants."""
        self.assertEqual(self.c.FM_UUID_INDEX, 0)
        self.assertEqual(self.c.FM_ALARM_ID_INDEX, 1)
        self.assertEqual(self.c.FM_ALARM_STATE_INDEX, 2)
        self.assertEqual(self.c.FM_SEVERITY_INDEX, 6)
        self.assertEqual(self.c.MAX_ALARM_ATTRIBUTES, 14)

    def test_distributed_cloud_alarm_ids(self):
        """Verify distributed cloud alarm IDs."""
        self.assertTrue(
            self.c.FM_ALARM_ID_DC_SUBCLOUD_OFFLINE.startswith("280."))
        self.assertTrue(
            self.c.FM_ALARM_ID_DC_SUBCLOUD_RESOURCE_OUT_OF_SYNC
            .startswith("280."))

    def test_sw_mgmt_alarm_ids(self):
        """Verify software management alarm IDs."""
        self.assertTrue(
            self.c.FM_ALARM_ID_PATCH_IN_PROGRESS.startswith("900."))
        self.assertTrue(
            self.c.FM_ALARM_ID_UPGRADE_IN_PROGRESS.startswith("900."))

    def test_security_alarm_ids(self):
        """Verify security alarm IDs."""
        self.assertTrue(
            self.c.FM_ALARM_ID_TPM_INIT.startswith("500."))
        self.assertTrue(
            self.c.FM_ALARM_ID_CERT_EXPIRING_SOON.startswith("500."))

    def test_vm_alarm_ids(self):
        """Verify VM alarm IDs."""
        self.assertTrue(self.c.FM_ALARM_ID_VM_FAILED.startswith("700."))
        self.assertTrue(self.c.FM_ALARM_ID_VM_PAUSED.startswith("700."))
        val = self.c.FM_ALARM_ID_VM_STOPPED
        self.assertTrue(val.startswith("700."))

    def test_vm_log_ids(self):
        """Verify VM log IDs."""
        self.assertTrue(self.c.FM_LOG_ID_VM_ENABLED.startswith("700."))
        self.assertTrue(self.c.FM_LOG_ID_VM_FAILED.startswith("700."))
        self.assertTrue(self.c.FM_LOG_ID_VM_DELETED.startswith("700."))

    def test_storage_alarm_ids(self):
        """Verify storage alarm IDs."""
        self.assertTrue(
            self.c.FM_ALARM_ID_STORAGE_CEPH.startswith("800."))
        self.assertTrue(
            self.c.FM_ALARM_ID_STORAGE_CEPH_CRITICAL.startswith("800."))

    def test_application_alarm_ids(self):
        """Verify application alarm IDs."""
        self.assertTrue(
            self.c.FM_ALARM_ID_APPLICATION_UPLOAD_FAILED
            .startswith("750."))
        self.assertTrue(
            self.c.FM_ALARM_ID_APPLICATION_APPLY_FAILED
            .startswith("750."))

    def test_proposed_repair_actions(self):
        """Verify proposed repair action strings."""
        self.assertIn('host-kernel-modify',
                      self.c.FM_PRA_CONTROLLERS_KERNEL_MISMATCH)
        self.assertIn('host-kernel-modify',
                      self.c.FM_PRA_PROVISIONED_KERNEL_MISMATCH)

    def test_k8s_alarm_ids(self):
        """Verify Kubernetes alarm IDs."""
        self.assertTrue(
            self.c.FM_ALARM_ID_K8S_RESOURCE_PV.startswith("850."))
        self.assertTrue(
            self.c.FM_ALARM_ID_K8S_CLUSTER_DOWN.startswith("850."))

    def test_backup_restore_ids(self):
        """Verify backup/restore alarm and log IDs."""
        self.assertTrue(
            self.c.FM_ALARM_ID_BACKUP_IN_PROGRESS.startswith("210."))
        self.assertTrue(
            self.c.FM_LOG_ID_RESTORE_COMPLETE.startswith("210."))


if __name__ == '__main__':
    unittest.main()
