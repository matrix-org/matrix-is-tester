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

import re
import sys
import unittest

import requests
from twisted.python import log

from matrix_is_tester.launch_is import get_or_launch_is
from matrix_is_tester.mailsink import MailSink


class IsApiTest(unittest.TestCase):
    def setUp(self):
        self.baseUrl = get_or_launch_is()

        self.mailsink = MailSink()
        self.mailsink.launch()

    def tearDown(self):
        self.mailsink.tearDown()

    def test_v1ping(self):
        resp = requests.get(self.baseUrl + "/_matrix/identity/api/v1")
        self.assertEquals(resp.json(), {})

    def test_request_email_code(self):
        resp = requests.post(
            self.baseUrl + "/_matrix/identity/api/v1/validate/email/requestToken",
            json={
                "client_secret": "sshitsasecret",
                "email": "fakeemail@nowhere.test",
                "send_attempt": 1,
            },
        )
        body = resp.json()
        log.msg("Got response %r", body)
        self.assertIn("sid", body)

    def test_submit_email_code(self):
        resp = requests.post(
            self.baseUrl + "/_matrix/identity/api/v1/validate/email/requestToken",
            json={
                "client_secret": "sosecret",
                "email": "fakeemail@nowhere.test",
                "send_attempt": 1,
            },
        )
        body = resp.json()
        log.msg("Got response %r", body)
        self.assertIn("sid", body)

        mail = self.mailsink.get_mail()
        log.msg("Got email: %r", mail)
        self.assertIn("data", mail)

        matches = re.match(r"<<<(.*)>>>", mail["data"])
        self.assertTrue(matches.group(1))
        token = matches.group(1)

        log.msg("Token is %s", token)

        sid = body["sid"]
        resp = requests.post(
            self.baseUrl + "/_matrix/identity/api/v1/validate/email/submitToken",
            json={"client_secret": "sosecret", "sid": sid, "token": token},
        )
        body = resp.json()
        log.msg("submitToken returned %r", body)
        self.assertTrue(body["success"])


if __name__ == "__main__":
    log.startLogging(sys.stdout)
    unittest.main()
