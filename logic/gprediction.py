import csv
import logging
import string
import StringIO

from events import eventdata
import fb_api
from logic import event_locations
from util import fb_mapreduce

convert_chars = string.punctuation + '\r\n\t'
trans = string.maketrans(convert_chars, ' ' * len(convert_chars))

def strip_punctuation(s):
    return s.translate(trans)

def training_data_for_pevents(batch_lookup, pevents):
    batch_lookup.allow_memcache_write = False # don't pollute memcache
    for potential_event in pevents:
        if not potential_event.looked_at:
            continue
        batch_lookup.lookup_event(potential_event.fb_event_id)
        batch_lookup.lookup_event_attending(potential_event.fb_event_id)
    batch_lookup.finish_loading()

    # TODO(lambert): ideally would use keys_only=True, but that's not supported on get_by_key_name :-(
    db_events = eventdata.get_cached_db_events([x.fb_event_id for x in pevents])
    good_event_ids = [x.fb_event_id for x in db_events if x]

    csv_file = StringIO.StringIO()
    csv_writer = csv.writer(csv_file)

    for potential_event in pevents:
        if not potential_event.looked_at:
            continue
        try:
            good_event = potential_event.fb_event_id in good_event_ids and 'dance' or 'nodance'

            fb_event = batch_lookup.data_for_event(potential_event.fb_event_id)
            if fb_event['deleted']:
                continue
            fb_event_attending = batch_lookup.data_for_event_attending(potential_event.fb_event_id)

            training_features = get_training_features(potential_event, fb_event, fb_event_attending)
            csv_writer.writerow([good_event] + list(training_features))
        except fb_api.NoFetchedDataException:
            logging.info("No data fetched for event id %s", potential_event.fb_event_id)
    yield csv_file.getvalue()
map_training_data_for_pevents = fb_mapreduce.mr_wrap(training_data_for_pevents)

def get_training_features(potential_event, fb_event, fb_event_attending):
    if 'owner' in fb_event['info']:
        owner_name = 'id%s' % fb_event['info']['owner']['id']
    else:
        owner_name = ''
    location = event_locations.get_address_for_fb_event(fb_event).encode('utf-8')
    def strip_text(s):
        return strip_punctuation(s.encode('utf8')).lower()
    name = strip_text(fb_event['info'].get('name', ''))
    description = strip_text(fb_event['info'].get('description', ''))

    attendee_list = ' '.join(['id%s' % x['id'] for x in fb_event_attending['attending']['data']])

    source_list = ' '.join('id%s' % x for x in potential_event.source_ids)

    #TODO(lambert): maybe include number-of-keywords and keyword-density?

    #TODO(lambert): someday write this as a proper mapreduce that reduces across languages and builds a classifier model per language?
    # for now we can just grep and build sub-models per-language on my client machine.
    #return (potential_event.language, owner_name, location, name, description, attendee_list, source_list)
    return (attendee_list,)


def mr_generate_training_data(batch_lookup):
    fb_mapreduce.start_map(
        batch_lookup=batch_lookup,
        name='Write Training Data',
        handler_spec='logic.gprediction.map_training_data_for_pevents',
        output_writer_spec='mapreduce.output_writers.BlobstoreOutputWriter',
        handle_batch_size=20,
        entity_kind='logic.potential_events.PotentialEvent',
        extra_mapper_params={'mime_type': 'text/plain'},
        queue=None,
    )

MAGIC_USER_ID = '100529355548393795594'

def get_predict_service():
    #TODO(lambert): we need to cache this somehow, if we use this, since it appears to not even use memcache for credentials.
    import httplib2
    from apiclient.discovery import build
    from oauth2client import appengine

    credentials = appengine.StorageByKeyName(appengine.CredentialsModel, MAGIC_USER_ID, 'credentials').get()
    http = credentials.authorize(httplib2.Http())

    service = build("prediction", "v1.5", http=http)
    return service

MODEL_NAME = 'dancedeets/training_data.english.csv'
DANCE_BIAS_MODEL_NAME = 'training20120513dance'
NOT_DANCE_BIAS_MODEL_NAME = 'training20120513nodance'

def predict(potential_event, fb_event, fb_event_attending, service=None):
    body = {'input': {'csvInstance': get_training_features(potential_event, fb_event, fb_event_attending)}}
    logging.info("Dance Data: %r", body)
    service = service or get_predict_service()
    train = service.trainedmodels()
    dance_bias_prediction = train.predict(body=body, id=DANCE_BIAS_MODEL_NAME).execute()
    dance_bias_score = [x['score'] for x in dance_bias_prediction['outputMulti'] if x['label'] == 'dance'][0]
    not_dance_bias_prediction = train.predict(body=body, id=NOT_DANCE_BIAS_MODEL_NAME).execute()
    not_dance_bias_score = [x['score'] for x in not_dance_bias_prediction['outputMulti'] if x['label'] == 'dance'][0]
    logging.info("Dance Result: %s", dance_bias_prediction)
    logging.info("NoDance Result: %s", not_dance_bias_prediction)
    logging.info("Dance Score: %s, NoDance Score: %s", dance_bias_score, not_dance_bias_score)
    return dance_bias_score, not_dance_bias_score
