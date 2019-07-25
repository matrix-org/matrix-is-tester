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
