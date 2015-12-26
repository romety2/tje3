# -*- coding: utf-8 -*-
#
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS HEADER.
#
# Copyright (c) 2009-2010 Oracle and/or its affiliates. All rights reserved.
#
# The contents of this file are subject to the terms of either the GNU
# General Public License Version 2 only ("GPL") or the Common Development
# and Distribution License("CDDL") (collectively, the "License").  You
# may not use this file except in compliance with the License.  You can
# obtain a copy of the License at
# https://glassfish.dev.java.net/public/CDDL+GPL_1_1.html
# or packager/legal/LICENSE.txt.  See the License for the specific
# language governing permissions and limitations under the License.
#
# When distributing the software, include this License Header Notice in each
# file and include the License file at glassfish/bootstrap/legal/LICENSE.txt.
#
# GPL Classpath Exception:
# Oracle designates this particular file as subject to the "Classpath"
# exception as provided by Oracle in the GPL Version 2 section of the License
# file that accompanied this code.
#
# Modifications:
# If applicable, add the following below the License Header, with the fields
# enclosed by brackets [] replaced by your own identifying information:
# "Portions Copyright [year] [name of copyright owner]"
#
# Contributor(s):
# If you wish your version of this file to be governed by only the CDDL or
# only the GPL Version 2, indicate your decision by adding "[Contributor]
# elects to include this software in this distribution under the [CDDL or GPL
# Version 2] license."  If you don't indicate a single choice of license, a
# recipient has the option to distribute your version of this file under
# either the CDDL, the GPL Version 2 or to extend the choice of license to
# its licensees as provided above.  However, if you add GPL Version 2 code
# and therefore, elected the GPL Version 2 license, then the option applies
# only if the new code is made subject to such option by the copyright
# holder.
#


"""Parse an Atom feed into a Featured Software dictionary"""

import sys
import threading
import urllib2
import time
import xml.dom.minidom
from xml.dom.minidom import Node
import wx

import common.utils as utils

"""
Parse an Atom feed into a data dictionary to support the Featured Software
featre. This only supports the subset of Atom used by Featured Software.
Note that the code is a bit simplistic and brute force, but should
work well enough for our simple use of Atom feeds.

The tables below list the dictionary keys values
"""

"""
Keys contained in a top level feed dictionary

Key                 Type            Description
-----------------------------------------------------------------------------
TITLE               String          Title
SUBTITLE            String          Subtitle
UPDATED             String          Update timestamp
PUBLISHED           String          Publish timestamp
ID                  String          Unique ID
RIGHTS              String          Copyright string
ICON_URL            String          URL to icon. Icon must be PNG for now
ICON_TYPE           String          Type of icon: 'png', 'jpg', 'gif'
SELF_URL            String          URL back to feed
ALT_URL             String          URL to feed description
REL_URL             String          URL to other info related to feed
ENTRIES             List of Dictionaries for entries
"""

"""
Keys contained in an entry dictionary. An entry represents a
software application or add-on.

Key                 Type            Description
-----------------------------------------------------------------------------
TITLE               String          Title
SUBTITLE            String          Subtitle
SUMMARY             String          Description of software
SUMMARY_HTML        String          Description of software in html
UPDATED             String          Update timestamp
ID                  String          Unique ID
RIGHTS              String          Copyright string
ICON_URL            String          URL to icon. Icon must be PNG for now.
ICON_TYPE           String          Type of icon: 'png', 'jpg', 'gif'
SELF_URL            String          URL to ???
ALT_URL             String          URL to alternate software description
                                    Used for "Learn More" button
REL_URL             String          URL to other info related to software
                                    Used for "Download" button
INSTALL_PATH        String          Software install path
APP_TYPE            String          'pkg', 'addon', 'other'
CATEGORIES          List of Strings represent software categories
SIZE                String          In KB
VERSION             String          Dotted decimal
PACKAGES            List of Strings of package names
PACKAGES_LANDMARK   List of Strings of package names (used as landmarks)
PREFERRED_PUBLISHER String          Name of preferred publisher
AUTHOR              Dictionary      Info about software author. Contains:
    NAME            String          Author Name
    URI             String          Authpr URI
PUBLISHERS          List of publisher Dictinaries containing:
    NAME            String          publisher name
    ORIGIN          String          URL to publisher repository
    PREFERRED       Boolean         True if this publisher is preferred
    DISABLED        Boolean         True if this publisher is disabled
SUMMARY_HEADER      Dictionary      Controls display of summary header in GUI
    USE_ICON        Boolean         True to display icon. Default: True
    USE_TITLE       Boolean         True to display title. Default: True
"""

