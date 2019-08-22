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

from .base_api_test import BaseApiTest
from .fakehs import getSharedFakeHs, tokenForUser


class V2Test(BaseApiTest, unittest.TestCase):
    API_VERSION = "v2"

    def setUp(self):
        super(V2Test, self).setUp()

        self.fakeHs = getSharedFakeHs()
        self.api.makeAccount(self.fakeHs.getAddr(), tokenForUser('@commonapitests:fake.test'))

    def test_bind_and_lookup(self):
        params = self.api.requestAndSubmitEmailCode("fakeemail3@nowhere.test")
        body = self.api.bindEmail(
            params["sid"], params["client_secret"], "@commonapitests:fake.test",
        )

        self.assertEquals(body["medium"], "email")
        self.assertEquals(body["address"], "fakeemail3@nowhere.test")
        self.assertEquals(body["mxid"], "@commonapitests:fake.test")

        hash_details = self.api.hash_details()

        lookupStr = "%s %s" % ("fakeemail3@nowhere.test", "email")
        body2 = self.api.hashed_lookup(
            [lookupStr], "none", hash_details["lookup_pepper"]
        )

        self.assertIn(lookupStr, body2["mappings"])
        self.assertEquals(body2["mappings"][lookupStr], "@commonapitests:fake.test")


if __name__ == "__main__":
    import sys
    from twisted.python import log

    log.startLogging(sys.stdout)
    unittest.main()
