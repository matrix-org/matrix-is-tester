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
import base64
import BaseHTTPServer
import json
import os
import random
import ssl
import urlparse
from multiprocessing import Process

random.seed(1)

sharedFakeHs = None


def tokenForRandomUser():
    num = random.randint(0, 2 ** 32)
    userId = "@user%d:localhost:4490" % (num,)
    return "user:%s" % (base64.b64encode(userId),)


def tokenForUser(userId):
    return "user:%s" % (base64.b64encode(userId),)


def getSharedFakeHs():
    global sharedFakeHs
    if sharedFakeHs is None:
        sharedFakeHs = FakeHomeserver()
        sharedFakeHs.launch()
        atexit.register(destroyShared)
    return sharedFakeHs


def destroyShared():
    sharedFakeHs.tearDown()


class FakeHomeserverRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/_matrix/federation/v1/openid/userinfo"):
            parsed = urlparse.urlparse(self.path)
            params = urlparse.parse_qs(parsed.query)

            token = params["access_token"][0]

            if token.startswith("user:"):
                userid = base64.b64decode(token.split(":")[1])
            else:
                resp = json.dumps(
                    {
                        "errcode": "M_UNKNOWN_TOKEN",
                        "error": "Not a valid token: try again.",
                    }
                )
                self.send_response(401)
                self.send_header("Content-Length", len(resp))
                self.end_headers()

                self.wfile.write(resp)

            resp = json.dumps({"sub": userid})

            self.send_response(200)
            self.send_header("Content-Length", len(resp))
            self.end_headers()

            self.wfile.write(resp)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write("Not found")

    def log_message(self, fmt, *args):
        # don't print to stdout: it screws up the test output (and we don't really care)
        return


def runHttpServer():
    certFile = os.path.join(os.path.dirname(__file__), "fakehs.pem")

    httpd = BaseHTTPServer.HTTPServer(("localhost", 4490), FakeHomeserverRequestHandler)
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile=certFile, server_side=True)
    httpd.serve_forever()


class FakeHomeserver(object):
    def launch(self):
        self.process = Process(target=runHttpServer)
        self.process.start()

    def getAddr(self):
        return ("localhost", 4490)

    def tearDown(self):
        self.process.terminate()


if __name__ == "__main__":
    fakehs = FakeHomeserver()
    fakehs.launch()