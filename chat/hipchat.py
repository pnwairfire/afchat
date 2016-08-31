"""pyairfire.chat.hipchat
"""

__author__      = "Joel Dubowy"

import json
import logging
import requests
import traceback

from pyairfire.scripting.utils import exit_with_msg
from . import archivebase

__all__ = [
    'HipChatArchiver',
    'send'
]


##
## Archives
##

class HipChatArchiver(archivebase.ArchiverBase):

    # TODO: should there indeed be a default sender?
    DEFAULT_EMAIL_SENDER = "hipchat-archiver@airfire.org"
    DEFAULT_EMAIL_SUBJECT = "HipChat archive {} through {}"
    ARCHIVE_PREFIX = 'hipchat-archive'

    def __init__(self, auth_token, num_days, **options):
        super(HipChatArchiver, self).__init__(num_days, **options)

        self._auth_token = auth_token

    def archive(self, room_id=None):
        rooms = self._get_rooms(room_id=room_id)
        histories = self._get_histories(rooms)
        in_memory_zip = self._zip(histories)
        self._write(in_memory_zip)
        self._email(in_memory_zip)

    def _send(self, url, join_char='?'):
        url = "{}{}auth_token={}".format(url, join_char, self._auth_token)
        headers = {
           'Accept': 'application/json'
        }
        logging.debug("Requesting {}".format(url))
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            # TODO: retry
            exit_with_msg("Http failure: {} - {}".format(url, r.content))
        return r.json()

    ROOM_URL = "https://api.hipchat.com/v2/room"
    def _get_rooms(self, room_id=None):
        logging.info('Querying room{}'.format(' id ' + room_id if room_id else 's'))
        # get rooms with:
        #  https://www.hipchat.com/docs/apiv2/method/get_all_rooms
        # Note: url path's can't have trailing slash; if there, you get 404
        url = self.ROOM_URL + '/' + room_id if room_id else self.ROOM_URL
        try:
            data = self._send(url)
        except Exception as e:
            logging.debug(traceback.format_exc())
            exit_with_msg("Failed to query room information: {}".format(e))
        return [data] if room_id else data['items']

    def _get_histories(self, rooms):
        logging.info('Querying histories')
        histories = []
        for r in rooms:
            try:
                logging.info('Querying history for room {} ({})'.format(
                    r['name'], r['id']))
                histories.append({
                    "id": r['id'],
                    "name": r['name'],
                    "history": self._get_history(r['id'])
                })
                logging.debug('Received {} messages from {}'.format(
                    len(histories[-1]['history']), r['name']))
            except Exception as e:
                logging.error("Failed to query history for room {} - {}."
                    " Skipping".format(r['name'], e))
        return histories

    def _get_history(self, room_id):
        # get room history with:
        #  https://www.hipchat.com/docs/apiv2/method/view_room_history
        base_url = '{}/{}/history?date={}&end-date={}'.format(self.ROOM_URL,
            room_id, self._start_date, self._end_date)
        history = []
        start_index=0
        while True:
            url = '{}&start-index={}'.format(base_url, start_index)
            data = self._send(url, join_char='&')
            if not data['items']:
                break
            history.extend(data['items'])
            start_index += len(data['items'])
        history.reverse()
        return history


##
## Notifications
##

def send(message, room_id, auth_token, color="green"):
    data = {
        "color": color,
        "message": message,
        "notify": False,
        "message_format": "text"
    }
    url = "https://api.hipchat.com/v2/room/{}/notification?auth_token={}".format(
        room_id, auth_token)
    headers = {
        'Content-type': 'application/json',
        'Accept': 'text/plain'
    }
    return requests.post(url, data=json.dumps(data), headers=headers)
