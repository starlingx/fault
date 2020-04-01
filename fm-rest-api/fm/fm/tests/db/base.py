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

"""Fault DB test base class."""

import abc
import six

from fm.common import context
from fm.tests import base

INIT_VERSION = 0


@six.add_metaclass(abc.ABCMeta)
class DbTestCase(base.TestCase):

    def setUp(self):
        super(DbTestCase, self).setUp()
        self.admin_context = context.make_context(is_admin=True)
