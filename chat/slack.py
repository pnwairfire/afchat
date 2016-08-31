"""pyairfire.chat.slack:  Utilities for archiving slack chat histories and
posting messages.
"""

__author__      = "Joel Dubowy"


import json
import logging
import requests

import slacker

from pyairfire.scripting.utils import exit_with_msg
from . import archivebase

__all__ = [
    'SlackArchiver',
    'send'
]


##
## Archives
##

class SlackArchiver(archivebase.ArchiverBase):

    # TODO: should there indeed be a default sender?
    DEFAULT_EMAIL_SENDER = "slack-archiver@airfire.org"
    DEFAULT_EMAIL_SUBJECT = "Slack archive {} through {}"
    ARCHIVE_PREFIX = 'slack-archive'

    def __init__(self, token, num_days, **options):
        super(SlackArchiver, self).__init__(num_days, **options)

        self._slack_client = slacker.Slacker(token)
        try:
            self._slack_client.api.test()
        except slacker.Error:
            raise RuntimeError(
                "Invalid token, or otherwise failed to use slack API")

    def archive(self, channel=None):
        channels = self._channels(channel)
        histories = self._histories(channels)
        in_memory_zip = self._zip(histories)
        self._write(in_memory_zip)
        self._email(in_memory_zip)

    def _channels(self, channel):
        channels = self._slack_client.channels.list().body['channels']
        if channel:
            channels = [c for c in channels if c['name'] == channel]
        return channels

    def _histories(self, channels):
        histories = []
        for c in channels:
            histories.append({
                "id": c['id'],
                "name": c['name'],
                "history": self._history(c)
            })
        return histories

    def _history(self, channel):
        history = []
        latest = str(self._start_date.timestamp())
        oldest = str(self._end_date.timestamp())
        while True:
            # Note: unless you set inclusize=true in the request,
            #  the latest / oldest range is non-inclusive
            logging.debug('Querying history - %s (%s) - %s -> %s',
                channel['name'], channel['id'], latest, oldest)
            r = self._slack_client.channels.history(
                channel['id'], latest=latest, oldest=oldest).body
            history.extend(r['messages'])
            # if 'is_limited' is True, that means we've reached
            # the limit for our free plan
            if not r['has_more'] or r.get('is_limited'):
                break
            latest = history[-1]['ts']
        return history


##
## Notifications
##

def send(webhook_url, text, channel=None, icon_emoji=None, username=None):
    """Posts notification to slack channel

    args:
     - webhook_url -- hooks.slack.com url containing identifier guids
     - text -- message to be posted

    kwargs:
     - channel -- used to specify alternate channel; if not defined, message
        will be posted to the webhook's default channel
     - username --
     - icon_emoji -- e.g ":robot:"; if not defined, channel's default icon
        emoji will be displayed

    Examples:

        > send('https://hooks.slack.com/services/sdjsdf/skdjfl/sdkfjlf',
            "test message")
        > send('https://hooks.slack.com/services/sdjsdf/skdjfl/sdkfjlf',
            "hello", channel="#foo", icon_emoji=":robot:", username="bar")
    """
    data = {
        "text": text
    }
    if channel:
        # Make sure channel has '#' prefix
        data['channel'] = '#' + channel.lstrip('#')
    if username:
        data['username'] = username
    if icon_emoji:
        data['icon_emoji'] = icon_emoji

    return requests.post(webhook_url, data=json.dumps(data))
