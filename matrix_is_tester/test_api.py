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

import atexit
import re
import sys
import unittest

# These are standard python unit tests, but are generally intended
# to be run with trial. Trial doesn't capture logging nicely if you
# use python 'logging': it only works if you use Twisted's own.
from twisted.python import log

import requests
from matrix_is_tester.mailsink import MailSink

try:
    from matrix_is_test.launcher import MatrixIsTestLauncher
except ImportError:
    print("ERROR: Couldn't import launcher")
    print(
        "matrix_is_tester needs an identity server to test: make sure, "
        "'matrix_is_test.launcher.MatrixIsTestLauncher' is in "
        "sys.path"
    )

    raise

launcher = None
baseUrl = None


def _getOrLaunchIS():
    global launcher
    global baseUrl

    if launcher is not None:
        return baseUrl

    launcher = MatrixIsTestLauncher()
    baseUrl = launcher.launch()

    atexit.register(destroyIS)

    return baseUrl


def destroyIS():
    global launcher

    if launcher is not None:
        launcher.tearDown()


class IsApiTest(unittest.TestCase):
    def setUp(self):
        self.baseUrl = _getOrLaunchIS()

        self.mailSink = MailSink()
        self.mailSink.launch()

    def tearDown(self):
        self.mailSink.tearDown()

    def test_v1ping(self):
        resp = requests.get(self.baseUrl + '/_matrix/identity/api/v1')
        self.assertEquals(resp.json(), {})

    def test_requestEmailCode(self):
        resp = requests.post(
            self.baseUrl + '/_matrix/identity/api/v1/validate/email/requestToken',
            json={
                'client_secret': "sshitsasecret",
                'email': "fakeemail@nowhere.test",
                'send_attempt': 1,
            },
        )
        body = resp.json()
        log.msg("Got response %r", body)
        self.assertIn('sid', body)

    def test_submitEmailCode(self):
        resp = requests.post(
            self.baseUrl + '/_matrix/identity/api/v1/validate/email/requestToken',
            json={
                'client_secret': "sosecret",
                'email': "fakeemail@nowhere.test",
                'send_attempt': 1,
            },
        )
        body = resp.json()
        log.msg("Got response %r", body)
        self.assertIn('sid', body)

        mail = self.mailSink.getMail()
        log.msg("Got email: %r", mail)
        self.assertIn('data', mail)

        matches = re.match(r"<<<(.*)>>>", mail['data'])
        self.assertTrue(matches.group(1))
        token = matches.group(1)

        log.msg("Token is %s", token)

        sid = body['sid']
        resp = requests.post(
            self.baseUrl + '/_matrix/identity/api/v1/validate/email/submitToken',
            json={
                'client_secret': "sosecret",
                'sid': sid,
                'token': token,
            },
        )
        body = resp.json()
        log.msg("submitToken returned %r", body)
        self.assertTrue(body['success'])


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    unittest.main()
