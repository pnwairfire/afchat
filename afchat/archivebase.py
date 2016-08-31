"""afchat.archivebase
"""

__author__ = "Joel Dubowy"

import datetime
import io
import json
import logging
import os
import re
import smtplib
import zipfile
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from afscripting.utils import exit_with_msg

class ArchiverBase(object):

    ARCHIVE_DATETIME_FORMAT = "%Y%m%dT%H%S%M"
    DEFAULT_SMTP_SERVER = "localhost:25"

    # Note: DEFAULT_EMAIL_SENDER, DEFAULT_EMAIL_SUBJECT,
    #  and ARCHIVE_PREFIX must be defined by child class

    def __init__(self, num_days, **options):
        self._start_date = datetime.datetime.utcnow()
        self._end_date = self._start_date - datetime.timedelta(num_days)

        self._dest_dir = options.get('dest_dir')
        self._email_recipients = options.get('email_recipients')
        if not self._dest_dir and not self._email_recipients:
            exit_with_msg("Specify either dest_dir or email_recipients, or both.")

        start_date_str = self._start_date.strftime(self.ARCHIVE_DATETIME_FORMAT)
        end_date_str =  self._end_date.strftime(self.ARCHIVE_DATETIME_FORMAT)

        self._archive_name = "{}-{}-{}".format(
            self.ARCHIVE_PREFIX, end_date_str, start_date_str)
        self._zip_file_name = '{}.zip'.format(self._archive_name)

        self._email_sender = options.get('email_sender') or self.DEFAULT_EMAIL_SENDER
        self._email_subject = (options.get('email_subject') or
            self.DEFAULT_EMAIL_SUBJECT.format(start_date_str, end_date_str))
        self._smtp_server = options.get('smtp_server') or self.DEFAULT_SMTP_SERVER
        self._smtp_username = options.get('smtp_username')
        self._smtp_password = options.get('smtp_password')
        self._smtp_starttls = options.get('smtp_starttls')

    FILENAME_CLEANER = re.compile('[^\w\-_]')
    def _zip(self, histories):
        logging.info("Zipping up files")
        in_memory_zip = io.BytesIO()
        z =  zipfile.ZipFile(in_memory_zip, 'a', zipfile.ZIP_DEFLATED, False)
        for h in histories:
            filename = '{}/{}.json'.format(self._archive_name,
                self.FILENAME_CLEANER.sub('_', h['name']))
            z.writestr(filename, json.dumps(h['history']))
        return in_memory_zip

    def _write(self, in_memory_zip):
        if not self._dest_dir:
            return

        zip_file_name = os.path.join(self._dest_dir, self._zip_file_name)
        logging.info('Writing zipfile {}'.format(zip_file_name))
        with open(zip_file_name, 'wb') as zf:
            in_memory_zip.seek(0) # is this necessary
            zf.write(in_memory_zip.read())

    def _email(self, in_memory_zip):
        if not self._email_recipients:
            return

        logging.info("Emailing zip file {} to {}".format(
            self._zip_file_name, ', '.join(self._email_recipients)))
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self._email_sender
            msg['To'] = ', '.join(self._email_recipients)
            msg['Subject'] = self._email_subject


            msg.attach(MIMEText(self._email_subject))

            in_memory_zip.seek(0)
            msg.attach(MIMEApplication(in_memory_zip.read(),
                Content_Disposition='attachment; filename="{}"'.format(self._zip_file_name),
                Name=self._zip_file_name))

            logging.debug('Connecting to SMTP server %s', self._smtp_server)
            s = smtplib.SMTP(self._smtp_server)

            if self._smtp_starttls:
                logging.debug('Using STARTTLS')
                s.ehlo()
                s.starttls()
                s.ehlo()

            if self._smtp_username and self._smtp_password:
                logging.debug('Logging into SMTP server with u/p')
                s.login(self._smtp_username, self._smtp_password)

            s.sendmail(msg['from'], self._email_recipients, msg.as_string())
            s.quit()

        except Exception as e:
            exit_with_msg('Failed to send email to {} - {}'.format(
                ', '.join(self._email_recipients), e))