"""
Constants for strings used as keys into a feed dictionary.
See descriptions above.
"""
ALT_URL="alt_url"
APP_TYPE="app_type"
AUTHOR="author"
CATEGORIES="categories"
DISABLED="disabled"
ENTRIES="entries"
ICON_TYPE="icon_type"
ICON_URL="icon_url"
LOGO_URL="logo_url"
ID="id"
INSTALL_PATH="install_path"
NAME="name"
ORIGIN="origin"
PACKAGES_LANDMARK="packages_landmark"
PACKAGES="packages"
PREFERRED="preferred"
PREFERRED_PUBLISHER="preferred_publisher"
PUBLISHED="published"
PUBLISHERS="publishers"
REL_URL="rel_url"
RIGHTS="rights"
SELF_URL="self_url"
SIZE="size"
SUBTITLE="subtitle"
SUMMARY_HTML="summary_html"
SUMMARY="summary"
TITLE="title"
UPDATED="updated"
URI="uri"
VERSION="version"
SUMMARY_HEADER="summary_header"
USE_ICON="use_icon"
USE_TITLE="use_title"


class BasicFeed(threading.Thread):

    def __init__(self, *args, **kwds):
        threading.Thread.__init__(self, name="BasicFeed")

        self.callback = None
        self.input_url = None
        self.status_exception_info = None
        self.feed = { }
        self.debug_delay = 0
        self.dom = None

        if not 'url' in kwds:
            raise "url attribute must be supplied"

        self.input_url = kwds['url']
        del kwds['url']


    def get_url(self):
        if self.input_url is None:
            return ""
        else:
            return self.input_url


    def parse(self, callback=None):
        '''
        Start parsing the feed from the url provided in the constructure.
        Parsing will commence in another thread. When the parsing is
        complete the function specified by "callback" will be called with
        one argument which is this object (an instance of BasicFeed).
        "callback" will be called via the WX main thread. "callback" may
        be None in which case it is not called.

        The common use case is to call BasicFeed.get_feed() from the
        callback function to get the parsed feed data. If you do not
        specify a callback you may call BasicFeed.get_feed() directly
        which will block until the feed is parsed.

        Note that only the subset variant of Atom that is used by
        Update Center is supported.
        '''
        self.callback = callback
        self.start()


    def run(self):
        # Parse the feed
        try:
            self._parse_feed()
            self._validate(self.feed)
        except Exception: # , e:
            # In order to preserve the stack trace we need to save the
            # exception info, not the actual exception.
            self.status_exception_info = sys.exc_info()

        # Invoke callback (via WX main thread) if there is a callback
        if self.callback is not None:
            wx.CallAfter(self.callback, self)


    def get_feed(self):
        '''
        Return a dictionary representing the feed. If the worker thread
        is not completed yet then block until it is. If get_feed()
        is called from inside the callback function (passed
        via the call to parse()) then this method will not block since
        the parsing is complete.
        '''

        # If the thread hasn't completed yet block until it does
        if self.isAlive():
            self.join()

        # Check if an exception was thrown during the execution of the
        # working thread.
        if self.status_exception_info is not None:
            e_info = self.status_exception_info
            # Raise an exception based on the exc_info (this preserves
            # the stack trace)
            raise e_info[0], e_info[1], e_info[2]

        # All is well, return the feed dictionary
        return self.feed


    def _parse_feed(self):
        '''
        Parse the feed specified by self.input_url
        '''

        # This delay makes the parsing appear to take longer. Can be
        # useful for testing.
        if self.debug_delay > 0:
            time.sleep(self.debug_delay)

        # Open the feed URL
        input = urllib2.urlopen(self.input_url)

        # Create a dom from the input
        self.dom = xml.dom.minidom.parse(input)

        # Create a data dictionary from the DOM of the feed

        self.feed = { }
        node = self.dom.getElementsByTagName("feed")[0]

        # Get top level feed information
        n = self._get_child_by_name(node, "title")
        self.feed[TITLE] = self._get_text(n)
        n = self._get_child_by_name(node, "subtitle")
        self.feed[SUBTITLE] = self._get_text(n)
        n = self._get_child_by_name(node, "updated")
        self.feed[UPDATED] = self._get_text(n)
        n = self._get_child_by_name(node, "id")
        self.feed[ID] = self._get_text(n)
        n = self._get_child_by_name(node, "rights")
        self.feed[RIGHTS] = self._get_text(n)

        n = self._get_child_by_name(node, "icon")
        self.feed[ICON_URL] = self._get_text(n)

        n = self._get_child_by_name(node, "logo")
        self.feed[LOGO_URL] = self._get_text(n)

        nodelist = self._get_children_by_name(node, "link")
        for n in nodelist:
            # Only support rel types of 'alternate', 'self', 'related'
            rel = n.getAttribute("rel")
            href = n.getAttribute("href")
            if rel == "self":
                self.feed[SELF_URL] = href
            elif rel == "alternate":
                self.feed[ALT_URL] = href
            elif rel == "related":
                self.feed[REL_URL] = href
            else:
                pass

        # Get data for entries. Each entry is a dictionary
        nodelist = self._get_children_by_name(node, "entry")
        if nodelist and len(nodelist) > 0:
            self.feed[ENTRIES] = [self._parse_entry(input, n) for n in nodelist]

        return


    def _parse_entry(self, input, node):
        '''
        Generate a dictionary of the feed at node "node"
        '''

        e = { }
        n = self._get_child_by_name(node, "title")
        e[TITLE] = self._get_text(n)
        n = self._get_child_by_name(node, "updated")
        e[UPDATED] = self._get_text(n)
        n = self._get_child_by_name(node, "published")
        e[PUBLISHED] = self._get_text(n)
        n = self._get_child_by_name(node, "id")
        e[ID] = self._get_text(n)

        # XXX Check type and trim <summary> from HTML
        n = self._get_child_by_name(node, "summary")
        e[SUMMARY] = n.toxml()
        e[SUMMARY_HTML] = n.toxml()

        n = self._get_child_by_name(node, "author")
        e[AUTHOR] = { }
        if n is not None:
            a = e[AUTHOR]
            t_n = self._get_child_by_name(n, "name")
            a[NAME] = self._get_text(t_n)
            t_n = self._get_child_by_name(n, "uri")
            a[URI] = self._get_text(t_n)

        # Can have more than one category, so this is a list
        nodelist = self._get_children_by_name(node, "category")
        e[CATEGORIES] = [ ]
        for n in nodelist:
            # XXX do something with label
            #l = n.getAttribute("label")
            s = n.getAttribute("term")
            e[CATEGORIES].append(s)

        nodelist = self._get_children_by_name(node, "link")
        for n in nodelist:
            # Only support rel types of 'alternate', 'self', 'related'
            rel = n.getAttribute("rel")
            href = n.getAttribute("href")
            if rel == "self":
                e[SELF_URL] = href
            elif rel == "alternate":
                e[ALT_URL] = href
            elif rel == "related":
                e[REL_URL] = href
            else:
                pass

        n = self._get_child_by_name(node, "content")

        # For our Featured Software Atom feed we include XML data in the
        # <content> element to carry more metadata. Go parse that.
        # XXX should check "type"
        content = self._parse_entry_content(input, n)

        # Merge data from <content> into entry's dictionary
        e.update(content)

        return e


    def _parse_entry_content(self, input, node):
        '''
        The UC Featured Software Atom feed uses XML tags in the <content>
        section to carry additional meta-data about the software described
        by the feed entry. This method parses that into a dictionary
        '''

        e = { }

        n = self._get_child_by_name(node, "icon")
        e[ICON_URL] = self._get_text(n)

        n = self._get_child_by_name(node, "logo")
        self.feed[LOGO_URL] = self._get_text(n)

        n = self._get_child_by_name(node, "install_path")
        e[INSTALL_PATH] = self._get_text(n)
        n = self._get_child_by_name(node, "app_type")
        e[APP_TYPE] = self._get_text(n)
        n = self._get_child_by_name(node, "size")
        e[SIZE] = self._get_text(n)
        n = self._get_child_by_name(node, "version")
        e[VERSION] = self._get_text(n)

        # summary_header of form <summary_header icon="false" title="false"/>
        n = self._get_child_by_name(node, "summary_header")
        # Default attributes to True
        d = { USE_ICON : True, USE_TITLE : True }
        if n:
            use_icon_attr = n.getAttribute("icon")
            if use_icon_attr and utils.parse_bool(use_icon_attr) == False:
                d[USE_ICON] = False
            use_title_attr= n.getAttribute("title")
            if use_title_attr and utils.parse_bool(use_title_attr) == False:
                d[USE_TITLE] = False
        e[SUMMARY_HEADER] = d


        # Generate list of packages for the software described by the entry
        # Packages that are tagged as "landmark" are also kept in a second
        # list
        nodelist = self._get_children_by_name(node, "package")
        e[PACKAGES] = [ ]
        e[PACKAGES_LANDMARK] = [ ]
        for n in nodelist:
            landmark = n.getAttribute("landmark").lower()
            name = self._get_text(n)
            if utils.parse_bool(landmark) == True:
                e[PACKAGES_LANDMARK].append(name)
            else:
                e[PACKAGES].append(name)

        n = self._get_child_by_name(node, "author")
        e[AUTHOR] = { }
        if n is not None:
            a = e[AUTHOR]
            t_n = self._get_child_by_name(n, "name")
            a[NAME] = self._get_text(t_n)
            t_n = self._get_child_by_name(n, "uri")
            a[URI] = self._get_text(t_n)

        n = self._get_child_by_name(node, "preferred_publisher")
        e[PREFERRED_PUBLISHER] = self._get_text(n)

        # Generate list of publishers
        nodelist = self._get_children_by_name(node, "publisher")
        e[PUBLISHERS] = [ ]
        for n in nodelist:
            a = { }
            e[PUBLISHERS].append(a)
            a[NAME] = n.getAttribute("name")
            t_n = self._get_child_by_name(n, "origin")
            a[ORIGIN] = self._get_text(t_n)

            t_n = self._get_child_by_name(n, "disabled")
            a[DISABLED] = utils.parse_bool(self._get_text(t_n))

            a[PREFERRED] = (a[NAME] == e[PREFERRED_PUBLISHER])

        return e


    def _get_child_by_name(self, node, name):
        '''
        Get the first direct child wth a nodeName of 'name'
        Note: this only looks at direct children, it does not
        traverse the entire subtree
        '''

        children = self._get_children_by_name(node, name)
        if len(children) > 0:
            return children[0]
        else:
            return None


    def _get_children_by_name(self, node, name):
        '''
        Get all direct children with a nodeName of 'name'
        Note: this only looks at direct children, it does not
        traverse the entire subtree
        '''

        if node.hasChildNodes():
            nodelist = node.childNodes
        else:
            return None

        children = [ n for n in nodelist if n.nodeName == name ]

        return children


    def _create_image_from_URL(self, image_url, type=wx.BITMAP_TYPE_PNG):
        '''
        Return a wx.Bitmap from an image_url. 'type' should be one of
        the wx.BITMAP_TYPE_* values
        '''

        try:
            # Load image from URL
            stream = urllib2.urlopen(image_url)
            image = wx.ImageFromStream(stream, type)
            stream.close()
        except Exception: #, e:
            # XXX Fix this
            return None

        return wx.BitmapFromImage(image)


    def _get_text(self, node):
        '''
        Return the text for the element specified by node (text is kep
        as a child of the tag node)
        '''
        if node is None:
            return ""

        if node.hasChildNodes():
            nodelist = node.childNodes
        else:
            return ""

        if nodelist is None:
            return ""

        rc = ""
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc = rc + node.data
        return rc


    def _validate(self, feed):
        """
        XXX
        Need to implement this. This should examine the feed dictionary and
        ensure it's well formed to avoid runtime errors in the application
        consuming the feed.
        """
        return True


    def _dump_dom(self, dom):
        node = dom.getElementsByTagName("feed")[0]
        self._visit_node(node, 0)
        return


    def _visit_node(self, node, indent):
        self._dump_node(node, indent)

        if node.hasChildNodes():
            nodelist = node.childNodes
            for n in nodelist:
                self._visit_node(n, indent + 1)


    def set_debug_delay(self, secs):
        '''
        Sets a debug delay for the parsing code. This is used to simulate
        network delays, etc for testing.
        '''
        self.debug_delay = secs


