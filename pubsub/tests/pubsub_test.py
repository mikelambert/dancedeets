# -*-*- encoding: utf-8 -*-*-

import mock
import unittest

from google.appengine.ext import testbed

import fb_api
from events import eventdata
from events import event_updates
from loc.test_utils import gmaps_fake
from pubsub import pubsub
from test_utils import fb_api_stub

FB_EVENT = {
    'info': {
        'id': '555',
        'name': 'Some really long name here that just keeps on going and may or may not ever get truncated, but we will just have to wait and see',
        'start_time': '2010-01-01T12:00:00',
    }
}

class TestPublishEvent(unittest.TestCase):
    def setUp(self):
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_search_stub()
        self.testbed.init_taskqueue_stub(root_path='.')
        self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        self.fb_api = fb_api_stub.Stub()
        self.fb_api.activate()
        gmaps_fake.activate()

    def tearDown(self):
        self.fb_api.deactivate()
        gmaps_fake.deactivate()

    @mock.patch('oauth2.Client.request')
    @mock.patch('twitter.Twitter')
    def testPull(self, Twitter, Client_request):
        # No-op works with with no tokens
        pubsub.pull_and_publish_event()

        # No-op works with a freshly created token
        Client_request.return_value = {'status': '200'}, 'oauth_token=token&oauth_token_secret=secret'
        pubsub.twitter_oauth1('user_id', 'token_nickname', None)
        pubsub.twitter_oauth2('token', 'verifier')
        pubsub.pull_and_publish_event()

        # Now when we add a token to the pull queue, it will get run
        event_id = '383948038362054'
        fbl = fb_api.FBLookup(None, None)
        fb_event = fbl.get(fb_api.LookupEvent, event_id)

        db_event = eventdata.DBEvent.get_or_insert(event_id)
        event_updates.update_and_save_event(db_event, fb_event)
        db_event.put()
        pubsub.eventually_publish_event(event_id)

        pubsub.pull_and_publish_event()
        # Check that Twitter().statuses.update(...) was called
        self.assertTrue(Twitter.return_value.statuses.update.called)

class TestImports(unittest.TestCase):
    def runTest(self):
        class DBEvent:
            actual_city_name = 'Sacramento, CA, United States'
        self.assertEqual(pubsub.format_twitter_post(DBEvent(), FB_EVENT, media=False, handles=[]),
            u'2010/01/01: Sacramento, CA, United States: Some really long name here that just keeps on going and may or may not ev… http://www.dancedeets.com/events/555/')
        self.assertEqual(pubsub.format_twitter_post(DBEvent(), FB_EVENT, media=False, handles=['@name']),
            u'2010/01/01: Sacramento, CA, United States: Some really long name here that just keeps on going and may or may … http://www.dancedeets.com/events/555/ @name')
        self.assertEqual(pubsub.format_twitter_post(DBEvent(), FB_EVENT, media=False, handles=['@name1', '@name2', '@name3', '@name4', '@name5', '@name6', '@name7']),
            u'2010/01/01: Sacramento, CA, United States: Some really long name here that just k… http://www.dancedeets.com/events/555/ @name1 @name2 @name3 @name4 @name5')
        self.assertEqual(pubsub.format_twitter_post(DBEvent(), FB_EVENT, media=False, handles=['@mspersia', '@grooveologydc', '@groovealils', '@dam_sf', '@mishmashboutique']),
            u'2010/01/01: Sacramento, CA, United States: Some really long name here that jus… http://www.dancedeets.com/events/555/ @mspersia @grooveologydc @groovealils')
        self.assertEqual(pubsub.format_twitter_post(DBEvent(), FB_EVENT, media=False, handles=['@jodywisternoff', '@jodywisternoff', '@Lane8music']),
            u'2010/01/01: Sacramento, CA, United States: Some really long name here that just keep… http://www.dancedeets.com/events/555/ @jodywisternoff @jodywisternoff')
