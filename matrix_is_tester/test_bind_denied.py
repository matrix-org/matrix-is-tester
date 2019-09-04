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

from matrix_is_tester.fakehs import get_shared_fake_hs, token_for_user
from matrix_is_tester.is_api import IsApi
from matrix_is_tester.launch_is import get_or_launch_is
from matrix_is_tester.mailsink import get_shared_mailsink


class AccountTest(unittest.TestCase):
    def setUp(self):
        self.fakeHs = get_shared_fake_hs()
        self.fakeHsAddr = self.fakeHs.get_addr()
        self.mailSink = get_shared_mailsink()

    def test_bind_notYourMxid(self):
        baseUrl = get_or_launch_is(False)
        api = IsApi(baseUrl, "v2", self.mailSink)
        api.make_account(self.fakeHsAddr, token_for_user("@bob:fake.test"))

        params = api.request_and_submit_email_code("perfectly_valid_email@nowhere.test")
        body = api.bind_email(
            params["sid"], params["client_secret"], "@alice:fake.test"
        )
        self.assertEquals(body["errcode"], "M_UNAUTHORIZED")


if __name__ == "__main__":
    import sys
    from twisted.python import log

    log.startLogging(sys.stdout)
    unittest.main()
