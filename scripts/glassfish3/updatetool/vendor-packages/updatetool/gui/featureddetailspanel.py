#!/usr/bin/env python
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

if False:    # Keep Pylint happy
    import gettext
    _ = gettext.gettext

import urllib

import wx
import wx.html

from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from common.mixins import KeywordArgsMixin
import common.utils as utils
import common.basicfeed as BF

ITEM_BACKGROUND_COLOR = wx.Color(red=242, green=245, blue=247)

class ListCtrlAutoWidth(wx.ListCtrl, ListCtrlAutoWidthMixin, KeywordArgsMixin):

    def __init__(self, parent, ident, *args, **kwargs):
        KeywordArgsMixin.__init__(self)
        wx.ListCtrl.__init__(self, parent, ident, *args, **kwargs)
        ListCtrlAutoWidthMixin.__init__(self)


class FeaturedDetailsPanel(wx.Panel):

    _ = wx.GetTranslation

    def __init__(self, *args, **kwds):

        wx.Panel.__init__(self, *args, **kwds)

        self.entries = None
        self.install_handler = None
        self.info_handler = None
        self.title = None
        self.icon = None

        # Dictionary to hold cachedimages
        self.image_cache = { }

        splitter = wx.SplitterWindow(self, -1)

        # List Control: New Software
        self.list_ctrl = ListCtrlAutoWidth(splitter, -1, style=wx.LC_REPORT)
        self.list_ctrl.SetMinSize(wx.Size(200, 125))

        columns = \
                  [ # Label             Width             Format
                   (_("New Software"),  400,              wx.LIST_FORMAT_LEFT),
                   (_("Version"),       120,              wx.LIST_FORMAT_LEFT),
                   (_("Size"),           60,               wx.LIST_FORMAT_LEFT)
                  ]

        for col, headings in enumerate(columns):
            self.list_ctrl.InsertColumn(col,
                                    heading=headings[0],
                                    format=headings[2],
                                    width=headings[1])

        # We set a size on the panel since when we did not do so we
        # had a crash on the Mac
        self.description_panel = wx.Panel(splitter, -1, size=(200,24))
        self.description_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.description_panel.SetSizer(self.description_panel_sizer)

        # Icon
        self.icon = wx.StaticBitmap(self.description_panel, -1)
        # Title
        self.title = wx.StaticText(self.description_panel, -1, " ")
        utils.make_bold(self.title)
        utils.make_bigger(self.title, 2)

        self.title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.title_sizer.Add(self.icon, 0, wx.ALIGN_CENTER|wx.RIGHT, 12)
        self.title_sizer.Add(self.title, 0,wx.ALIGN_CENTER)
        self.title_sizer.Layout()

        # HTML description
        self.desc_html = InfoHtmlWindow(self.description_panel, style=wx.BORDER_NONE)
        #self.desc_html.SetMinSize((-1, 300))
        bgcolor = self.desc_html.GetBackgroundColour()
        self.description_panel.SetBackgroundColour(bgcolor)

        # Bottom buttons
        # We put the buttons in a panel so we can set the background color
        # We set a size on the panel since when we did not do so we
        # had a crash on the Mac
        self.button_panel = wx.Panel(self.description_panel, -1, size=(200,24))
        self.button_panel.SetBackgroundColour(bgcolor)

        self.install_button = wx.Button(self.button_panel, -1, _("Install..."))
        self.info_button = wx.Button(self.button_panel, -1, _("Learn More"))

        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer.AddStretchSpacer(1)
        self.button_sizer.Add(self.info_button, 0,
                                wx.TOP|wx.BOTTOM|wx.LEFT|wx.ALIGN_TOP, 8)
        self.button_sizer.Add(self.install_button, 0,
                                wx.TOP|wx.BOTTOM|wx.LEFT|wx.ALIGN_TOP, 8)
        self.button_sizer.AddSpacer(12)
        self.button_panel.SetSizer(self.button_sizer)

        self.description_panel_sizer.Add(self.title_sizer, 0, wx.ALL, 8)
        self.description_panel_sizer.Add(self.desc_html, 1, wx.EXPAND)
        self.description_panel_sizer.Add(self.button_panel, 0, wx.EXPAND)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(splitter, 1, wx.EXPAND)
        #self.sizer.Add(self.button_panel, 0, wx.EXPAND)

        self.SetSizer(self.sizer)

        splitter.SplitHorizontally(self.list_ctrl, self.description_panel, 125)

        self.list_ctrl.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick,
                            self.list_ctrl)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListItemSelected,
                            self.list_ctrl)
        self.Bind(wx.EVT_BUTTON, self.OnInstall, self.install_button)
        self.Bind(wx.EVT_BUTTON, self.OnInfo, self.info_button)

        self.sizer.Layout()


    def set_title(self, title=None, bmp=None):
        if title is not None:
            self.title.SetLabel(title)
            self.title.Show()
        else:
            self.title.Hide()
        if bmp is not None:
            self.icon.SetBitmap(bmp)
            self.icon.Show()
        else:
            self.icon.Hide()
        self.title_sizer.Layout()
        self.description_panel.Refresh()


    def set_install_handler(self, handler):
        '''
        Set an event handler for the "Install" button. The event
        will contain the feed entry for the currently selected application
        feed.
        '''
        self.install_handler = handler


    def set_info_handler(self, handler):
        '''
        Set an event handler for the "Learn More" button. The event
        will contain the feed entry for the currently selected application
        feed.
        '''
        self.info_handler = handler


    def OnInstall(self, event):
        if self.install_handler is not None:
            event.SetClientData(self.get_selected_entry())
            self.install_handler(event)


    def OnInfo(self, event):
        if self.info_handler is not None:
            event.SetClientData(self.get_selected_entry())
            self.info_handler(event)


    def delete_entries(self):
        self.list_ctrl.DeleteAllItems()
        self.desc_html.SetPage("")


    def load_entries(self, entries):
        '''
        Load feed entries into the list control.
        '''
        self.entries = entries

        if entries is None or len(entries) == 0:
            self.delete_entries()
            self.desc_html.SetPage("<br><h5>" +
                                   _("No software currently available") +
                                   "</h5>")
            self.set_title(title="")
            self.install_button.Disable()
            self.info_button.Disable()
            return

        for row, e in enumerate(entries):
            index = self.list_ctrl.InsertStringItem(row, " " + e[BF.TITLE])
            self.list_ctrl.SetStringItem(index, 1, e[BF.VERSION])
            if utils.is_integer_string(e[BF.SIZE]):
                self.list_ctrl.SetStringItem(index, 2,
                    utils.readable_size(int(e[BF.SIZE]) * 1024))
            else:
                self.list_ctrl.SetStringItem(index, 2, " ")
            self.list_ctrl.SetItemData(index, row)
            if index % 2 == 0:
                self.list_ctrl.SetItemBackgroundColour(index,
                                                      ITEM_BACKGROUND_COLOR)

        # Select first entry
        self.list_ctrl.SetItemState(0, wx.LIST_STATE_SELECTED,
                                       wx.LIST_STATE_SELECTED)
        self.list_ctrl.SetItemState(0, wx.LIST_STATE_FOCUSED,
                                       wx.LIST_STATE_FOCUSED)
        if entries[0][BF.APP_TYPE] == "addon":
            self.set_column_label(0, _("New Add-ons"))
        else:
            self.set_column_label(0, _("New Applications"))

        return


    def set_column_label(self, column_number, label):
            item = wx.ListItem()
            item.SetText(label)
            item.SetMask(wx.LIST_MASK_TEXT)
            self.list_ctrl.SetColumn(column_number, item)


    def get_selected_entry(self):
        n = self.list_ctrl.GetFirstSelected()
        if n > -1:
            return self.entries[n]


    def _get_default_bmp(self):
        return utils.get_image("package-24x24.png")


    def _create_image_from_URL(self, image_url):
        '''
        Create an image bitmap from a URL. The URL must point to a PNG
        bitmap. Returns None if there was a problem loading the bitmap
        '''

        if self.image_cache.has_key(image_url):
            return self.image_cache[image_url]

        try:
            # Load image from URL
            stream = urllib.urlopen(image_url)
            image = wx.ImageFromStream(stream, type=wx.BITMAP_TYPE_PNG)
            stream.close()
            bmp = wx.BitmapFromImage(image)
            self.image_cache[image_url] = bmp
            return bmp
        except Exception, e:
            utils.logger.debug(_("Could not load icon %s") % image_url)
            utils.logger.debug(utils.format_trace())
            # Go ahead and cache None so we don't try to use the bad url again
            self.image_cache[image_url] = None

        return None


    def OnClick(self, event):
        wx.MessageBox("Go away, come back another day.", style=wx.OK | wx.ICON_INFORMATION, caption="Sun Software Update", parent=self)


    def OnColClick(self, evt):
        self.lists["updates"]._sort_col = evt.GetColumn()
        evt.Skip()


    def OnListItemSelected(self, evt):
        list = evt.GetEventObject()
        item = evt.GetItem()
        entry = self.entries[item.GetData()]

        bmp = None
        if entry.has_key(BF.ICON_URL) and entry[BF.SUMMARY_HEADER][BF.USE_ICON]:
            i_url = entry[BF.ICON_URL]
            bmp = self._create_image_from_URL(i_url)
            if bmp is None:
                bmp = self._get_default_bmp()
        title = None
        if entry.has_key(BF.TITLE) and entry[BF.SUMMARY_HEADER][BF.USE_TITLE]:
            title = entry[BF.TITLE]
        self.set_title(title=title, bmp=bmp)

        desc = self._generate_description(entry)
        self.desc_html.SetPage(desc)

        if entry[BF.APP_TYPE] in ("pkg"):
            # If IPS based application then show Install
            self.install_button.Enable()
            self.install_button.SetLabel(_("Install..."))
        elif entry[BF.APP_TYPE] in ("addon"):
            # We don't support add-on install yet
            self.install_button.Enable()
            self.install_button.SetLabel(_("Install..."))
        else:
            # Other software show download
            self.install_button.Enable()
            self.install_button.SetLabel(_("Download..."))

        self.info_button.Enable()
        self.button_sizer.RecalcSizes()
        self.button_sizer.Layout()
        self.desc_html
        self.desc_html.Layout()
        self.description_panel_sizer.RecalcSizes()
        self.description_panel_sizer.Layout()
        self.sizer.Layout()
        evt.Skip()


    def _generate_description(self, entry):
        if entry.has_key(BF.SUMMARY):
            return entry[BF.SUMMARY]
        return " "


class InfoHtmlWindow(wx.html.HtmlWindow):

    def __init__(self, parent, *args, **kwargs):
        wx.html.HtmlWindow.__init__(self, parent, *args, **kwargs)


    def OnLinkClicked(self, link):
        print "wx.LaunchDefaultBrowser(): " + link.GetHref()
        wx.LaunchDefaultBrowser(link.GetHref())
