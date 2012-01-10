import datetime
import logging

import base_servlet
from events import users
import locations
from logic import search
from util import dates
from util import urls

class LoginIfUnspecified(object):
    def requires_login(self):
        return False

#TODO(lambert): clean this out
class CalendarHandler(LoginIfUnspecified, base_servlet.BaseRequestHandler):
    def get(self):
        self.finish_preload()
        self.display['calendar_feed_url'] = '/calendar/feed?%s' % '&'.join('%s=%s' % (k, v) for (k, v) in self.request.params.iteritems())
        self.render_template('calendar_shell')

class CalendarFeedHandler(LoginIfUnspecified, base_servlet.BaseRequestHandler):
    def get(self):
        self.finish_preload()
        if self.request.get('start'):
            start_time = datetime.datetime.fromtimestamp(int(self.request.get('start')))
        else:
            start_time = datetime.datetime.now()
        if self.request.get('end'):
            end_time = datetime.datetime.fromtimestamp(int(self.request.get('end')))
        else:
            end_time = datetime.datetime.now() + datetime.timedelta(days=365)

        if self.request.get('city_name'):
            location = self.request.get('city_name')
            distance = 50
            distance_units = 'miles'
        else:
            location = self.request.get('location', self.user and self.user.location)
            distance = int(self.request.get('distance', self.user and self.user.distance or 50))
            distance_units = self.request.get('distance_units', self.user and self.user.distance_units or 'miles')
        if distance_units == 'miles':
            distance_in_km = locations.miles_in_km(distance)
        else:
            distance_in_km = distance
        bounds = locations.get_location_bounds(location, distance_in_km)

        query = search.SearchQuery(bounds=bounds, start_time=start_time, end_time=end_time)
        search_results = query.get_search_results(self.fb_uid, self.fb_graph)

        json_results = []
        for result in search_results:
            json_results.append(dict(
                id=result.fb_event['info']['id'],
                title=result.fb_event['info']['name'],
                start=dates.parse_fb_timestamp(result.fb_event['info'].get('start_time')).strftime('%Y-%m-%dT%H:%M:%SZ'),
                end=dates.parse_fb_timestamp(result.fb_event['info'].get('end_time')).strftime('%Y-%m-%dT%H:%M:%SZ'),
                url=urls.fb_event_url(result.fb_event['info']['id']),
            ))
        self.write_json_response(json_results)    

