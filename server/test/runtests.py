# Copyright 2019 Evgeny Golyshev. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

import fakeredis
import subprocess
import sqlalchemy as sa  # Tests are running synchronously so we have to use sqlalchemy instead of gino.
import testing.postgresql
from aiologger import Logger
from tornado.ioloop import IOLoop
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

from huntflow_reloaded import handler, scheduler, models
from huntflow_reloaded.models import Candidate, Interview
from test import stubs


ACCOUNT = """
    "account": {
        "id": 1,
        "name": "Noname"
    }
"""

CREATED_DATE = "1989-12-17T00:00:00+00:00"

POSTGRES_URL = "postgresql://postgres:@localhost:5432/test"

def compose(req):
    return (req.replace('%ACCOUNT%', ACCOUNT)
               .replace('%CREATED_DATE%', CREATED_DATE))


class WebTestCase(AsyncHTTPTestCase):
    """Base class for web tests that also supports WSGI mode.

    Override get_handlers and get_app_kwargs instead of get_app.
    Append to wsgi_safe to have it run in wsgi_test as well.
    Override get_new_ioloop to avoid creating a new loop for each test case.
    The code was borrowed from the original Tornado tests.
    """
    def get_app(self):
        self.app = Application(self.get_handlers(), **self.get_app_kwargs())
        return self.app

    def setUp(self):
        super(WebTestCase, self).setUp()
        self._mock_postgres = testing.postgresql.Postgresql(port=5432)

        command = 'server/alembic/migrate.sh ' + POSTGRES_URL
        subprocess.Popen(command, shell=True).wait()

        engine = sa.create_engine(POSTGRES_URL)
        self.conn = engine.connect()

    def get_handlers(self):
        raise NotImplementedError()

    def get_app_kwargs(self):
        return {}

    def get_new_ioloop(self):
        return IOLoop.current()

    def tearDown(self):
        super(WebTestCase, self).tearDown()

        for table in (Interview, Candidate):
            self.conn.execute(table.delete)

        self.conn.close()
        self._mock_postgres.stop()

class HuntflowWebhookHandlerTest(WebTestCase):
    def get_handlers(self):
        conn = fakeredis.FakeStrictRedis()
        logger = Logger.with_default_handlers()
        args = {
            'logger': logger,
            'postgres': {
                'dbname': 'test',
                'hostname': 'localhost',
                'password': '',
                'port': '5432',
                'username': 'postgres',
            },
            'redis_conn': conn,
            'channel_name': 'stub',
        }
        return [
            ('/hf', handler.HuntflowWebhookHandler, args),
        ]

    def test_broken_request(self):
        response = self.fetch('/hf', body='hello', method='POST')
        self.assertEqual(response.code, 500)
        self.assertEqual(response.body, b'Could not decode request body. '
                                        b'There must be valid JSON')

    def test_request_with_undefined_type(self):
        response = self.fetch('/hf',
                              body=compose(stubs.REQUEST_WITH_UNDEFINED_TYPE),
                              method='POST')
        self.assertEqual(response.code, 500)
        self.assertEqual(response.body, b'Undefined type')

    def test_request_with_unknown_type(self):
        response = self.fetch('/hf',
                              body=compose(stubs.REQUEST_WITH_UNKNOWN_TYPE),
                              method='POST')
        self.assertEqual(response.code, 500)
        self.assertEqual(response.body, b'Unknown type')

    def test_handling_incomplete_interview_request(self):
        response = self.fetch('/hf',
                              body=compose(stubs.INCOMPLETE_INTERVIEW_REQUEST),
                              method='POST')
        self.assertEqual(response.code, 500)
        self.assertEqual(response.body, b'Incomplete request')

    def test_handling_interview_request(self):
        body = compose(stubs.INTERVIEW_REQUEST)

        response = self.fetch('/hf', body=body, method='POST')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, b'')

        s = sa.sql.select([Candidate]).where(Candidate.id == 1)
        result = self.conn.execute(s)
        row = result.fetchone()
        result.close()

        event = json.loads(body)['event']
        exp_candidate = event['applicant']
        exp_row = (exp_candidate['id'], exp_candidate['first_name'], exp_candidate['last_name'])
        self.assertEqual(row, exp_row)

        calendar_event = event['calendar_event']

        s = sa.sql.select([Interview]).where(Interview.candidate == exp_candidate['id'])
        result = self.conn.execute(s)
        row = result.fetchone()
        result.close()

        interview_start = handler.get_date_from_string(calendar_event['start'])
        interview_end = handler.get_date_from_string(calendar_event['end'])

        self.assertEqual(row[Interview.start], interview_start)
        self.assertEqual(row[Interview.end], interview_end)
        self.assertEqual(row[Interview.type], event['type'])

    def test_missing_calendar_event_item(self):
        response = self.fetch('/hf',
                              body=compose(stubs.MISSING_CALENDAR_INTERVIEW_REQUEST),
                              method='POST')
        self.assertEqual(response.code, 500)
        self.assertEqual(response.body, b'Could not decode request body. There must be valid JSON')
