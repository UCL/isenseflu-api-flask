# i-sense flu api: REST API, and data processors for the i-sense flu service from UCL.
# (c) 2019, UCL <https://www.ucl.ac.uk/
#
# This file is part of i-sense flu api
#
# i-sense flu api is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# i-sense flu api is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with i-sense flu api.  If not, see <http://www.gnu.org/licenses/>.

"""
 Collects data from Google Health Trends API
"""

from os import getenv
import json
import time
from typing import List, Dict, Union

from datetime import date, datetime, timedelta, time as dtime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SERVICE_NAME = 'trends'
SERVICE_VERSION = 'v1beta'

_DISCOVERY_SERVICE_URL = 'https://www.googleapis.com/discovery/v1/apis/trends/v1beta/rest'
_GEORESTRICTION_REGION = 'GB-ENG'
_GOOGLE_API_KEY = getenv("GOOGLE_API_KEY", "")
_ISO_FORMAT = '%Y-%m-%d'
_TIMELINE_RESOLUTION = 'day'


class GoogleApiClient:
    """
    Google Trends API client. It queries data restricted to England with a
    timeline resolution of 1 day.
    """

    def __init__(self):
        self.service = build(
            serviceName=SERVICE_NAME,
            version=SERVICE_VERSION,
            discoveryServiceUrl=_DISCOVERY_SERVICE_URL,
            developerKey=_GOOGLE_API_KEY,
            cache_discovery=False,
            static_discovery=False
        )
        self.block_until = None

    def fetch_google_scores(
            self, terms: List[str],
            start: date,
            end: date
        ) -> List[Dict[str, Union[str, List[Dict[str, Union[str, float]]]]]]:
        """
        Retrieves data from Google trends.getTimelinesForHealth endpoint. It sleeps for 1
        second before running a request to help prevent hitting the limit with subsequent
        calls.
        The returned collection contains a list of data points per term as in the example
        below
        [
            {
                'term': 'a flu',
                'points': [
                    {
                        'date': 'Jul 01 2018',
                        'value': 60.58781476812457
                    },
                    {
                        'date': 'Jul 02 2018',
                        'value': 83.01700758132898
                    }
                ]
            },
            {
                'term': 'flu season',
                'points': [
                    {
                        'date': 'Jul 01 2018',
                        'value': 0.0
                    },
                    {
                        'date': 'Jul 02 2018',
                        'value': 15.144689517705173
                    }
                ]
            }
        ]
        """
        if not self.is_accepting_calls():
            raise RuntimeError('API client blocked until %s' % self.block_until)
        if not self.is_returning_non_zero_for_temperature(end):
            import logging
            logging.warning('API returning zero for term temperature. Not saving')
            return []
        graph = self.service.getTimelinesForHealth(
            terms=terms,
            geoRestriction_region=_GEORESTRICTION_REGION,
            time_startDate=start.strftime(_ISO_FORMAT),
            time_endDate=end.strftime(_ISO_FORMAT),
            timelineResolution=_TIMELINE_RESOLUTION
        )
        time.sleep(1)  # sleep for 1 second to avoid hitting the rate limit
        try:
            response = graph.execute()
            return response['lines']
        except HttpError as http_error:
            data = json.loads(http_error.content.decode('utf-8'))
            code = data['error']['code']
            reason = data['error']['errors'][0]['reason']
            if code == 403 and reason == 'dailyLimitExceeded':
                self.block_until = datetime.combine(date.today() + timedelta(days=1), dtime.min)
                raise RuntimeError('%s: blocked until %s' % (reason, self.block_until))
            import logging
            logging.warning(http_error)
            return []

    def is_accepting_calls(self):
        """
        Displays current status of the client in relation to API limits
        """
        return self.block_until is None or self.block_until <= datetime.today()

    def is_returning_non_zero_for_temperature(self, end: date):
        """
        Checks whether the API returns a non-zero value for the term temperature
        for the end date
        """
        start = end - timedelta(days=1)
        graph = self.service.getTimelinesForHealth(
            terms=['temperature'],
            geoRestriction_region=_GEORESTRICTION_REGION,
            time_startDate=start.strftime(_ISO_FORMAT),
            time_endDate=end.strftime(_ISO_FORMAT),
            timelineResolution=_TIMELINE_RESOLUTION
        )
        time.sleep(1)  # sleep for 1 second to avoid hitting the rate limit
        try:
            response = graph.execute()
            temperature_lines = response['lines'][0]
            temperature_value = temperature_lines['points'][1]['value']
            if temperature_value == 0:
                return False
            return True
        except HttpError as http_error:
            data = json.loads(http_error.content.decode('utf-8'))
            code = data['error']['code']
            reason = data['error']['errors'][0]['reason']
            if code == 403 and reason == 'dailyLimitExceeded':
                self.block_until = datetime.combine(date.today() + timedelta(days=1), dtime.min)
                raise RuntimeError('%s: blocked until %s' % (reason, self.block_until))
            import logging
            logging.warning(http_error)
            return False
