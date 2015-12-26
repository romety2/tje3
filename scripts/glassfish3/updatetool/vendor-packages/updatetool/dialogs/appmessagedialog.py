#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS HEADER.
#
# Copyright (c) 2008-2010 Oracle and/or its affiliates. All rights reserved.
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

import wx

class AppMessageDialog(wx.Dialog):

    _ = wx.GetTranslation

    def __init__(self, *args, **kwds):
        """
        Simplified custom MessageDialog to allow centering on Mac and any other behavior we might want to add.

        style attribute must be specified for the dialog
        """
        if not 'style' in kwds:
            raise "style attribute must be supplied"
        if not 'message' in kwds:
            raise "message attribute must be supplied"
        if not 'caption' in kwds:
            raise "caption attribute must be supplied"
        self._style = kwds['style']
        self._message = kwds['message']
        self._caption = kwds['caption']
        del kwds['message']
        del kwds['caption']
        # begin wxGlade: AppMessageDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.theicon_bitmap = wx.StaticBitmap(self, -1, (wx.ArtProvider.GetBitmap(wx.ART_WARNING, wx.ART_CMN_DIALOG,(32,32))))
        self.message_label = wx.StaticText(self.panel_1, -1, _("message"))
        self.panel_2 = wx.Panel(self.panel_1, -1)
        self.button_left = wx.Button(self.panel_1, -1, _("button_2"))
        self.button_right = wx.Button(self.panel_1, -1, _("button_1"))

        self.__set_properties()
        self.__do_layout()
        # end wxGlade
        if wx.OK & self._style:
            self.button_right.SetId(wx.ID_OK)
            self.button_right.SetLabel(wx.GetStockLabel(wx.ID_OK, True))
            if wx.CANCEL & self._style:
                self.button_left.SetId(wx.ID_CANCEL)
                self.button_left.SetLabel(wx.GetStockLabel(wx.ID_CANCEL, True))
            else:
                self.button_left.Enable(False)
                self.button_left.Hide()
        elif wx.YES & self._style:
            self.button_right.SetId(wx.ID_YES)
            self.button_right.SetLabel(wx.GetStockLabel(wx.ID_YES, True))
            if wx.NO & self._style:
                self.button_left.SetId(wx.ID_NO)
                self.button_left.SetLabel(wx.GetStockLabel(wx.ID_NO, True))
            else:
                self.button_left.Enable(False)
                self.button_left.Hide()
        elif wx.NO_DEFAULT & wx._style:
            self.button_right.SetId(wx.ID_YES)
            self.button_right.SetLabel(wx.GetStockLabel(wx.ID_YES, True))
            self.button_left.SetId(wx.ID_NO)
            self.button_left.SetLabel(wx.GetStockLabel(wx.ID_NO, True))
            self.button_left.SetDefault()
        else:
            raise _("Internal error: Invalid AppMessageDialog usage")

        if wx.ICON_EXCLAMATION & self._style:
            self.bitmap_1 = wx.ArtProvider.GetBitmap(wx.ART_WARNING, wx.ART_CMN_DIALOG, (32, 32))
        elif wx.ICON_ERROR & self._style:
            self.bitmap_1 = wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_CMN_DIALOG, (32, 32))
        elif wx.ICON_QUESTION & self._style:
            self.bitmap_1 = wx.ArtProvider.GetBitmap(wx.ART_QUESTION, wx.ART_CMN_DIALOG, (32, 32))
        elif wx.ICON_INFORMATION & self._style:
            self.bitmap_1 = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_CMN_DIALOG, (32, 32))
        else:
            raise _("Internal error: Invalid AppMessageDialog usage")

        # print "wx.ICON_EXCLAMATION", wx.ICON_EXCLAMATION
        # print "wx.ICON_ERROR", wx.ICON_ERROR
        # print "wx.ICON_QUESTION", wx.ICON_QUESTION
        # print "wx.ICON_INFORMATION", wx.ICON_INFORMATION
        # print "wx.YES_DEFAULT", wx.YES_DEFAULT              # 0
        # print "wx.YES=",wx.YES                              # 2
        # print "wx.OK=",wx.OK                                # 4
        # print "wx.NO", wx.NO                                # 8
        # print "wx.YES_NO", wx.YES_NO                        # 10
        # print "wx.CANCEL=",wx.CANCEL                        # 16
        # print "wx.NO_DEFAULT", wx.NO_DEFAULT                # 128
        # print "wx.ICON_EXCLAMATION", wx.ICON_EXCLAMATION
        # print "wx.ICON_ERROR", wx.ICON_ERROR
        # print "wx.ICON_QUESTION", wx.ICON_QUESTION
        # print "wx.ICON_INFORMATION", wx.ICON_INFORMATION
        sizer = self.GetSizer()
        sizer.Fit(self)
        self.Layout()

    def __set_properties(self):
        # begin wxGlade: AppMessageDialog.__set_properties
        pass
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: AppMessageDialog.__do_layout
        grid_sizer_1 = wx.FlexGridSizer(1, 3, 6, 0)
        grid_sizer_2 = wx.FlexGridSizer(2, 1, 6, 6)
        sizer_1_copy = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_1.Add(self.theicon_bitmap, 0, wx.ALL, 6)
        grid_sizer_2.Add(self.message_label, 1, wx.ALL|wx.EXPAND, 6)
        sizer_1_copy.Add(self.panel_2, 1, wx.EXPAND, 0)
        sizer_1_copy.Add(self.button_left, 0, wx.ALL|wx.ALIGN_RIGHT, 6)
        sizer_1_copy.Add(self.button_right, 0, wx.ALL|wx.ALIGN_RIGHT, 6)
        grid_sizer_2.Add(sizer_1_copy, 0, wx.ALL|wx.ALIGN_RIGHT, 6)
        self.panel_1.SetSizer(grid_sizer_2)
        grid_sizer_2.AddGrowableRow(0)
        grid_sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)
        self.SetSizer(grid_sizer_1)
        grid_sizer_1.Fit(self)
        grid_sizer_1.AddGrowableRow(0)
        grid_sizer_1.AddGrowableCol(2)
        self.Layout()
        # end wxGlade

# end of class AppMessageDialog

if __name__ == "__main__":
    import gettext
    gettext.install("appmessagedialog")

    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()

    appmessagedialog = AppMessageDialog(None, message="Message", caption="Caption", style=wx.OK|wx.ICON_INFORMATION)
    app.SetTopWindow(appmessagedialog)
    appmessagedialog.ShowModal()
    appmessagedialog.Destroy()
    appmessagedialog = AppMessageDialog(None, message="Message", caption="Caption", style=wx.YES_NO|wx.ICON_ERROR)
    app.SetTopWindow(appmessagedialog)
    appmessagedialog.ShowModal()
    app.MainLoop()
