#!/usr/bin/env python

import logging
import time
import urllib

import app
import base_servlet
from logic import friends
from logic import rsvp
from util import dates
from . import search
from . import search_base
from . import search_pages

class SearchHandler(base_servlet.BaseRequestHandler):
    def requires_login(self):
        if not self.request.get('location') and not self.request.get('keywords'):
            return True
        return False

    def get(self, *args, **kwargs):
        self.handle(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.handle(*args, **kwargs)

    def handle(self, city_name=None):
        self.finish_preload()
        if self.user and not self.user.location:
            #TODO(lambert): make this an error
            self.user.add_message("We could not retrieve your location from facebook. Please fill out a location below")
            self.redirect('/user/edit')
            return

        form = search_base.HtmlSearchForm(self.request.GET, data=self.user.dict_for_form() if self.user else None)
        form.validated = form.validate()
        self.handle_search(form)

@app.route('/')
@app.route('/events/relevant')
class RelevantHandler(SearchHandler):
    template_name = 'results'
    search_query_class = search.SearchQuery

    def handle_search(self, form):
        validated = form.validate()
        if not validated:
            for field, errors in form.errors.items():
                for error in errors:
                    self.add_error(u"%s error: %s" % (
                        getattr(form, field).label.text,
                        error
                    ))

        if not self.request.get('calendar'):
            search_query = None
            try:
                search_query = self.search_query_class.create_from_form(form)
            except search_base.SearchException as e:
                logging.warning("Bad search query: %s", form)
                self.add_error(unicode(e))

            if search_query and validated:
                search_results = search_query.get_search_results()
            else:
                search_results = []
            # We can probably speed this up 2x by shrinking the size of the fb-event-attending objects. a list of {u'id': u'100001860311009', u'name': u'Dance InMinistry', u'rsvp_status': u'attending'} is 50% overkill.
            a = time.time()
            friends.decorate_with_friends(self.fbl, search_results)
            logging.info("Decorating with friends-attending took %s seconds", time.time() - a)
            a = time.time()
            rsvp.decorate_with_rsvps(self.fbl, search_results)
            logging.info("Decorating with personal rsvp data took %s seconds", time.time() - a)

            past_results, present_results, grouped_results = search.group_results(search_results)
            if search_query and search_query.time_period == dates.TIME_FUTURE:
                present_results = past_results + present_results
                past_results = []

            self.display['num_upcoming_results'] = sum([len(x.results) for x in grouped_results]) + len(present_results)
            self.display['past_results'] = past_results
            self.display['ongoing_results'] = present_results
            self.display['grouped_upcoming_results'] = grouped_results

        if form.time_period.data == search_base.TIME_PAST:
            self.display['selected_tab'] = 'past'
        elif self.request.get('calendar'):
            self.display['selected_tab'] = 'calendar'
        else:
            self.display['selected_tab'] = 'present'

        self.display['form'] = form
        if form.location.data and form.keywords.data:
            self.display['result_title'] = '%s dance events near %s' % (form.keywords.data, form.location.data)
        elif form.location.data:
            self.display['result_title'] = '%s dance events' % form.location.data
        elif form.keywords.data:
            self.display['result_title'] = '%s dance events' % form.keywords.data
        else:
            self.display['result_title'] = 'Dance events'

        request_params = form.url_params()
        self.display['past_view_url'] = '/events/relevant?past=1&%s' % urllib.urlencode(request_params)
        self.display['upcoming_view_url'] = '/events/relevant?%s' % urllib.urlencode(request_params)
        self.display['calendar_view_url'] = '/events/relevant?calendar=1&%s' % urllib.urlencode(request_params)
        self.display['calendar_feed_url'] = '/calendar/feed?%s' % urllib.urlencode(request_params)
        self.jinja_env.globals['CHOOSE_RSVPS'] = rsvp.CHOOSE_RSVPS
        self.render_template(self.template_name)

@app.route('/city/(.*)/?')
class CityHandler(RelevantHandler):
    def requires_login(self):
        return False

    def handle(self, city_name):
        # TODO(lambert): Why is this still required, can we get rid of it?
        self.fbl.batch_fetch() # to avoid bad error handler?
        form = search_base.SearchForm(data={'location': city_name, 'distance': 100, 'distance_units': 'km'})
        self.handle_search(form)

@app.route('/pages/search')
class RelevantPageHandler(RelevantHandler):
    template_name = 'results_pages'
    search_query_class = search_pages.SearchPageQuery

