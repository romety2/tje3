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

from common.boot import n_
import wx
from common.utils import readable_size
from common.exception import UpdateToolException
import dialogs

import gettext
if False:    # Keep Pylint happy
    _ = gettext.gettext



class PreOpConfirmationDialog(wx.Dialog):

    _ = wx.GetTranslation

    INSTALL = 1
    REMOVE = 2

    def __init__(self, *args, **kwds):

        self._items = []
        if 'items' in kwds:
            self._items = kwds['items']
            del kwds['items']

        self._selected_pkg_count = 0
        if 'pkg_count' in kwds:
            self._selected_pkg_count = kwds['pkg_count']
            del kwds['pkg_count']

        self._extra_pkg_count = 0
        if 'extra_pkg_count' in kwds:
            self._extra_pkg_count = kwds['extra_pkg_count']
            del kwds['extra_pkg_count']

        self._op_size = 0
        if 'op_size' in kwds:
            self._op_size = kwds['op_size']
            del kwds['op_size']

        self._confirm_type = kwds['confirm_type']
        del kwds['confirm_type']

        #kwds["style"] = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.THICK_FRAME
        # begin wxGlade: PreOpConfirmationDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        if self._extra_pkg_count:
            self.bitmap_1 = wx.StaticBitmap(self, -1, (wx.ArtProvider.GetBitmap(wx.ART_WARNING, wx.ART_CMN_DIALOG, (32, 32))))
        else:
            self.bitmap_1 = wx.StaticBitmap(self, -1, (wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_CMN_DIALOG, (32, 32))))
        self.short_msg_label = wx.StaticText(self.panel_1, -1, _("Short msg goes here.\n\nThe message is multiline."))
        self.list_box = wx.ListBox(self.panel_1, -1, choices=[], style=wx.LB_NEEDED_SB)
        self.summary_heading = wx.StaticText(self.panel_1, -1, _("Summary"))
        self.summary_text = wx.StaticText(self.panel_1, -1, _("Summary goes here"))

        self.__set_properties()
        self.__do_layout()
        # end wxGlade
        self._update_display()
        self.Centre()


    def __set_properties(self):
        # begin wxGlade: PreOpConfirmationDialog.__set_properties
        self.SetTitle(_("PreOp Confirmation"))
        self.SetMinSize((500, -1))
        self.summary_heading.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        # end wxGlade
        # The need to use the wx.CollapsiblePane prevents us from using wxGlade completely


    def __do_layout(self):
        # begin wxGlade: PreOpConfirmationDialog.__do_layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.bitmap_1, 0, wx.ALL, 5)
        sizer_2.Add(self.short_msg_label, 0, wx.ALL|wx.EXPAND, 5)
        sizer_2.Add(self.list_box, 0, wx.ALL|wx.EXPAND, 5)
        sizer_2.Add(self.summary_heading, 0, wx.ALL|wx.EXPAND, 5)
        sizer_2.Add(self.summary_text, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)
        main_sizer.Add(sizer_1, 1, wx.ALL|wx.EXPAND, 12)
        self.SetSizer(main_sizer)
        self.Layout()
        self.Centre()
        # end wxGlade
        if self._confirm_type == PreOpConfirmationDialog.INSTALL:
            bpanel, dummy1, dummy2 = dialogs.make_std_dlg_btn_szr_panel(self, (
                (wx.ID_CANCEL, _("&Cancel"), _("Do not proceed with install/update")),
                (wx.ID_OK, _("Install"), _("Proceed with install/update")),
                ))
        elif self._confirm_type == PreOpConfirmationDialog.REMOVE:
            bpanel, dummy1, dummy2 = dialogs.make_std_dlg_btn_szr_panel(self, (
                (wx.ID_CANCEL, _("&Cancel"), _("Do not proceed with removal")),
                (wx.ID_OK, _("Remove"), _("Proceed with removal")),
                ))
        else:
            raise UpdateToolException("Internal Error: Invalid usage of PreOpConfirmationDialog")
        main_sizer.Add(bpanel, 0, wx.ALL|wx.ALIGN_RIGHT|wx.EXPAND, 12)
        main_sizer.Fit(self)
        self.Layout()


    def _update_display(self):
        if self._confirm_type == PreOpConfirmationDialog.INSTALL:
            _title = _("Install/Update Confirmation")
            if self._extra_pkg_count > 0:
                _short_msg = _("This action affects other components.\n\nThe following components will be installed/updated.")
            else:
                _short_msg = _("The following components will be installed/updated.")

            _summary = n_("%(count)d package was selected for install/update.",
                    "%(count)d packages were selected for install/update.", self._selected_pkg_count) % {
                            'count':self._selected_pkg_count}

            if self._extra_pkg_count > 0:
                _summary = "\n".join([_summary, n_(
                    "%(count)d other package will be installed/updated due to dependencies.",
                    "%(count)d other packages will be installed/updated due to dependencies.", self._extra_pkg_count) % {
                        'count':self._extra_pkg_count}])
            # XXX : Unused for now
            if self._op_size != 0:
                _summary = "".join([_summary, _("%s of install/update will be done.") % readable_size(self._op_size)])

        elif self._confirm_type == PreOpConfirmationDialog.REMOVE:
            _title = _("Removal Confirmation")
            if self._extra_pkg_count > 0:
                _short_msg = _("Components that depend on the selected components will also be removed.\n\n" \
                        "Carefully review the following list of affected components to be removed before proceeding.")
            else:
                _short_msg = _("The following components will be removed.")

            if self._selected_pkg_count > 0: # it's true at this point
                _summary = n_("%(count)d package was selected for removal.",
                        "%(count)d packages were selected for removal.", self._selected_pkg_count) % {
                                'count':self._selected_pkg_count}

            if self._extra_pkg_count > 0:
                _summary = "\n".join([_summary, n_(
                    "%(count)d other package will be removed due to dependencies.",
                    "%(count)d other packages will be removed due to dependencies.", self._extra_pkg_count) % {
                        'count':self._extra_pkg_count}])
            # XXX : Unused for now
            if self._op_size != 0:
                _summary = "".join([_summary, _("%(megabyte_size)s of removal will be done.") % {'megabyte_size':readable_size(self._op_size)}])
        else:
            raise UpdateToolException("Internal Error: Invalid usage of PreOpConfirmationDialog")

        self.summary_text.SetLabel(_summary)
        self.short_msg_label.SetLabel(_short_msg)
        self.list_box.Clear()
        if self._items:
            self._items.sort()
            self.list_box.InsertItems(self._items, 0)
        self.list_box.SetFocus()
        self.SetTitle(_title)
        self.GetSizer().Fit(self)
        self.Layout()
