import unittest
from unittest.mock import patch

import requests

from Coursedump import CourseDump


class CourseLookupTests(unittest.TestCase):
    def setUp(self):
        self.course = CourseDump()
        self.url = 'https://example.test/GetType1Result'
        self.payload = {'year': 115}
        self.ok = requests.Response()
        self.ok.status_code = 200
        self.ok._content = b'{"total": 1}'

    def request(self, effects):
        with patch('Coursedump.UserAgent') as ua, \
                patch('Coursedump.requests.post', side_effect=effects) as post, \
                patch('Coursedump.time.sleep') as sleep:
            ua.return_value.random = 'test-agent'
            self.post, self.sleep = post, sleep
            return self.course._get_res_json(self.url, self.payload)

    @staticmethod
    def response(status):
        response = requests.Response()
        response.status_code = status
        response._content = b''
        return response

    def test_recovers_from_timeout_and_503(self):
        self.assertEqual(self.request([requests.exceptions.ReadTimeout(), self.response(503), self.ok]),
                         {"total": 1})
        self.assertEqual(self.post.call_count, 3)
        self.assertTrue(all(c.kwargs['timeout'] == (5, 45) for c in self.post.call_args_list))
        self.assertEqual([c.args[0] for c in self.sleep.call_args_list], [1, 2])

    def test_exhausted_connection_errors_still_fail_the_job(self):
        with self.assertRaises(SystemExit) as result:
            self.request([requests.exceptions.ConnectionError()] * 3)
        self.assertEqual(result.exception.code, 1)
        self.assertEqual(self.post.call_count, 3)

    def test_400_and_tls_errors_are_not_retried(self):
        for failure in (self.response(400), requests.exceptions.SSLError()):
            with self.subTest(failure=failure), self.assertRaises(SystemExit):
                self.request([failure])
            self.assertEqual(self.post.call_count, 1)
            self.sleep.assert_not_called()

    def test_invalid_json_still_fails_without_retry(self):
        invalid = self.response(200)
        invalid._content = b'not JSON'
        with self.assertRaises(SystemExit) as result:
            self.request([invalid])
        self.assertEqual(result.exception.code, 1)
        self.assertEqual(self.post.call_count, 1)
        self.sleep.assert_not_called()
