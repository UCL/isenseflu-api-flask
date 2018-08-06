"""
 Tests Google Trends API client
"""

from datetime import date, datetime, timedelta, time
from os import path
from unittest import TestCase
from unittest.mock import patch

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpMock, RequestMockBuilder
from httplib2 import Response

from scheduler.google_api_client import GoogleApiClient, SERVICE_NAME, SERVICE_VERSION

DATA_DIR = path.join(path.dirname(__file__), 'data')


def datafile(filename):
    """
    Calculates the full absolute path from the relative path of a file
    """
    return path.join(DATA_DIR, filename)


class GoogleApiClientTestCase(TestCase):
    """ Test case for module scheduler.google_api_client """

    def test_fetch_google_scores(self):
        """
        Scenario: Evaluate GoogleApiClient#fetch_google_scores() method for a
        valid request
        Given a list of terms of type List[str]
        And start date in ISO format
        And end date in ISO format
        Then client retrieves a JSON object with an element "lines" inside
        """
        http = HttpMock(datafile('trends_discovery.json'), {'status': '200'})
        response = b'{"lines": [ { "term" : "a flu" , "points" : [] } ]}'
        request_builder = RequestMockBuilder(
            {
                'trends.getTimelinesForHealth': (None, response)
            }
        )
        with patch.object(GoogleApiClient, '__init__', lambda x: None):
            instance = GoogleApiClient()
            instance.service = build(
                serviceName=SERVICE_NAME,
                version=SERVICE_VERSION,
                http=http,
                developerKey='APIKEY',
                requestBuilder=request_builder,
                cache_discovery=False
            )
            instance.block_until = None
            terms = ['flu']
            start = date.today() - timedelta(days=5)
            end = start + timedelta(days=1)
            result = instance.fetch_google_scores(terms, start, end)
            self.assertEqual(len(result), 1)
            self.assertIn('term', result[0])
            self.assertIn('points', result[0])

    def test_403_error(self):
        """
        Scenario: Evaluate generation of error raising logic when calls to
        Google API hit the daily limit.
        Given a list of terms of type List[str]
        And start date in ISO format
        And end date in ISO format
        When Google API returns HTTP 403
        Then GoogleApiClient#fetch_google_scores() raises a RuntimeError
        """
        http = HttpMock(datafile('trends_discovery.json'), {'status': '200'})
        error = {
            'code': 403,
            'message': 'dailyLimitExceeded'
        }
        response = Response({'status': 403, 'reason': 'dailyLimitExceeded', 'error': error})
        request_builder = RequestMockBuilder(
            {
                'trends.getTimelinesForHealth': (response, b'{}')
            }
        )
        with patch.object(GoogleApiClient, '__init__', lambda x: None):
            instance = GoogleApiClient()
            instance.service = build(
                serviceName=SERVICE_NAME,
                version=SERVICE_VERSION,
                http=http,
                developerKey='APIKEY',
                requestBuilder=request_builder,
                cache_discovery=False
            )
            instance.block_until = None
            terms = ['flu']
            start = date.today() - timedelta(days=5)
            end = start + timedelta(days=1)
            try:
                instance.fetch_google_scores(terms, start, end)
            except RuntimeError as runtime_error:
                self.assertRegex(str(runtime_error), '^dailyLimitExceeded: blocked until ')

    def test_http_error(self):
        """
        Scenario: Evaluate generation of error raising logic when calls to
        Google API returns an error code other than 403.
        Given a list of terms of type List[str]
        And start date in ISO format
        And end date in ISO format
        When Google API returns an HTTP error code other than 403
        Then GoogleApiClient#fetch_google_scores() propagates HttpError
        """
        http = HttpMock(datafile('trends_discovery.json'), {'status': '200'})
        error = {
            'code': 400,
            'message': 'badRequest'
        }
        response = Response({'status': 400, 'reason': 'badRequest', 'error': error})
        request_builder = RequestMockBuilder(
            {
                'trends.getTimelinesForHealth': (response, b'{}')
            }
        )
        with patch.object(GoogleApiClient, '__init__', lambda x: None):
            instance = GoogleApiClient()
            instance.service = build(
                serviceName=SERVICE_NAME,
                version=SERVICE_VERSION,
                http=http,
                developerKey='APIKEY',
                requestBuilder=request_builder,
                cache_discovery=False
            )
            instance.block_until = None
            terms = ['flu']
            start = date.today() - timedelta(days=5)
            end = start + timedelta(days=1)
            with self.assertRaises(HttpError):
                instance.fetch_google_scores(terms, start, end)

    def test_blocked_until(self):
        """
        Scenario: Attempt at calling Google API from the same client instance
        after having reached the limit.
        Given GoogleApiClient.block_until has been set to tomorrow
        Then GoogleApiClient#fetch_google_scores() raises a RuntimeError
        """
        with patch.object(GoogleApiClient, '__init__', lambda x: None):
            instance = GoogleApiClient()
            instance.service = None
            instance.block_until = datetime.combine(date.today() + timedelta(days=1), time.min)
            terms = ['flu']
            start = date.today() - timedelta(days=5)
            end = start + timedelta(days=1)
            try:
                instance.fetch_google_scores(terms, start, end)
            except RuntimeError as runtime_error:
                expected = 'API client blocked until %s' % instance.block_until
                self.assertEqual(str(runtime_error), expected)

    def test_not_accepting_calls(self):
        """
        Scenario: Attempt at calling Google API from the same client instance
        after having reached the limit.
        Given GoogleApiClient.block_until has been set to tomorrow
        Then GoogleApiClient#is_accepting_calls() returns False
        """
        with patch.object(GoogleApiClient, '__init__', lambda x: None):
            instance = GoogleApiClient()
            instance.service = None
            instance.block_until = datetime.combine(date.today() + timedelta(days=1), time.min)
            self.assertFalse(instance.is_accepting_calls())

    def test_is_accepting_calls(self):
        """
        Scenario: Attempt at calling Google API from a new client instance.
        Given GoogleApiClient.block_until is not set
        Then GoogleApiClient#is_accepting_calls() returns True
        """
        instance = GoogleApiClient()
        self.assertTrue(instance.is_accepting_calls())
