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

import BaseHTTPServer

import os
import json
import ssl
import random
from multiprocessing import Process


random.seed(1)

class FakeHomeserverRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/_matrix/federation/v1/openid/userinfo'):
            userid = random.randint(0, 2**32)
            resp = json.dumps({
                'sub': '@user%d:localhost:4490' % (userid,),
            })

            self.send_response(200)
            self.send_header('Content-Length', len(resp))
            self.end_headers()

            self.wfile.write(resp)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write('Not found')

    def log_message(self, fmt, *args):
        # don't print to stdout: it screws up the test output (and we don't really care)
        return

def runHttpServer():
    certFile = os.path.join(os.path.dirname(__file__), 'fakehs.pem')

    httpd = BaseHTTPServer.HTTPServer(('localhost', 4490), FakeHomeserverRequestHandler)
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile=certFile, server_side=True)
    httpd.serve_forever()

class FakeHomeserver(object):
    def launch(self):
        self.process = Process(target=runHttpServer)
        self.process.start()
        return ('localhost', 4490)

    def tearDown(self):
        self.process.terminate()

if __name__ == '__main__':
    fakehs = FakeHomeserver()
    fakehs.launch()
