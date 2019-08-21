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
    from matrix_is_test.launcher import MatrixIsTestLauncher
except ImportError:
    print("ERROR: Couldn't import launcher")
    print(
        "matrix_is_tester needs an identity server to test: make sure, "
        "'matrix_is_test.launcher.MatrixIsTestLauncher' is in "
        "sys.path"
    )

    raise

launchers = {}


def getOrLaunchIS(withTerms=False):
    global launchers

    key = 'withTerms' if withTerms else 'noTerms'

    if key not in launchers:
        if not launchers:
            atexit.register(destroyAll)

        launchers[key] = MatrixIsTestLauncher(withTerms)
        launchers[key].launch()

    return launchers[key].get_base_url()


def destroyAll():
    global launchers

    for launcher in launchers.values():
        launcher.tearDown()