############# Debug routines for testing and dumping DOM #################
    def _dump_node(self, node, indent):

        if node.nodeName == "summary":
            print node.toxml()

        s = "    " * indent

        print s + "+-------------------"
        print s + "| nodeName: " , node.nodeName
        print s + "| nodeType: " , self._node_type_string(node.nodeType)
        print s + "|nodeValue: " , node.nodeValue
        if node.hasAttributes():
            print s + "|attribute: "
            if node.attributes is not None:
                for i in range(node.attributes.length):
                    self._dump_node(node.attributes.item(i), indent + 1)
        print s + "+-------------------"


    def _node_type_string(self, node_type):
        if node_type == Node.ELEMENT_NODE:
            return "ELEMENT_NODE"
        if node_type == Node.ATTRIBUTE_NODE:
            return "ATTRIBUTE_NODE"
        if node_type == Node.TEXT_NODE:
            return "TEXT_NODE"
        if node_type == Node.CDATA_SECTION_NODE:
            return "CDATA_SECTION_NODE"
        if node_type == Node.ENTITY_NODE:
            return "ENTITY_NODE"
        if node_type == Node.PROCESSING_INSTRUCTION_NODE:
            return "PROCESSING_INSTRUCTION_NODE"
        if node_type == Node.COMMENT_NODE:
            return "COMMENT_NODE"
        if node_type == Node.DOCUMENT_NODE:
            return "DOCUMENT_NODE"
        if node_type == Node.DOCUMENT_TYPE_NODE:
            return "DOCUMENT_TYPE_NODE"
        if node_type == Node.NOTATION:
            return "NOTATION"

        return "unknown"


def _test(args):

    if len(args) < 1:
        print "usage: basicfeed.py <url to feed>"
        return 1

    try:
        basicfeed = BasicFeed(url=args[0])
    except Exception: #,e:
        print "ERROR: Could not open feed %s" % args[0]
        raise

    try:
        basicfeed.parse()
        feed = basicfeed.get_feed()
    except Exception: #,e:
        print "ERROR: Could not parse feed %s" % args[0]
        raise

    print feed
    return 0

if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()
    sys.exit(_test(args))

