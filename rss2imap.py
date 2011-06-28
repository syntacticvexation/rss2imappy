# rss2imappy: A reimplementation of rss2imap (http://rss2imap.sourceforge.net)
# in Python
# Copyright (C) 2011 Syntactic Vexation

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

#!/usr/bin/python

from urlfileparser import *

import ConfigParser
import calendar
import datetime
import email
from email import Charset
from email.mime.text import MIMEText
import feedparser
import imaplib
import sys
import time

config_section = 'IMAPConfig'

# To replicate rss2imap's output more closely this hack is needed to force
# 7 or 8-bit codec use
# Inspired by
# http://radix.twistedmatrix.com/2010/07/how-to-send-good-unicode-email-with.html
Charset.add_charset('utf-8', Charset.QP,None, 'utf-8')
EMAIL_TEMPLATE="""<html>
    <head>
    <title>%(TITLE)s</title>
    <style type="text/css">
    body {
          margin: 0;
          border: none;
          padding: 0;
    }
    iframe {
      position: fixed;
      top: 0;
      right: 0;
      bottom: 0;
      left: 0;
      border: none;
    }
    </style>
    </head>
    <body>
    <iframe  width="100%%" height="100%%" src="%(LINK)s">
    %(SUMMARY)s
    </iframe>
    </body>
    </html>"""


def get_name():
    return "rss2imappy"

def get_version_string():
    return get_name()+" version 0.0.2"

def get_usage():
    return get_version_string() + "\n" + "Usage:\n" + get_name() + " <url-file>"

class FeedMsg:
    def __init__(self,url,user,from_addr,channel_link,entry):
        title = entry['title']
        link = entry['link']
        date = email.utils.formatdate(calendar.timegm(entry['updated_parsed']),\
                                      False,True)
        self.msg_id = link+'@localhost'

        if 'summary_detail' in entry:
            summary = entry['summary_detail']['value']
        elif 'summary' in entry:
            summary = entry['summary']
        else:
            print entry.keys()
            summary = ''
            
        agg_date = datetime.datetime.today().strftime("%a %b %d %H:%M:%S %Y")

        self.msg = MIMEText(self.generate_msg_body(title,link,summary),\
                            'html','utf-8')
        self.msg['From'] = from_addr
        self.msg['Subject'] = title
        self.msg['To'] = user
        self.msg.add_header('Date',date)
        self.msg.add_header('Content-Base',link)
        self.msg.add_header('Message-Id',self.msg_id)
        self.msg.add_header('User-Agent',get_version_string())
        self.msg.add_header('X-RSS-Link',url)
        self.msg.add_header('X-RSS-Channel-Link',channel_link)
        self.msg.add_header('X-RSS-Item-Link',link)
        self.msg.add_header('X-RSS-Aggregator',get_name())
        self.msg.add_header('X-RSS-Aggregate-Date',agg_date)
        # this is different in original don't know why
        self.msg.add_header('X-RSS-Last-Modified',date)

    @staticmethod
    def generate_msg_body(TITLE,LINK,SUMMARY):
        return EMAIL_TEMPLATE % locals()

    def get_msg_id(self):
        return self.msg_id

    def __str__(self):
        return self.msg.as_string()

class RIMAPConnection:
    def __init__(self,config):
        self.config = config

        if self.config['use-ssl']:
            self.conn = imaplib.IMAP4_SSL(self.config['host'])
        else:
            self.conn = imaplib.IMAP4(self.config['host'])
        self.conn.login(self.config['user'],self.config['password'])

    def new_feed(self,directory):
        self.conn.create(directory)
        self.conn.subscribe(directory)

    def feed_exists(self,directory):
        (status,result) = self.conn.list(directory)
        return len(result) > 0

    def entry_exists(self,directory,target_msg):
        target_msg_id = target_msg.get_msg_id()
        self.conn.select(directory,True)
        typ, msgs = self.conn.search(None,'ALL')

        for msg in msgs:
            for num in msg.split():
                typ, data = self.conn.fetch(num, \
                                            '(BODY[HEADER.FIELDS (MESSAGE-ID)])')
                typ,msg_id_string  = data[0]
                if msg_id_string.split(': ')[1].rstrip() == target_msg_id:
                    return True

        return False


    def put_entry(self,feed_dir,msg):
        feed_dir = self.escape_directory(feed_dir)
        if self.feed_exists(feed_dir):
            self.new_feed(feed_dir)
        if not self.entry_exists(feed_dir,msg):
            self.conn.append(feed_dir,'',\
                             imaplib.Time2Internaldate(time.time()),str(msg))

    def disconnect(self):
        self.conn.logout()

    @staticmethod
    def read_imap_config(conf_file):
        imap_config = {}
        config = ConfigParser.RawConfigParser()
        config.read(conf_file)

        imap_config['user'] = config.get(config_section,'user')
        imap_config['password'] = config.get(config_section,'password')
        imap_config['host'] = config.get(config_section,'host')

        imap_config['use-ssl'] = config.getboolean(config_section,'use-ssl')

        return imap_config

    @staticmethod
    def escape_directory(directory):
        return '"'+directory+'"'

def process_feed(imap_conn,user,config,url):
    feed = feedparser.parse(url)
  
    for entry in reversed(feed['entries']):
        expanded_config = expand_macros(feed,entry,config)
        imap_conn.put_entry(expanded_config['folder'],\
                            FeedMsg(url,user,expanded_config['from'],\
                                    feed.feed['link'],entry))
    
def main():
    if len(sys.argv) != 2:
        print get_usage()
    else:
        urlconfig = URLFileParser.parse(sys.argv[1])
        imap_config = RIMAPConnection.read_imap_config('conf/rss2imap.conf')

        imap_conn = RIMAPConnection(imap_config)    

        for conf in urlconfig:
            for url in conf.get_links():
                process_feed(imap_conn,imap_config['user'],conf.get_items(),url)

        imap_conn.disconnect()


if __name__ == "__main__":
    main()

