# Copyright 2020 Intel Corporation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from fm.common import utils
from fm.tests import base


class FaultUtilsTestCase(base.TestCase):

    def test_generate_uuid(self):
        uuid = utils.generate_uuid()
        self.assertTrue(isinstance(uuid, str))

    def test_safe_rstrip(self):
        input_int = 1
        self.assertEqual(input_int, utils.safe_rstrip(input_int))
        input_str = "string input"
        self.assertEqual(input_str, utils.safe_rstrip(input_str))

        input_str = "string to strip   \r\n\t"
        output_str = "string to strip"
        self.assertEqual(output_str, utils.safe_rstrip(input_str))

        input_str = "string to strip ssss"
        output_str = "string to strip"
        self.assertEqual(output_str, utils.safe_rstrip(input_str, "s "))
