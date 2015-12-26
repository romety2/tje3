# -*- coding: utf-8 -*-
#
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS HEADER.
#
# Copyright (c) 2010 Oracle and/or its affiliates. All rights reserved.
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

from common.boot import n_
from common.fsutils import fsenc
from common.mixins import KeywordArgsMixin
import common.utils as utils
import common.ips as ips
from common import messages
from gui.mixinlistctrl import MixinListCtrl

import pkg.client.image as pkgimage
from pkg.client.api_errors import ImageNotFoundException

import wx.richtext
from wx.lib.wordwrap import wordwrap
import  wx.lib.scrolledpanel as scrolled
import os
import sys
import itertools

import gettext
if False:
    _ = gettext.gettext

HYPERLINKS = '__WXMAC__' not in wx.PlatformInfo

class AppInfoNotebook(wx.Notebook, KeywordArgsMixin):

    NOTEBOOK_TABS = {
        _("Overview"): "tab-overview-16x16.png",
        _("Files"): "tab-files-16x16.png",
        _("Dependencies"): "tab-dependencies-16x16.png",
        _("License"): "tab-license-16x16.png",
        _("Change"): "tab-change-16x16.png",
        _("Image Details"): "tab-image-details-16x16.png",
    }
    NOTEBOOK_TABS_LABELS = [
        _("Overview"),
        _("Files"),
        _("Dependencies"),
        _("License"),
        _("Change"),
        _("Image Details"),
    ]

    def __init__(self, parent, ident, *args, **kwargs):
        kwargs['style'] = wx.BK_DEFAULT
        wx.Notebook.__init__(self, parent, ident, *args, **kwargs)
        self._frame = self.GetTopLevelParent()

        # Some GTK themes offset their glyph bitmaps such that they get
        # clipped at the bottom. To compensate we make them a hair larger.
        if wx.Platform == "__WXGTK__":
            self.glyph_size = (18, 18)
        else:
            self.glyph_size = (16, 16)

        self.img_list = wx.ImageList(self.glyph_size[0], self.glyph_size[1])
        press_image_bm   = utils.create_radiobutton_bitmap(self,
                                        wx.CONTROL_CHECKED, self.glyph_size)
        self.press_image   = self.img_list.Add(press_image_bm)


    def add_rtc_page(self, title=None):
        if title:
            t = title
        else:
            t = ""
        rtc_panel = wx.Panel(self)
        _bsizer = wx.BoxSizer(wx.VERTICAL)
        rtc = wx.richtext.RichTextCtrl(rtc_panel, wx.ID_ANY, "", \
                style=wx.TE_READONLY|wx.VSCROLL|wx.NO_BORDER|wx.TAB_TRAVERSAL & (~ wx.WANTS_CHARS))

        _bsizer.Add(rtc, 1, wx.EXPAND|wx.ALL, 0)
        rtc_panel.SetSizer(_bsizer)

        if '__WXMSW__' in wx.PlatformInfo:
            # NOTE: The following only gets trigged on Non-Mac platforms
            # Mac OS X never gets this event.
            def OnKeyUp(event, win=rtc):
                key = event.GetKeyCode()
                if key in [wx.WXK_TAB, wx.WXK_NUMPAD_TAB]:
                    flags = 0
                    if not event.ShiftDown():
                        flags |= wx.NavigationKeyEvent.IsForward
                    win.GetParent().GetParent().Navigate(flags)
                else:
                    event.Skip()

            rtc.Bind(wx.EVT_KEY_UP, OnKeyUp, rtc)

        self.AddPage(rtc_panel, t, imageId=self.NOTEBOOK_TABS_LABELS.index(t))
        return rtc


    def add_image_details_page(self):
        self.image_details_pane = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.NO_BORDER)
        self.image_details = scrolled.ScrolledPanel(self.image_details_pane, -1, style = wx.TAB_TRAVERSAL)
        if wx.Platform != "__WXMSW__":
            self.image_details.SetBackgroundColour(wx.WHITE)

        self.image_title = wx.StaticText(self.image_details, -1)
        myfont = self.image_title.GetFont()
        myfont.SetWeight(wx.BOLD)
        self.image_title.SetFont(myfont)

        self.image_desc = wx.StaticText(self.image_details, -1)

        self.image_path_label = wx.StaticText(self.image_details, -1, _("Image Directory:"))
        self.image_path_label.SetFont(myfont)
        self.image_path = wx.StaticText(self.image_details, -1)

        self.image_repos_label = wx.StaticText(self.image_details, -1, _("Software Sources:"))
        self.image_repos_label.SetFont(myfont)
        self.image_repos = MixinListCtrl(self.image_details, -1, style=wx.LC_REPORT|wx.NO_BORDER)
        self.image_repos.InsertColumn(0, _("Publisher"), format=wx.LIST_FORMAT_LEFT, width=180)
        self.image_repos.InsertColumn(1, _("Preferred"))
        self.image_repos.InsertColumn(2, _("Repository URL"))
        self.image_repos.SetImageList(self.img_list, wx.IMAGE_LIST_SMALL)

        self.image_details_button = wx.Button(self.image_details, 20, messages.EDIT_PROPERTIES_LABEL, (20, 20))
        self.image_details_button.SetToolTipString(messages.EDIT_PROPERTIES_TOOLTIP)

        self.image_details_sizer = wx.BoxSizer(wx.VERTICAL)
        self.image_details_sizer.Add(self.image_title, 0, wx.EXPAND|wx.ALL, 4)
        self.image_details_sizer.Add(self.image_desc, 0, wx.EXPAND|wx.ALL, 4)

        image_details_grid_sizer = wx.FlexGridSizer(3, 2, 0, 4)
        image_details_grid_sizer.Add(self.image_path_label, 0, wx.ALL|wx.ALIGN_RIGHT, 4)
        image_details_grid_sizer.Add(self.image_path, 0, wx.EXPAND|wx.ALL, 4)
        image_details_grid_sizer.Add(self.image_repos_label, 0, wx.ALL|wx.ALIGN_RIGHT, 4)
        image_details_grid_sizer.Add(self.image_repos, 0, wx.EXPAND|wx.ALL, 4)
        image_details_grid_sizer.AddSpacer(12)
        image_details_grid_sizer.Add(self.image_details_button, 0, wx.ALL|wx.ALIGN_RIGHT, 4)
        image_details_grid_sizer.AddGrowableCol(1)
        image_details_grid_sizer.AddGrowableRow(1)
        image_details_grid_sizer.SetItemMinSize(self.image_repos, 200, 120)

        self.image_details_sizer.Add(image_details_grid_sizer, 0, wx.EXPAND|wx.ALL, 4)
        self.image_details.SetSizer(self.image_details_sizer)

        # Caution: Since SetupScrolling() includes a call to wx.CallAfter(),
        # you need to ensure that wx.YieldIfNeeded() is called prior to
        # the scrolled panel object being deleted.  Otherwise, you will
        # encounter exception  traces on all platforms and perhaps a core
        # dump on Solaris 10.  A call to wx.YieldIfNeeded() has been added to
        # update_image_view() in mainframe.py to ensure that all callbacks
        # are processed prior to performing another rendering of the image
        # details tab (which entails removal of the scrolled window pane
        # object).
        #
        # Traceback (most recent call last):
        # File "wx/_core.py", line 14550, in <lambda>
        # File "wx/lib/scrolledpanel.py", line 74, in _SetupAfter
        # File "wx/_core.py", line 14500, in __getattr__
        # wx._core.PyDeadObjectError: The C++ part of the ScrolledPanel object has been deleted, attribute access no longer allowed.

        self.image_details.SetupScrolling(scroll_x=True, scroll_y=True, rate_x=10, rate_y=10)

        self.image_details_pane_sizer = wx.BoxSizer(wx.VERTICAL)
        self.image_details_pane_sizer.Add(self.image_details, 1, wx.EXPAND, 0)
        self.image_details_pane.SetSizer(self.image_details_pane_sizer)
        self.AddPage (self.image_details_pane, _("Image Details"), imageId=self.NOTEBOOK_TABS_LABELS.index(_("Image Details")))

        return


    def add_comp_overview_page(self):
        # AppInfoNotebook
        #   comp_overview_pane                          <Panel>
        #   (comp_overview_pane_sizer)
        #       comp_overview                           <ScrolledPanel>
        #       (comp_overview_sizer)                   <BoxSizer>
        #           comp_desc
        #           grid_panel
        #           (comp_overview_grid_sizer)
        #               comp_name_label             comp_name
        #               comp_version_label          comp_version
        #               comp_size_label             comp_size
        #               comp_pub_label              comp_pub
        #               comp_detailed_urls_label     comp_detailed_urls_panel
        #                                           (comp_detailed_urls_sizer)
        #               comp_source_label           comp_source
        #               comp_project_url_label      comp_project_url <HyperlinkCtrl>
        #               comp_maintainer_url_label   comp_maintainer_url
        #
        #
        self.comp_overview_pane = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.NO_BORDER)
        self.comp_overview = scrolled.ScrolledPanel(self.comp_overview_pane, -1, style=wx.TAB_TRAVERSAL)

        bgcolor = None
        if wx.Platform != "__WXMSW__":
            bgcolor = wx.WHITE
            self.comp_overview.SetBackgroundColour(bgcolor)

        self.comp_desc = wx.StaticText(self.comp_overview, -1)

        self.grid_panel = wx.Panel(self.comp_overview, -1, style=wx.TAB_TRAVERSAL|wx.NO_BORDER)
        if bgcolor is not None:
            self.grid_panel.SetBackgroundColour(bgcolor)
        self.comp_name_label = wx.StaticText(self.grid_panel, -1, _("Package Name:"))
        myfont = self.comp_name_label.GetFont()
        myfont.SetWeight(wx.BOLD)
        self.comp_name_label.SetFont(myfont)
        self.comp_name = wx.StaticText(self.grid_panel, -1)

        self.comp_version_label = wx.StaticText(self.grid_panel, -1, _("Version:"))
        self.comp_version_label.SetFont(myfont)
        self.comp_version = wx.StaticText(self.grid_panel, -1)

        self.comp_size_label = wx.StaticText(self.grid_panel, -1, _("Installed Size:"))
        self.comp_size_label.SetFont(myfont)
        self.comp_size = wx.StaticText(self.grid_panel, -1)

        self.comp_pub_label = wx.StaticText(self.grid_panel, -1, _("Published:"))
        self.comp_pub_label.SetFont(myfont)
        self.comp_pub = wx.StaticText(self.grid_panel, -1)

        self.comp_detailed_urls_label = wx.StaticText(self.grid_panel, -1,
                                                        _("Details:"))
        self.comp_detailed_urls_label.SetFont(myfont)
        self.comp_detailed_urls_panel = wx.Panel(self.grid_panel, -1, style=wx.TAB_TRAVERSAL|wx.NO_BORDER)
        if bgcolor is not None:
            self.comp_detailed_urls_panel.SetBackgroundColour(bgcolor)
        self.comp_detailed_urls_sizer = wx.BoxSizer(wx.VERTICAL)
        self.comp_detailed_urls_panel.SetSizer(self.comp_detailed_urls_sizer)

        self.comp_source_label = wx.StaticText(self.grid_panel, -1, _("Source:"))
        self.comp_source_label.SetFont(myfont)
        self.comp_source = wx.StaticText(self.grid_panel, -1)

        self.comp_id_label = wx.StaticText(self.grid_panel, -1, _("Unique Identifier:"))
        self.comp_id_label.SetFont(myfont)
        self.comp_id = wx.StaticText(self.grid_panel, -1)

        self.comp_project_url_label = wx.StaticText(self.grid_panel, -1,
                                                        _("Project:"))
        self.comp_project_url_label.SetFont(myfont)

        if HYPERLINKS:
            self.comp_project_url = wx.HyperlinkCtrl(self.grid_panel, -1,
                            style=wx.HL_ALIGN_LEFT|wx.NO_BORDER|wx.HL_CONTEXTMENU,
                            label=" ", url="")
        else:
            self.comp_project_url = wx.StaticText(self.grid_panel, -1, "")

        if bgcolor is not None:
            self.comp_project_url.SetBackgroundColour(bgcolor)

        self.comp_maintainer_url_label = wx.StaticText(self.grid_panel, -1,
                                                        _("Maintainer:"))
        self.comp_maintainer_url_label.SetFont(myfont)
        if HYPERLINKS:
            self.comp_maintainer_url = wx.HyperlinkCtrl(self.grid_panel, -1,
                            style=wx.HL_ALIGN_LEFT|wx.NO_BORDER|wx.HL_CONTEXTMENU,
                            label=" ", url="")
        else:
            self.comp_maintainer_url = wx.StaticText(self.grid_panel, -1,
                            "")
        if bgcolor is not None:
            self.comp_maintainer_url.SetBackgroundColour(bgcolor)

        self.comp_overview_sizer = wx.BoxSizer(wx.VERTICAL)
        self.comp_overview_sizer.Add(self.comp_desc, 0, wx.ALL|wx.EXPAND, 4)

        self.comp_overview_grid_sizer = wx.FlexGridSizer(9, 2, 0, 4)

        self.comp_overview_grid_sizer.Add(self.comp_name_label, 0, wx.ALL|wx.ALIGN_RIGHT, 4)
        self.comp_overview_grid_sizer.Add(self.comp_name, 0, wx.EXPAND|wx.ALL, 4)
        self.comp_overview_grid_sizer.Add(self.comp_version_label, 0, wx.ALL|wx.ALIGN_RIGHT, 4)
        self.comp_overview_grid_sizer.Add(self.comp_version, 0, wx.EXPAND|wx.ALL, 4)
        self.comp_overview_grid_sizer.Add(self.comp_size_label, 0, wx.ALL|wx.ALIGN_TOP|wx.ALIGN_RIGHT, 4)
        self.comp_overview_grid_sizer.Add(self.comp_size, 0, wx.EXPAND|wx.ALL, 4)
        self.comp_overview_grid_sizer.Add(self.comp_pub_label, 0, wx.ALL|wx.ALIGN_RIGHT, 4)
        self.comp_overview_grid_sizer.Add(self.comp_pub, 0, wx.EXPAND|wx.ALL, 4)
        self.comp_overview_grid_sizer.Add(self.comp_detailed_urls_label, 0, wx.ALL|wx.ALIGN_TOP|wx.ALIGN_RIGHT, 4)
        self.comp_overview_grid_sizer.Add(self.comp_detailed_urls_panel, 0, wx.EXPAND|wx.ALL, 4)
        self.comp_overview_grid_sizer.Add(self.comp_source_label, 0, wx.ALL|wx.ALIGN_RIGHT, 4)
        self.comp_overview_grid_sizer.Add(self.comp_source, 0, wx.EXPAND|wx.ALL, 4)
        self.comp_overview_grid_sizer.Add(self.comp_id_label, 0, wx.ALL|wx.ALIGN_TOP|wx.ALIGN_RIGHT, 4)
        self.comp_overview_grid_sizer.Add(self.comp_id, 0, wx.EXPAND|wx.ALL, 4)

        self.comp_overview_grid_sizer.Add(self.comp_project_url_label, 0, wx.ALL|wx.ALIGN_TOP|wx.ALIGN_RIGHT, 4)
        self.comp_overview_grid_sizer.Add(self.comp_project_url, 0, wx.EXPAND|wx.ALL, 4)
        self.comp_overview_grid_sizer.Add(self.comp_maintainer_url_label, 0, wx.ALL|wx.ALIGN_TOP|wx.ALIGN_RIGHT, 4)
        self.comp_overview_grid_sizer.Add(self.comp_maintainer_url, 0, wx.EXPAND|wx.ALL, 4)
        self.comp_overview_grid_sizer.AddGrowableCol(1)
        self.grid_panel.SetSizer(self.comp_overview_grid_sizer)

        self.comp_overview_sizer.Add(self.grid_panel, 0, wx.EXPAND|wx.ALL, 4)
        self.comp_overview.SetSizer(self.comp_overview_sizer)
        self.comp_overview.SetupScrolling(scroll_x=True, scroll_y=True, rate_x=10, rate_y=10)

        self.comp_overview_pane_sizer = wx.BoxSizer(wx.VERTICAL)
        self.comp_overview_pane_sizer.Add(self.comp_overview, 1, wx.EXPAND, 0)
        self.comp_overview_pane.SetSizer(self.comp_overview_pane_sizer)
        self.AddPage (self.comp_overview_pane, _("Overview"), imageId=self.NOTEBOOK_TABS_LABELS.index(_("Overview")))


        # NOTE: The following only gets trigged on Non-Mac platforms
        # Mac OS X never gets this event.
        def OnKeyUp(event, win=self.comp_overview_pane):
            key = event.GetKeyCode()
            if key in [wx.WXK_TAB, wx.WXK_NUMPAD_TAB]:
                if event.ControlDown():
                    if event.ShiftDown():
                        win.GetParent().AdvanceSelection(False)
                    else:
                        win.GetParent().AdvanceSelection(True)
                else:
                    flags = 0
                    if not event.ShiftDown():
                        flags |= wx.NavigationKeyEvent.IsForward
                    win.GetParent().Navigate(flags)
            else:
                event.Skip()

        self.comp_overview_pane.Bind(wx.EVT_KEY_UP, OnKeyUp, self.comp_overview_pane)

        return


    def _rtc_fmt_pair(self, rtc, key, value):
        rtc.BeginBold()
        rtc.WriteText("%s:" % key)
        rtc.EndBold()
        rtc.WriteText(" %s" % utils.to_unicode(value))
        rtc.Newline()


    def _set_images_list(self):
        """Loads images to be used by the Notebook Tabs"""

        img_list = wx.ImageList(16, 16)
        for t  in self.NOTEBOOK_TABS_LABELS:
            img_list.Add(utils.get_image(self.NOTEBOOK_TABS[t]))
        self.AssignImageList(img_list)


    def describe_component(self, imagedir, fmri):
        self.Show(False)
        if imagedir is None or fmri is None: # Called too early or incorrectly
            self.Show(True)
            return
        if self.GetPageCount() > 0:
            self.DeleteAllPages()

        self._set_images_list()
        self.add_comp_overview_page()
        bgcolor = None
        if wx.Platform != "__WXMSW__":
            bgcolor = self.comp_overview.GetBackgroundColour()

        for tab in [_("Files"), _("Dependencies"), _("License")]:
            rtc_tab = self.add_rtc_page(tab)
            rtc_tab.list_fmri = fmri
            rtc_tab.listed_fmri = None

        try:
            self._frame.set_status(_("Confirming image..."))
            img = pkgimage.Image()
            img.history.client_name = 'updatetool'
            img.history.operation_name = 'list'
            img.find_root(fsenc(imagedir))
            if img.type != pkgimage.IMG_USER:
                self._frame.set_status("")
                raise AssertionError("Not a user image")
            self._frame.set_status(_("Loading image configuration..."))
            img.load_config()

            self._frame.set_status(_("Getting manifest for %s...") % fmri)
            manifest = img.get_manifest(fmri)
            self._frame.set_status("")
            pub, name, ver = ips.get_fmri_info(manifest.fmri)
            self.description = manifest.get('pkg.summary', "")
            if not self.description or self.description == "":
                self.description = name

            # Show optional description_long as summary when available
            long_desc = manifest.get('pkg.description', "")
            if not long_desc or long_desc == "":
                long_desc = manifest.get('description_long', "")

            if long_desc and long_desc != "":
                self.comp_desc.SetLabel(wordwrap(long_desc, self.GetSize().GetWidth() - 60, wx.ClientDC(self)))

            self.comp_name.SetLabel(name)
            self.comp_version.SetLabel("%s-%s" % (ver.release, ver.branch))
            self.comp_size.SetLabel("%s bytes (%s)" % (manifest.get_size(), utils.readable_size(manifest.get_size())))
            self.comp_pub.SetLabel(ver.get_timestamp().strftime("%x"))
            self.comp_source.SetLabel(pub)
            self.comp_id.SetLabel("%s" % fmri)

            # Check if there is a detailed URL list. At the time of this
            # writing it is not clear if the attribute will use an underscore
            # or a dash -- so we accept both
            url_str = manifest.get('pkg.detailed_url', None)
            if url_str is None or len(url_str) == 0:
                url_str = manifest.get('pkg.detailed-url', None)
            self.comp_detailed_urls_sizer.Clear(deleteWindows=True)
            if url_str and len(url_str) > 0:
                url_list = url_str.split()
                for url in url_list:
                    if HYPERLINKS:
                        link = wx.HyperlinkCtrl(self.comp_detailed_urls_panel, -1,
                               style=wx.HL_ALIGN_LEFT|wx.NO_BORDER|wx.HL_CONTEXTMENU,
                               label=url, url=url)
                    else:
                        link = wx.StaticText(self.comp_detailed_urls_panel, -1,
                               url)
                    if bgcolor is not None:
                        link.SetBackgroundColour(bgcolor)
                    self.comp_detailed_urls_sizer.Add(link, 0, wx.EXPAND, 0)
                self.comp_overview_grid_sizer.Show(self.comp_detailed_urls_label)
                self.comp_overview_grid_sizer.Show(self.comp_detailed_urls_panel)
            else:
                self.comp_detailed_urls_sizer.Add(wx.Panel(self.comp_detailed_urls_panel, -1, style=wx.TAB_TRAVERSAL), 0, wx.EXPAND, 0)
                self.comp_overview_grid_sizer.Hide(self.comp_detailed_urls_label)
                self.comp_overview_grid_sizer.Hide(self.comp_detailed_urls_panel)

            self.comp_detailed_urls_sizer.Layout()

            url = manifest.get('info.upstream_url', None)
            if url is None or len(url) == 0:
                url = manifest.get('info.upstream-url', None)
            if url and len(url) > 0:
                self.comp_project_url.SetLabel(url)
                if HYPERLINKS:
                    self.comp_project_url.SetURL(url)
                self.comp_overview_grid_sizer.Show(self.comp_project_url_label)
                self.comp_overview_grid_sizer.Show(self.comp_project_url)
            else:
                self.comp_overview_grid_sizer.Hide(self.comp_project_url_label)
                self.comp_overview_grid_sizer.Hide(self.comp_project_url)

            url = manifest.get('info.maintainer_url', None)
            if url is None or len(url) == 0:
                url = manifest.get('info.maintainer-url', None)
            if url and len(url) > 0:
                self.comp_maintainer_url.SetLabel(url)
                if HYPERLINKS:
                    self.comp_maintainer_url.SetURL(url)
                self.comp_overview_grid_sizer.Show(self.comp_maintainer_url_label)
                self.comp_overview_grid_sizer.Show(self.comp_maintainer_url)
            else:
                self.comp_overview_grid_sizer.Hide(self.comp_maintainer_url_label)
                self.comp_overview_grid_sizer.Hide(self.comp_maintainer_url)

            self.comp_overview_grid_sizer.Layout()
            self.comp_overview_sizer.Layout()
            self.Show(True)

        except:
            self._frame.set_status("")
            utils.logger.error(utils.format_trace())

        def OnNotebookPageChanged(event, frame=self._frame):
            idx = event.GetSelection()
            if idx < 1:
                event.Skip()
                return
            win = event.GetEventObject()
            rtc = win.GetPage(idx).GetChildren()[0]
            if idx == 1:
                if not hasattr(rtc, 'listed_fmri') or rtc.listed_fmri != rtc.list_fmri:
                    wx.BeginBusyCursor()
                    rtc.SetEditable(False)
                    rtc.Freeze()
                    rtc.Clear()

                    rtc.BeginParagraphSpacing(0, 20)
                    try:
                        frame.set_status(_("Confirming image..."))
                        img = pkgimage.Image()
                        img.history.client_name = 'updatetool'
                        img.history.operation_name = 'list'
                        img.find_root(fsenc(imagedir))
                        if img.type != pkgimage.IMG_USER:
                            frame.set_status("")
                            raise AssertionError("Not a user image")
                        frame.set_status(_("Loading image configuration..."))
                        img.load_config()
                        frame.set_status(_("Getting manifest for %s...") % rtc.list_fmri)
                        manifest = img.get_manifest(rtc.list_fmri)
                        frame.set_status(_("Loading files details..."))
                        win._rtc_fmt_pair(rtc, _("Image Directory"), imagedir)
                        rtc.BeginLeftIndent(60)
                        text = ""
                        for index, path in enumerate(sorted(act.attrs.get('path', _("(Path unknown)")) \
                                for act in itertools.chain(manifest.gen_actions_by_type('file'),
                                    manifest.gen_actions_by_type('dir')))):
                            if not index % 100:
                                frame.set_status(_("Loading files details %d ...") % index)
                            text += path
                            text += "\n"
                        frame.set_status(_("Loading ..."))
                        rtc.WriteText(text)
                        frame.set_status("")
                        del text
                        rtc.EndLeftIndent()
                        rtc.listed_fmri = rtc.list_fmri
                    except (AssertionError, ImageNotFoundException):
                        utils.logger.error(utils.format_trace())
                        frame.set_status("")
                        rtc.EndAllStyles()
                        rtc.MoveHome()
                        rtc.BeginBold()
                        if utils.is_v1_image(fsenc(imagedir)):
                            rtc.WriteText(messages.NEW_IMAGE_MSG % {'path':imagedir})
                        elif not os.path.exists(fsenc(imagedir)):
                            rtc.WriteText(messages.INACCESSIBLE_IMAGE_REMOVE_MSG % {'path':imagedir})
                        else:
                            rtc.WriteText(messages.UNRECOGNIZED_IMAGE_REMOVE_MSG % {'path':imagedir})
                        rtc.EndBold()
                        rtc.Newline()
                        rtc.Newline()
                    except:
                        utils.logger.error(utils.format_trace())
                        frame.set_status("")
                        rtc.EndAllStyles()
                        rtc.MoveHome()
                        rtc.BeginBold()
                        rtc.WriteText(_("Error encountered while trying to display the files list for this component."))
                        rtc.EndBold()
                        rtc.Newline()
                        rtc.Newline()

                    rtc.EndParagraphSpacing()

                    rtc.Thaw()
                    rtc.MoveHome()
                    rtc.GetCaret().Hide()
                    wx.EndBusyCursor()
            elif idx == 2:
                if not hasattr(rtc, 'listed_fmri') or rtc.listed_fmri != rtc.list_fmri:
                    wx.BeginBusyCursor()
                    rtc.SetEditable(False)
                    rtc.Freeze()
                    rtc.Clear()

                    rtc.BeginParagraphSpacing(0, 20)
                    try:
                        frame.set_status(_("Confirming image..."))
                        img = pkgimage.Image()
                        img.history.client_name = 'updatetool'
                        img.history.operation_name = 'list'
                        img.find_root(fsenc(imagedir))
                        if img.type != pkgimage.IMG_USER:
                            frame.set_status("")
                            raise AssertionError("Not a user image")
                        frame.set_status(_("Loading image configuration..."))
                        img.load_config()
                        frame.set_status(_("Getting manifest for %s...") % rtc.list_fmri)
                        manifest = img.get_manifest(rtc.list_fmri)
                        frame.set_status(_("Loading dependency details..."))
                        dep_actions = list(manifest.gen_actions_by_type('depend'))
                        count = len(dep_actions)
                        if count:
                            rtc.BeginBold()
                            rtc.WriteText(n_("%(count)d dependency:", "%(count)d dependencies:", count) % {'count':count})
                            rtc.EndBold()
                            rtc.Newline()
                            rtc.BeginLeftIndent(60)
                            for dummy_dep_idx, dep_act in enumerate(dep_actions):
                                rtc.WriteText("%s" % dep_act.attrs.get('fmri', '(INVALID FMRI)'))
                                rtc.Newline()
                            rtc.EndLeftIndent()
                        else:
                            rtc.BeginBold()
                            rtc.WriteText(_("No dependencies."))
                            rtc.EndBold()
                            rtc.Newline()
                        rtc.listed_fmri = rtc.list_fmri
                        frame.set_status("")
                    except (AssertionError, ImageNotFoundException):
                        frame.set_status("")
                        rtc.EndAllStyles()
                        rtc.MoveHome()
                        rtc.BeginBold()
                        if utils.is_v1_image(fsenc(imagedir)):
                            rtc.WriteText(messages.NEW_IMAGE_MSG % {'path': imagedir})
                        elif not os.path.exists(fsenc(imagedir)):
                            rtc.WriteText(messages.INACCESSIBLE_IMAGE_REMOVE_MSG % {'path': imagedir})
                        else:
                            rtc.WriteText(messages.UNRECOGNIZED_IMAGE_REMOVE_MSG % {'path': imagedir})
                        rtc.EndBold()
                        rtc.Newline()
                        rtc.Newline()
                    except:
                        utils.logger.error(utils.format_trace())
                        frame.set_status("")
                        rtc.EndAllStyles()
                        rtc.MoveHome()
                        rtc.BeginBold()
                        rtc.WriteText(_("Error encountered while trying to display the legal list for this component."))
                        rtc.EndBold()
                        rtc.Newline()
                        rtc.Newline()

                    rtc.EndParagraphSpacing()

                    rtc.Thaw()
                    rtc.MoveHome()
                    rtc.GetCaret().Hide()
                    wx.EndBusyCursor()
            elif idx == 3:
                if not hasattr(rtc, 'listed_fmri') or rtc.listed_fmri != rtc.list_fmri:
                    wx.BeginBusyCursor()
                    rtc.SetEditable(False)
                    rtc.Freeze()
                    rtc.Clear()

                    rtc.BeginParagraphSpacing(0, 20)
                    try:
                        frame.set_status(_("Confirming image..."))
                        img = pkgimage.Image()
                        img.history.client_name = 'updatetool'
                        img.history.operation_name = 'list'
                        img.find_root(fsenc(imagedir))
                        if img.type != pkgimage.IMG_USER:
                            frame.set_status("")
                            raise AssertionError("Not a user image")
                        frame.set_status(_("Loading image configuration..."))
                        img.load_config()
                        frame.set_status(_("Getting manifest for %s...") % rtc.list_fmri)
                        manifest = img.get_manifest(rtc.list_fmri)
                        frame.set_status(_("Loading legal details..."))
                        lic_actions = list(manifest.gen_actions_by_type('license'))
                        count = len(lic_actions)
                        if count < 1:
                            rtc.BeginAlignment(wx.richtext.TEXT_ALIGNMENT_CENTRE)
                            rtc.BeginBold()
                            rtc.WriteText(_("No license is present for this component."))
                            rtc.EndBold()
                            rtc.Newline()
                            rtc.EndAlignment()
                        elif count > 1:
                            rtc.BeginAlignment(wx.richtext.TEXT_ALIGNMENT_CENTRE)
                            rtc.BeginBold()
                            rtc.WriteText(_("%d license texts.") % count)
                            rtc.EndBold()
                            rtc.Newline()
                            rtc.EndAlignment()
                        else:
                            pass
                        for lic_idx, lic_act in enumerate(lic_actions):
                            frame.set_status(_("Loading legal details %d ...") % (lic_idx + 1))
                            lic_text, lic_name, exc = ips.get_license(img, lic_act, rtc.list_fmri)
                            if lic_text:
                                lic_text = lic_text.decode('latin-1')
                            else:
                                utils.logger.error(str(exc))
                            if count > 1:
                                win._rtc_fmt_pair(rtc, _("License %d") % (lic_idx + 1), lic_name)
                            else:
                                win._rtc_fmt_pair(rtc, _("License"), lic_name)
                            rtc.Newline()
                            rtc.BeginLeftIndent(60)
                            if lic_text is None:
                                rtc.BeginBold()
                                rtc.WriteText(_("Could not fetch license text"))
                                rtc.EndBold()
                                rtc.Newline()
                            else:
                                rtc.WriteText(lic_text)
                                rtc.Newline()
                                rtc.Newline()
                            rtc.EndLeftIndent()

                        rtc.listed_fmri = rtc.list_fmri
                        frame.set_status("")
                    except (AssertionError, ImageNotFoundException):
                        frame.set_status("")
                        rtc.EndAllStyles()
                        rtc.MoveHome()
                        rtc.BeginBold()
                        if utils.is_v1_image(fsenc(imagedir)):
                            rtc.WriteText(messages.NEW_IMAGE_MSG % {'path':imagedir})
                        elif not os.path.exists(fsenc(imagedir)):
                            rtc.WriteText(messages.INACCESSIBLE_IMAGE_REMOVE_MSG % {'path':imagedir})
                        else:
                            rtc.WriteText(messages.UNRECOGNIZED_IMAGE_REMOVE_MSG % {'path':imagedir})
                        rtc.EndBold()
                        rtc.Newline()
                        rtc.Newline()
                    except:
                        utils.logger.error(utils.format_trace())
                        frame.set_status("")
                        rtc.EndAllStyles()
                        rtc.MoveHome()
                        rtc.BeginBold()
                        rtc.WriteText(_("Error encountered while trying to display the legal list for this component."))
                        rtc.EndBold()
                        rtc.Newline()
                        rtc.Newline()

                    rtc.EndParagraphSpacing()

                    rtc.Thaw()
                    rtc.MoveHome()
                    rtc.GetCaret().Hide()
                    wx.EndBusyCursor()
            else:
                # This should not happen
                pass

            event.Skip()
            return

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, OnNotebookPageChanged)


    def describe_view(self, imagedir, view):
        self.Show(False)
        if imagedir is None: # Called too early or incorrectly
            self.Show(False)
            return
        if self.GetPageCount() > 1:
            # Component tabs exist, remove them
            self.DeleteAllPages()
        if self.GetPageCount() == 0:
            # No tabs exist, add image details tab
            self._set_images_list()
            self.add_image_details_page()
        else:
            # We'll bind it anew if it was bound before to Remove Entry or Edit Properties
            self.image_details.Unbind(wx.EVT_BUTTON)

        self.image_details_button.SetLabel(messages.EDIT_PROPERTIES_LABEL)
        self.image_details_button.SetToolTipString(messages.EDIT_PROPERTIES_TOOLTIP)
        self.image_details.Bind(wx.EVT_BUTTON, self._frame.OnEditImage, self.image_details_button)

        if imagedir:
            try:
                # Should consider displaying either the generic installed image
                # icon or support art work on a per image basis.
                #desc.WriteImage(utils.get_image_png("view-installed-image-24x24.png"))

                title = ips.get_image_title(fsenc(imagedir), opname='list')
                self.image_title.SetLabel(title)

                idesc = ips.get_image_description(fsenc(imagedir), opname='list')
                if idesc != "":
                    self.image_desc.SetLabel(wordwrap(idesc, self.GetSize().GetWidth() - 60, wx.ClientDC(self)))
                else:
                    self.image_desc.SetLabel(_("No description available."))

                self.image_path.SetLabel(imagedir)

                img = pkgimage.Image()
                img.history.client_name = 'updatetool'
                img.history.operation_name = 'list'
                img.find_root(fsenc(imagedir))
                if img.type != pkgimage.IMG_USER:
                    raise AssertionError("Not a user image")
                img.load_config()
                self.image_details_sizer.ShowItems(True)

                preferred_publisher = img.get_preferred_publisher()
                self.image_repos.DeleteAllItems()

                # sort by publisher name first
                pubs = list(img.gen_publishers(inc_disabled = True))
                pubs.sort(key=lambda k: k['prefix'])

                # Display preferred publisher first.
                for pub in pubs:
                    if pub["prefix"] == preferred_publisher:
                        index = self.image_repos.InsertStringItem(sys.maxint, pub["prefix"])
                        self.image_repos.SetItemColumnImage(index, 1, self.press_image)
                        self.image_repos.SetStringItem(index, 2, pub["origin"])

                # display non-preferred active repo entries
                for pub in pubs:
                    if pub["prefix"] != preferred_publisher and not pub["disabled"]:
                        index = self.image_repos.InsertStringItem(sys.maxint, pub["prefix"])
                        self.image_repos.SetStringItem(index, 1, " ")
                        self.image_repos.SetStringItem(index, 2, pub["origin"])

                # display non-preferred inactive repo entries
                for pub in pubs:
                    if pub["prefix"] != preferred_publisher and pub["disabled"]:
                        index = self.image_repos.InsertStringItem(sys.maxint, pub["prefix"])
                        self.image_repos.SetStringItem(index, 1, " ")
                        self.image_repos.SetStringItem(index, 2, pub["origin"])
                        self.image_repos.SetItemTextColour(index, wx.LIGHT_GREY)

                self.image_details_sizer.Layout()
                self.Show(True)

            except:
                self.image_details_sizer.ShowItems(False)
                self.image_details_button.SetLabel(messages.REMOVE_ENTRY_LABEL)
                self.image_details_button.SetToolTipString(messages.REMOVE_ENTRY_TOOLTIP)
                self.image_details.Bind(wx.EVT_BUTTON, self._frame.OnCloseImage, self.image_details_button)
                if utils.is_v1_image(fsenc(imagedir)):
                    self.image_title.SetLabel(messages.INCOMPATIBLE_IMAGE_LABEL)
                    self.image_desc.SetLabel(wordwrap(messages.NEW_IMAGE_MSG % {'path':imagedir},
                        self.GetSize().GetWidth() - 60, wx.ClientDC(self)))
                elif not os.path.exists(fsenc(imagedir)):
                    self.image_title.SetLabel(messages.INVALID_IMAGE_LABEL)
                    self.image_desc.SetLabel(wordwrap(messages.INACCESSIBLE_IMAGE_REMOVE_MSG % {'path':imagedir},
                        self.GetSize().GetWidth() - 60, wx.ClientDC(self)))
                    self.image_details_button.Show(True)
                else:
                    self.image_title.SetLabel(messages.INVALID_IMAGE_LABEL)
                    self.image_desc.SetLabel(wordwrap(messages.UNRECOGNIZED_IMAGE_REMOVE_MSG % {'path':imagedir},
                        self.GetSize().GetWidth() - 60, wx.ClientDC(self)))
                    self.image_details_button.Show(True)
                self.image_title.Show(True)
                self.image_desc.Show(True)
                self.image_details_sizer.Layout()
                self.Show(True)
                self._frame.set_status("")
                utils.logger.error(utils.format_trace())

