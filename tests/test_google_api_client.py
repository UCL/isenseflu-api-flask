"""
 Tests Google Trends API client
"""

from datetime import date, timedelta
from os import path
from unittest import TestCase
from unittest.mock import patch

from googleapiclient.discovery import build
from googleapiclient.http import HttpMock, RequestMockBuilder

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
        response = '{"lines": [ { "term" : "a flu" , "points" : [] } ]}'
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
            terms = ['flu']
            start = date.today() - timedelta(days=5)
            end = start + timedelta(days=1)
            result = instance.fetch_google_scores(terms, start, end)
            self.assertEqual(len(result), 1)
            self.assertIn('term', result[0])
            self.assertIn('points', result[0])
