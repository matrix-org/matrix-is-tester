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

import requests
import random
import string
import re

from twisted.python import log

from .fakehs import tokenForRandomUser

class IsApi(object):
    def __init__(self, baseUrl, version, mailSink):
        self.headers = None

        self.version = version
        if version == 'v1':
            self.apiRoot = baseUrl + '/_matrix/identity/api/v1';
        elif version == 'v2':
            self.apiRoot = baseUrl + '/_matrix/identity/v2';
        else:
            raise Exception("Invalid version: %s" % (version,))

        self.mailSink = mailSink

    # Uses the /register API to create an account. This account will be used for all subsequent
    # API calls that requrie auth.
    def makeAccount(self, hsAddr, openidToken=None):
        if self.version != 'v2':
            raise Exception("Only v2 supports authentication")

        if openidToken == None:
            openidToken = tokenForRandomUser()

        body = self.register(':'.join([str(x) for x in hsAddr]), openidToken)
        self.headers = {'Authorization': 'Bearer %s' % (body['access_token'],)}

    def getTokenFromMail(self):
        mail = self.mailSink.getMail()

        log.msg("Got email: %r", mail)
        if 'data' not in mail:
            raise Exception("Mail has no 'data'")
        matches = re.match(r"<<<(.*)>>>", mail['data'])
        if not matches.group(1):
            raise Exception("Failed to match token from mail")

        return matches.group(1)

    def ping(self):
        resp = requests.get(self.apiRoot)
        return resp.json()

    def requestEmailCode(self, address, clientSecret, sendAttempt):
        resp = requests.post(
            self.apiRoot + '/validate/email/requestToken',
            json={
                'client_secret': clientSecret,
                'email': address,
                'send_attempt': sendAttempt,
            },
            headers=self.headers,
        )
        return resp.json()

    def submitEmailTokenViaGet(self, sid, clientSecret, token):
        resp = requests.get(
            self.apiRoot + '/validate/email/submitToken',
            params={
                'client_secret': clientSecret,
                'sid': sid,
                'token': token,
            },
            headers=self.headers,
        )
        return resp.content

    def requestAndSubmitEmailCode(self, address):
        clientSecret = "".join([random.choice(string.digits) for _ in range(16)])
        reqResponse = self.requestEmailCode(address, clientSecret, 1)

        token = self.getTokenFromMail()

        sid = reqResponse['sid']
        resp = requests.post(
            self.apiRoot + '/validate/email/submitToken',
            json={
                'client_secret': clientSecret,
                'sid': sid,
                'token': token,
            },
            headers=self.headers,
        )
        body = resp.json()
        log.msg("submitToken returned %r", body)
        if not body['success']:
            raise Exception("Submit token failed")
        return {'sid': sid, 'client_secret': clientSecret}

    def bindEmail(self, sid, clientSecret, mxid):
        resp = requests.post(
            self.apiRoot + '/3pid/bind',
            json={
                'client_secret': clientSecret,
                'sid': sid,
                'mxid': mxid,
            },
            headers=self.headers,
        )
        return resp.json()

    def lookup(self, medium, address):
        resp = requests.get(
            self.apiRoot + '/lookup',
            params={
                'medium': medium,
                'address': address,
            },
            headers=self.headers,
        )
        return resp.json()

    def bulkLookup(self, threepids):
        resp = requests.post(
            self.apiRoot + '/bulk_lookup',
            json={
                'threepids': threepids,
            },
            headers=self.headers,
        )
        return resp.json()
        
    def getValidatedThreepid(self, sid, clientSecret):
        resp = requests.get(
            self.apiRoot + '/3pid/getValidated3pid',
            params={
                'sid': sid,
                'client_secret': clientSecret,
            },
            headers=self.headers,
        )
        return resp.json()

    def storeInvite(self, params):
        resp = requests.post(
            self.apiRoot + '/store-invite',
            json=params,
            headers=self.headers,
        )
        return resp.json()

    def pubkeyIsValid(self, url, pubkey):
        resp = requests.get(
            url,
            params={
                'public_key': pubkey,
            },
        )
        return resp.json()

    def getTerms(self):
        resp = requests.get(
            self.apiRoot + '/terms',
        )
        return resp.json()

    def agreeToTerms(self, userAccepts):
        resp = requests.post(
            self.apiRoot + '/terms',
            json={
                'user_accepts': userAccepts,
            },
            headers=self.headers,
        )
        return resp.json()

    def register(self, matrixServerName, accessToken):
        resp = requests.post(
            self.apiRoot + '/account/register',
            json={
                'matrix_server_name': matrixServerName,
                'access_token': accessToken,
            },
        )
        return resp.json()

    def account(self):
        resp = requests.get(
            self.apiRoot + '/account',
            headers=self.headers,
        )
        return resp.json()

    def logout(self):
        resp = requests.post(
            self.apiRoot + '/account/logout',
            headers=self.headers,
        )
        return resp.json()
