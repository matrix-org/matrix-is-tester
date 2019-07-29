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
from .fakehs import getSharedFakeHs


class TermsTest(unittest.TestCase):
    def setUp(self):
        self.fakeHs = getSharedFakeHs()
        self.fakeHsAddr = self.fakeHs.getAddr()

    def test_getTerms(self):
        baseUrl = getOrLaunchIS(True)
        api = IsApi(baseUrl, 'v2', None)
        
        body = api.getTerms()
        self.assertIn('policies', body)
        self.assertIn('privacy_policy', body['policies'])
        self.assertEquals(body['policies']['privacy_policy']['version'], '1.2')
        self.assertIn('en', body['policies']['privacy_policy'])
        self.assertIn('name', body['policies']['privacy_policy']['en'])
        self.assertIn('url', body['policies']['privacy_policy']['en'])
        self.assertIn('fr', body['policies']['privacy_policy'])
        self.assertIn('name', body['policies']['privacy_policy']['fr'])
        self.assertIn('url', body['policies']['privacy_policy']['fr'])

        self.assertIn('terms_of_service', body['policies'])
        self.assertEquals(body['policies']['terms_of_service']['version'], '5.0')
        self.assertIn('en', body['policies']['terms_of_service'])
        self.assertIn('name', body['policies']['terms_of_service']['en'])
        self.assertIn('url', body['policies']['terms_of_service']['en'])
        self.assertIn('fr', body['policies']['terms_of_service'])
        self.assertIn('name', body['policies']['terms_of_service']['fr'])
        self.assertIn('url', body['policies']['terms_of_service']['fr'])

    def test_agreeToTerms(self):
        baseUrl = getOrLaunchIS(True)
        api = IsApi(baseUrl, 'v2', None)
        api.makeAccount(self.fakeHsAddr)

        termsBody = api.getTerms()
        agreeBody = api.agreeToTerms([termsBody['policies']['privacy_policy']['en']['url']])
        self.assertEqual(agreeBody, {})

    def test_rejectIfNotAuthed(self):
        baseUrl = getOrLaunchIS(True)
        api = IsApi(baseUrl, 'v2', None)

        body = api.lookup('email', 'bob@example.com')
        self.assertEquals(body['errcode'], 'M_UNAUTHORIZED')

    def test_terms_rejectIfNoneAgreed(self):
        baseUrl = getOrLaunchIS(True)
        api = IsApi(baseUrl, 'v2', None)
        api.makeAccount(self.fakeHsAddr)

        body = api.lookup('email', 'bob@example.com')
        self.assertEquals(body['errcode'], 'M_TERMS_NOT_SIGNED')

    def test_terms_rejectIfNotAllAgreed(self):
        baseUrl = getOrLaunchIS(True)
        api = IsApi(baseUrl, 'v2', None)
        api.makeAccount(self.fakeHsAddr)

        termsBody = api.getTerms()
        api.agreeToTerms([termsBody['policies']['privacy_policy']['en']['url']])

        body = api.lookup('email', 'bob@example.com')
        self.assertEquals(body['errcode'], 'M_TERMS_NOT_SIGNED')

    def test_terms_allowWhenAllAgreed(self):
        baseUrl = getOrLaunchIS(True)
        api = IsApi(baseUrl, 'v2', None)
        api.makeAccount(self.fakeHsAddr)

        termsBody = api.getTerms()
        api.agreeToTerms([
            termsBody['policies']['privacy_policy']['en']['url'],
            termsBody['policies']['terms_of_service']['en']['url'],
        ])

        body = api.lookup('email', 'bob@example.com')
        self.assertEquals(body, {})

    def test_terms_allowMixedLangs(self):
        baseUrl = getOrLaunchIS(True)
        api = IsApi(baseUrl, 'v2', None)
        api.makeAccount(self.fakeHsAddr)

        termsBody = api.getTerms()
        api.agreeToTerms([
            termsBody['policies']['privacy_policy']['en']['url'],
            termsBody['policies']['terms_of_service']['fr']['url'],
        ])

        body = api.lookup('email', 'bob@example.com')
        self.assertEquals(body, {})

    def test_terms_allowInSeparateCalls(self):
        baseUrl = getOrLaunchIS(True)
        api = IsApi(baseUrl, 'v2', None)
        api.makeAccount(self.fakeHsAddr)

        termsBody = api.getTerms()
        api.agreeToTerms([termsBody['policies']['privacy_policy']['en']['url']])
        api.agreeToTerms([termsBody['policies']['terms_of_service']['en']['url']])

        body = api.lookup('email', 'bob@example.com')
        self.assertEquals(body, {})

    def test_terms_noTerms(self):
        baseUrl = getOrLaunchIS(False)
        api = IsApi(baseUrl, 'v2', None)
        api.makeAccount(self.fakeHsAddr)

        termsBody = api.getTerms()
        self.assertEquals(termsBody['policies'], {})

    def test_terms_allowIfNoTerms(self):
        baseUrl = getOrLaunchIS(False)
        api = IsApi(baseUrl, 'v2', None)
        api.makeAccount(self.fakeHsAddr)

        body = api.lookup('email', 'bob@example.com')
        self.assertEquals(body, {})

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    unittest.main()
