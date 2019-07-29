#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright 2019 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from .is_api import IsApi
from .launch_is import getOrLaunchIS
from .mailsink import getSharedMailSink
from .fakehs import getSharedFakeHs, tokenForUser


class AccountTest(unittest.TestCase):
    def setUp(self):
        self.fakeHs = getSharedFakeHs()
        self.fakeHsAddr = self.fakeHs.getAddr()
        self.mailSink = getSharedMailSink()

    def test_bind_notYourMxid(self):
        baseUrl = getOrLaunchIS(False)
        api = IsApi(baseUrl, 'v2', self.mailSink)
        api.makeAccount(self.fakeHsAddr, tokenForUser('@bob:fake.test'))

        params = api.requestAndSubmitEmailCode('perfectly_valid_email@nowhere.test')
        body = api.bindEmail(params['sid'], params['client_secret'], '@alice:fake.test')
        self.assertEquals(body['errcode'], 'M_UNAUTHORIZED')

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    unittest.main()
