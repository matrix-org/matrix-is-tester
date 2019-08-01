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

import asyncore
import smtpd
from multiprocessing import Process, Queue


class MailSinkSmtpServer(smtpd.SMTPServer):
    def __init__(self, localaddr, remoteaddr, q):
        smtpd.SMTPServer.__init__(self, localaddr, remoteaddr)
        self.queue = q

    def process_message(self, peer, mailfrom, rctpto, data):
        self.queue.put({
            'peer': peer,
            'mailfrom': mailfrom,
            'rctpto': rctpto,
            'data': data,
        })


def runMailSink(q):
    MailSinkSmtpServer(('127.0.0.1', 1025), None, q)
    asyncore.loop()


class MailSink(object):
    def launch(self):
        self.queue = Queue()
        self.process = Process(target=runMailSink, args=(self.queue,))
        self.process.start()

    def getMail(self):
        return self.queue.get()

    def tearDown(self):
        self.process.terminate()


if __name__ == '__main__':
    ms = MailSink()
    ms.launch()
    print("%r" % (ms.getMail(),))
    ms.tearDown()
