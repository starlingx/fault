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

import datetime
from fm.common import timeutils

from fm.tests import base


class FaultTimeUtilsTestCase(base.TestCase):

    def test_isotime(self):
        isotimestr = timeutils.isotime()
        isotime = timeutils.parse_isotime(isotimestr)
        self.assertTrue(isinstance(isotime, datetime.datetime))

        isotimestr = timeutils.isotime(subsecond=True)
        isotime = timeutils.parse_isotime(isotimestr)
        self.assertTrue(isinstance(isotime, datetime.datetime))

        self.assertRaises(ValueError, timeutils.parse_isotime, "bad input")
        self.assertRaises(ValueError, timeutils.parse_isotime, isotime)
