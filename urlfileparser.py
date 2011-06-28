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

import re
import string

class URLFileParser:
    @staticmethod
    def parse(configfile):
        f = open(configfile,'r')

        confobjs = []
        confobj = URLFileConfObj()
        
        for line in f:
            if line == "\n":
                confobjs.append(confobj)
                confobj = URLFileConfObj()
            # not a comment
            elif not line.startswith('#'):
                if line.startswith('http'):
                    confobj.add_link(line.rstrip())
                else:
                    (label,item) = str.split(line,': ')
                    confobj.add_item(label,item.rstrip())


        confobjs.append(confobj)
        return confobjs

class URLFileConfObj:
    def __init__(self):
        self.items = {}
        self.links = []

        # set default data
        self.items['folder'] = 'RSS.%{channel:title}'
        self.items['type'] = 'items'
        self.items['sync'] = False
        self.items['expire'] = -1
        self.items['expire-unseen'] = False
        # not defined by default self.items['expire-folder']
        # self.items['subject'] TODO
        # self.items['from'] TODO
        

    def add_item(self,label,item):
        self.items[label] = item

    def add_link(self,link):
        self.links.append(link)

    def get_links(self):
        return self.links

    def get_items(self):
        return self.items

    def __str__(self):
        ret_str = ''

        for key in self.items.keys():
            ret_str = ret_str + key + ": " + self.items[key] + "\n"

        for link in self.links:
            ret_str = ret_str + link.__str__() + "\n"

        return ret_str

def expand_macros(feed,item,conf_items):
    macro_defns = {}
    macro_defns['%{host}'] = 'TODO'
    macro_defns['%{user}'] = 'TODO'
    macro_defns['%{rss-link}'] = feed.setdefault('href',None)
    macro_defns['%{last-modified}'] = 'TODO'
    macro_defns['%{item:link}'] = item.setdefault('link',None)
    macro_defns['%{item:title}'] = item.setdefault('title',None)
    macro_defns['%{item:description}'] = item.setdefault('description',None)
    macro_defns['%{item:dc:date}'] = item.setdefault('date',None)
    macro_defns['%{item:dc:subject}'] = 'TODO'
    macro_defns['%{item:dc:creator}'] = 'TODO'
    macro_defns['%{channel:link}'] = feed.setdefault('feed',None).\
                                     setdefault('link',None)
    macro_defns['%{channel:title}'] = feed.setdefault('feed',None).\
                                      setdefault('title',None)
    macro_defns['%{channel:description}'] = feed.setdefault('feed',None).\
                                            setdefault('description',None)
    macro_defns['%{channel:dc:date}'] = feed.setdefault('feed',None).\
                                        setdefault('date',None)

    expanded_config = {}

    for key,val in conf_items.items():
        regex = re.compile('(?P<macro>%{.*})')
        matches = regex.search(val)

        if matches is not None:
            macro_label = matches.groupdict()['macro']

            # need to escape folders
            if key == 'folder':
                macro_defns[macro_label] = string.replace(\
                    macro_defns[macro_label],'.',':')
            expanded_config[key] = string.replace(\
                conf_items[key],macro_label,macro_defns[macro_label])
        else:
            expanded_config[key] = conf_items[key]

    return expanded_config
        
