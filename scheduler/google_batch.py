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
 Container for a set of query parameters to use for calling Google API.
 These parameters are organised in batches to comply with the limits
 set by the API
"""

from datetime import date, timedelta
from typing import Iterator, List, Tuple

_GOOGLE_TERMS_BATCH_SIZE = 30
_GOOGLE_MAX_LINES = 2000
_GOOGLE_MAX_INTERVAL_PER_BATCH = timedelta(days=66)


class GoogleBatch:  # pylint: disable=too-few-public-methods
    """
    Container of query parameters for running requests on Google API. It processes
    entries to comply with the limits set by the API, such as number of data points
    returned and number of query terms
    """

    def __init__(self, google_terms: List[str], collect_dates: List[Tuple[date, date]]):
        self._google_terms = google_terms
        self._collect_dates = collect_dates
        self._batch_size = -1

    def get_batch(self) -> Iterator[Tuple[List[str], date, date]]:
        """
        Returns a generator of a list of Google terms and dates to be collected from the API
        organised in batches of up to 30 terms as per API documentation
        """
        for idx in range(0, len(self._google_terms), _GOOGLE_TERMS_BATCH_SIZE):
            batch = self._google_terms[idx:idx + _GOOGLE_TERMS_BATCH_SIZE]
            for collect_date in self._get_filtered_date_ranges():
                yield batch, collect_date[0], collect_date[1]

    def _get_size(self) -> int:
        if self._batch_size == -1:
            day_counter = 0
            for date_range in self._collect_dates:
                datediff = abs(date_range[1] - date_range[0])
                day_counter += datediff.days + 1
            self._batch_size = _GOOGLE_MAX_INTERVAL_PER_BATCH.days * day_counter
        return self._batch_size

    def _get_filtered_date_ranges(self) -> List[Tuple[date, date]]:
        if self._get_size() > 2000:
            filtered_date_ranges = []
            for date_range in self._collect_dates:
                interval_in_days = date_range[1] - date_range[0]
                if interval_in_days > _GOOGLE_MAX_INTERVAL_PER_BATCH:
                    range_start = date_range[0]
                    for _ in range(interval_in_days // _GOOGLE_MAX_INTERVAL_PER_BATCH):
                        range_end = range_start + _GOOGLE_MAX_INTERVAL_PER_BATCH
                        shortened_range = (range_start, range_end)
                        filtered_date_ranges.append(shortened_range)
                        range_start = range_end + timedelta(days=1)
                    if interval_in_days % _GOOGLE_MAX_INTERVAL_PER_BATCH:
                        filtered_date_ranges.append((range_start, date_range[1]))
                else:
                    filtered_date_ranges.append(date_range)
            return filtered_date_ranges
        return self._collect_dates
