"""
 Collects data from Google Health Trends API
"""

from datetime import date
from googleapiclient.discovery import build
from os import environ
from typing import List

_DISCOVERY_SERVICE_URL = 'https://www.googleapis.com/discovery/v1/apis/trends/v1beta/rest'
_GEORESTRICTION_REGION = 'GB-ENG'
_GOOGLE_API_KEY = environ["GOOGLE_API_KEY"]
_ISO_FORMAT = '%Y-%m-%d'
_SERVICE_NAME = 'trends'
_SERVICE_VERSION = 'v1beta'
_TIMELINE_RESOLUTION = 'day'


class GoogleApiClient(object):

    def __init__(self):
        self.service = build(
            serviceName=_SERVICE_NAME,
            version=_SERVICE_VERSION,
            discoveryServiceUrl=_DISCOVERY_SERVICE_URL,
            developerKey=_GOOGLE_API_KEY,
            cache_discovery=False
        )

    def fetch_google_scores(self, terms:List[str], start:date, end:date):
        graph = self.service.getTimelinesForHealth(
            terms=terms,
            geoRestriction_region=_GEORESTRICTION_REGION,
            time_startDate=start.strftime(_ISO_FORMAT),
            time_endDate=end.strftime(_ISO_FORMAT),
            timelineResolution=_TIMELINE_RESOLUTION
        )
        response = graph.execute()
        pass
