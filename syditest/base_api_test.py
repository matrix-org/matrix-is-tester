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
import json
import random

# These are standard python unit tests, but are generally intended
# to be run with trial. Trial doesn't capture logging nicely if you
# use python 'logging': it only works if you use Twisted's own.
from twisted.python import log


from .is_api import IsApi
from .launch_is import getOrLaunchIS
from .mailsink import MailSink

# Not a test case itself, but can be subclassed to test APIs common
# between versions. Subclasses provide self.api
class BaseApiTest():
    def setUp(self):
        self.baseUrl = getOrLaunchIS()

        self.mailSink = MailSink()
        self.mailSink.launch()

        self.api = IsApi(self.baseUrl, self.API_VERSION, self.mailSink)

        random.seed(1)

    def tearDown(self):
        self.mailSink.tearDown()

    def test_v1ping(self):
        body = self.api.ping()
        self.assertEquals(body, {})

    def test_requestEmailCode(self):
        body = self.api.requestEmailCode('fakeemail1@nowhere.test', 'sekrit', 1)
        log.msg("Got response %r", body)
        self.assertIn('sid', body)

    def test_rejectInvalidEmail(self):
        body = self.api.requestEmailCode('fakeemail1@nowhere.test@elsewhere.test', 'sekrit', 1)
        self.assertEquals(body['errcode'], 'M_INVALID_EMAIL')

    def test_submitEmailCode(self):
        self.api.requestAndSubmitEmailCode('fakeemail2@nowhere.test')

    def test_submitEmailCodeGet(self):
        reqResponse = self.api.requestEmailCode('steve@nowhere.test', 'verysekrit', 1)
        sid = reqResponse['sid']

        token = self.api.getTokenFromMail()

        body = self.api.submitEmailTokenViaGet(sid, 'verysekrit', token)
        self.assertEquals(body, 'syditest:email_submit_get_response\n')

        body = self.api.getValidatedThreepid(sid, 'verysekrit')

        self.assertEquals(body['medium'], 'email')
        self.assertEquals(body['address'], 'steve@nowhere.test')

    def test_bind_and_lookup(self):
        params = self.api.requestAndSubmitEmailCode('fakeemail3@nowhere.test')
        body = self.api.bindEmail(params['sid'], params['client_secret'], '@some_mxid:fake.test')

        self.assertEquals(body['medium'], 'email')
        self.assertEquals(body['address'], "fakeemail3@nowhere.test")
        self.assertEquals(body['mxid'], "@some_mxid:fake.test")

        body2 = self.api.lookup('email', "fakeemail3@nowhere.test")

        self.assertEquals(body2['medium'], 'email')
        self.assertEquals(body2['address'], 'fakeemail3@nowhere.test')
        self.assertEquals(body2['mxid'], '@some_mxid:fake.test')

        self.assertEquals(body['ts'], body2['ts'])
        self.assertEquals(body['not_before'], body2['not_before'])
        self.assertEquals(body['not_after'], body2['not_after'])

    def test_bind_toBadMxid(self):
        raise unittest.SkipTest("sydent allows this currently")
        params = self.api.requestAndSubmitEmailCode('perfectly_valid_email@nowhere.test')
        body = self.api.bindEmail(params['sid'], params['client_secret'], 'not a valid mxid')
        self.assertEquals(body['errcode'], 'M_INVALID_PARAM')

    def test_unverified_bind(self):
        reqCodeBody = self.api.requestEmailCode('fakeemail5@nowhere.test', 'sekrit', 1)
        body = self.api.bindEmail(reqCodeBody['sid'], 'sekrit', '@thing1:fake.test')
        self.assertEquals(body['errcode'], 'M_SESSION_NOT_VALIDATED')

    def test_bulk_lookup(self):
        params = self.api.requestAndSubmitEmailCode('thing1@nowhere.test')
        body = self.api.bindEmail(params['sid'], params['client_secret'], '@thing1:fake.test')

        params = self.api.requestAndSubmitEmailCode('thing2@nowhere.test')
        body = self.api.bindEmail(params['sid'], params['client_secret'], '@thing2:fake.test')

        body = self.api.bulkLookup([
            ('email', 'thing1@nowhere.test'),
            ('email', 'thing2@nowhere.test'),
            ('email', 'thing3@nowhere.test'),
        ])

        self.assertIn(['email', 'thing1@nowhere.test', '@thing1:fake.test'], body['threepids'])
        self.assertIn(['email', 'thing2@nowhere.test', '@thing2:fake.test'], body['threepids'])
        self.assertEquals(len(body['threepids']), 2)

    def test_getValidatedThreepid(self):
        params = self.api.requestAndSubmitEmailCode('fakeemail4@nowhere.test')

        body = self.api.getValidatedThreepid(params['sid'], params['client_secret'])

        self.assertEquals(body['medium'], 'email')
        self.assertEquals(body['address'], 'fakeemail4@nowhere.test')

    def test_getValidatedThreepid_notValidated(self):
        reqCodeBody = self.api.requestEmailCode('fakeemail5@nowhere.test', 'sekrit', 1)

        getValBody = self.api.getValidatedThreepid(reqCodeBody['sid'], 'sekrit')
        self.assertEquals(getValBody['errcode'], 'M_SESSION_NOT_VALIDATED')

    def test_storeInvite(self):
        body = self.api.storeInvite({
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
            isValidBody = self.api.pubkeyIsValid(k['key_validity_url'], k['public_key'])
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
        params = self.api.requestAndSubmitEmailCode('already_here@fake.test')
        self.api.bindEmail(params['sid'], params['client_secret'], '@some_mxid:fake.test')

        body = self.api.storeInvite({
            'medium': 'email',
            'address': 'already_here@fake.test',
            'room_id': '$aroom:fake.test',
            'sender': '@sender:fake.test',
        })
        self.assertEquals(body['errcode'], 'THREEPID_IN_USE')
