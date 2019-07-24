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
import requests
import re
import sys
import atexit
import random
import string
import json

# These are standard python unit tests, but are generally intended
# to be run with trial. Trial doesn't capture logging nicely if you
# use python 'logging': it only works if you use Twisted's own.
from twisted.python import log

from .mailsink import MailSink

try:
    from syditest_subject.launcher import SyditestLauncher
except ImportError:
    print("ERROR: Couldn't import launcher")
    print(
        "syditest needs an identity server to test: make sure, "
        "'syditest_subject.launcher.SyditestLauncher' is in "
        "sys.path"
    )
    
    raise

launcher = None
baseUrl = None

def getOrLaunchIS():
    global launcher
    global baseUrl

    if launcher is not None:
        return baseUrl

    launcher = SyditestLauncher()
    baseUrl = launcher.launch()

    atexit.register(destroyIS)

    return baseUrl

def destroyIS():
    global launcher

    if launcher is not None:
        launcher.tearDown()
    

class IsApiTest(unittest.TestCase):
    def setUp(self):
        self.baseUrl = getOrLaunchIS()

        self.mailSink = MailSink()
        self.mailSink.launch()

        random.seed(1)

    def tearDown(self):
        self.mailSink.tearDown()

    def _requestEmailCode(self, address, clientSecret, sendAttempt):
        resp = requests.post(
            self.baseUrl + '/_matrix/identity/api/v1/validate/email/requestToken',
            json={
                'client_secret': clientSecret,
                'email': address,
                'send_attempt': sendAttempt,
            },
        )
        return resp.json()

    def _getTokenFromMail(self):
        mail = self.mailSink.getMail()

        log.msg("Got email: %r", mail)
        self.assertIn('data', mail)
        matches = re.match(r"<<<(.*)>>>", mail['data'])
        self.assertTrue(matches.group(1))
        return matches.group(1)

    def _requestAndSubmitEmailCode(self, address):
        clientSecret = "".join([random.choice(string.digits) for _ in range(16)])
        reqResponse = self._requestEmailCode(address, clientSecret, 1)

        token = self._getTokenFromMail()

        sid = reqResponse['sid']
        resp = requests.post(
            self.baseUrl + '/_matrix/identity/api/v1/validate/email/submitToken',
            json={
                'client_secret': clientSecret,
                'sid': sid,
                'token': token,
            },
        )
        body = resp.json()
        log.msg("submitToken returned %r", body)
        self.assertTrue(body['success'])
        return {'sid': sid, 'client_secret': clientSecret}

    def _bindEmail(self, sid, clientSecret, mxid):
        resp = requests.post(
            self.baseUrl + '/_matrix/identity/api/v1/3pid/bind',
            json={
                'client_secret': clientSecret,
                'sid': sid,
                'mxid': mxid,
            },
        )
        return resp.json()

    def _lookup(self, medium, address):
        resp = requests.get(
            self.baseUrl + '/_matrix/identity/api/v1/lookup',
            params={
                'medium': medium,
                'address': address,
            },
        )
        return resp.json()

    def _bulkLookup(self, threepids):
        resp = requests.post(
            self.baseUrl + '/_matrix/identity/api/v1/bulk_lookup',
            json={
                'threepids': threepids,
            },
        )
        return resp.json()
        
    def _getValidatedThreepid(self, sid, clientSecret):
        resp = requests.get(
            self.baseUrl + '/_matrix/identity/api/v1/3pid/getValidated3pid',
            params={
                'sid': sid,
                'client_secret': clientSecret,
            },
        )
        return resp.json()

    def _storeInvite(self, params):
        resp = requests.post(
            self.baseUrl + '/_matrix/identity/api/v1/store-invite',
            json=params,
        )
        return resp.json()

    def _pubkeyIsValid(self, url, pubkey):
        resp = requests.get(
            url,
            params={
                'public_key': pubkey,
            },
        )
        return resp.json()

    def test_v1ping(self):
        resp = requests.get(self.baseUrl + '/_matrix/identity/api/v1')
        self.assertEquals(resp.json(), {})

    def test_requestEmailCode(self):
        body = self._requestEmailCode('fakeemail1@nowhere.test', 'sekrit', 1)
        log.msg("Got response %r", body)
        self.assertIn('sid', body)

    def test_rejectInvalidEmail(self):
        body = self._requestEmailCode('fakeemail1@nowhere.test@elsewhere.test', 'sekrit', 1)
        self.assertEquals(body['errcode'], 'M_INVALID_EMAIL')

    def test_submitEmailCode(self):
        self._requestAndSubmitEmailCode('fakeemail2@nowhere.test')

    def test_submitEmailCodeGet(self):
        reqResponse = self._requestEmailCode('steve@nowhere.test', 'verysekrit', 1)
        sid = reqResponse['sid']

        token = self._getTokenFromMail()

        resp = requests.get(
            self.baseUrl + '/_matrix/identity/api/v1/validate/email/submitToken',
            params={
                'client_secret': 'verysekrit',
                'sid': sid,
                'token': token,
            },
        )
        self.assertEquals(resp.content, 'syditest:email_submit_get_response\n')

        body = self._getValidatedThreepid(sid, 'verysekrit')

        self.assertEquals(body['medium'], 'email')
        self.assertEquals(body['address'], 'steve@nowhere.test')

    def test_bind_and_lookup(self):
        params = self._requestAndSubmitEmailCode('fakeemail3@nowhere.test')
        body = self._bindEmail(params['sid'], params['client_secret'], '@some_mxid:fake.test')

        self.assertEquals(body['medium'], 'email')
        self.assertEquals(body['address'], "fakeemail3@nowhere.test")
        self.assertEquals(body['mxid'], "@some_mxid:fake.test")

        body2 = self._lookup('email', "fakeemail3@nowhere.test")

        self.assertEquals(body2['medium'], 'email')
        self.assertEquals(body2['address'], 'fakeemail3@nowhere.test')
        self.assertEquals(body2['mxid'], '@some_mxid:fake.test')

        self.assertEquals(body['ts'], body2['ts'])
        self.assertEquals(body['not_before'], body2['not_before'])
        self.assertEquals(body['not_after'], body2['not_after'])

    def test_bind_toBadMxid(self):
        raise unittest.SkipTest("sydent allows this currently")
        params = self._requestAndSubmitEmailCode('perfectly_valid_email@nowhere.test')
        body = self._bindEmail(params['sid'], params['client_secret'], 'not a valid mxid')
        self.assertEquals(body['errcode'], 'M_INVALID_PARAM')

    def test_unverified_bind(self):
        reqCodeBody = self._requestEmailCode('fakeemail5@nowhere.test', 'sekrit', 1)
        body = self._bindEmail(reqCodeBody['sid'], 'sekrit', '@thing1:fake.test')
        self.assertEquals(body['errcode'], 'M_SESSION_NOT_VALIDATED')

    def test_bulk_lookup(self):
        params = self._requestAndSubmitEmailCode('thing1@nowhere.test')
        body = self._bindEmail(params['sid'], params['client_secret'], '@thing1:fake.test')

        params = self._requestAndSubmitEmailCode('thing2@nowhere.test')
        body = self._bindEmail(params['sid'], params['client_secret'], '@thing2:fake.test')

        body = self._bulkLookup([
            ('email', 'thing1@nowhere.test'),
            ('email', 'thing2@nowhere.test'),
            ('email', 'thing3@nowhere.test'),
        ])

        self.assertIn(['email', 'thing1@nowhere.test', '@thing1:fake.test'], body['threepids'])
        self.assertIn(['email', 'thing2@nowhere.test', '@thing2:fake.test'], body['threepids'])
        self.assertEquals(len(body['threepids']), 2)

    def test_getValidatedThreepid(self):
        params = self._requestAndSubmitEmailCode('fakeemail4@nowhere.test')

        body = self._getValidatedThreepid(params['sid'], params['client_secret'])

        self.assertEquals(body['medium'], 'email')
        self.assertEquals(body['address'], 'fakeemail4@nowhere.test')

    def test_getValidatedThreepid_notValidated(self):
        reqCodeBody = self._requestEmailCode('fakeemail5@nowhere.test', 'sekrit', 1)

        getValBody = self._getValidatedThreepid(reqCodeBody['sid'], 'sekrit')
        self.assertEquals(getValBody['errcode'], 'M_SESSION_NOT_VALIDATED')

    def test_storeInvite(self):
        body = self._storeInvite({
            'medium': 'email',
            'address': 'ian@fake.test',
            'room_id': '$aroom:fake.test',
            'sender': '@sender:fake.test',
            'room_alias': '#alias:fake.test',
            'room_avatar_url': 'mxc://fake.test/roomavatar',
            'room_name': 'my excellent room',
            'sender_display_name': 'Ian Sender',
            'sender_avatar_url': 'mxc://fake.test/iansavatar',
        })
        self.assertGreater(len(body['token']), 0)
        # must be redacted
        self.assertNotEqual(body['display_name'], 'ian@fake.test')
        self.assertGreater(len(body['public_keys']), 0)

        for k in body['public_keys']:
            isValidBody = self._pubkeyIsValid(k['key_validity_url'], k['public_key'])
            self.assertTrue(isValidBody['valid'])

        mail = self.mailSink.getMail()
        mailObject = json.loads(mail['data'])
        self.assertEquals(mailObject['token'], body['token'])
        self.assertEquals(mailObject['room_alias'], '#alias:fake.test')
        self.assertEquals(mailObject['room_avatar_url'], 'mxc://fake.test/roomavatar')
        self.assertEquals(mailObject['room_name'], 'my excellent room')
        self.assertEquals(mailObject['sender_display_name'], 'Ian Sender')
        self.assertEquals(mailObject['sender_avatar_url'], 'mxc://fake.test/iansavatar')

    def test_storeInvite_boundThreepid(self):
        params = self._requestAndSubmitEmailCode('already_here@fake.test')
        self._bindEmail(params['sid'], params['client_secret'], '@some_mxid:fake.test')

        body = self._storeInvite({
            'medium': 'email',
            'address': 'already_here@fake.test',
            'room_id': '$aroom:fake.test',
            'sender': '@sender:fake.test',
        })
        self.assertEquals(body['errcode'], 'THREEPID_IN_USE')

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    unittest.main()
