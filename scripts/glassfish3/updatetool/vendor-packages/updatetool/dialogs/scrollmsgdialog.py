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

import wx

if False:    # Keep Pylint happy
    import gettext
    _ = gettext.gettext

def ScrollMsgBox(*args, **kwargs):
    """
    Convenience method
    """
    dlg = ScrollMsgDialog(*args, **kwargs)
    dlg.ShowModal()
    dlg.Destroy()

class ScrollMsgDialog(wx.Dialog):

    _ = wx.GetTranslation

    def __init__(self, *args, **kwds):
        """
        Required:
        short_msg - The message label to show
        long_msg - The scrolled message to show
        """
        assert 'short_msg' in kwds, "short_msg is a required argument to ScrollMsgDialog"
        assert 'long_msg' in kwds, "long_msg is a required argument to ScrollMsgDialog"
        sm = kwds['short_msg']
        del kwds['short_msg']
        lm = kwds['long_msg']
        del kwds['long_msg']
        cap = None
        if 'caption' in kwds:
            cap = kwds['caption']
            del kwds['caption']
        wx.InitAllImageHandlers()
        # begin wxGlade: ScrollMsgDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.icon = wx.StaticBitmap(self, -1, (wx.ArtProvider_GetBitmap(wx.ART_ERROR, wx.ART_CMN_DIALOG, (32, 32))))
        self.short_msg = wx.StaticText(self.panel_1, -1, sm)
        self.long_msg = wx.TextCtrl(self.panel_1, -1, lm, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        self.button_1 = wx.Button(self, wx.ID_OK, _("&OK"))

        if cap is not None:
            self.SetTitle(cap)
        self.__set_properties()
        self.__do_layout()
        # end wxGlade


    def __set_properties(self):
        # begin wxGlade: ScrollMsgDialog.__set_properties
        self.SetTitle(_("Message"))
        self.SetSize((600, 400))
        # end wxGlade


    def __do_layout(self):
        # begin wxGlade: ScrollMsgDialog.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.icon, 0, wx.ALL, 5)
        sizer_3.Add(self.short_msg, 0, wx.ALL|wx.EXPAND, 5)
        sizer_3.Add(self.long_msg, 1, wx.ALL|wx.EXPAND, 5)
        self.panel_1.SetSizer(sizer_3)
        sizer_2.Add(self.panel_1, 1, wx.EXPAND, 0)
        sizer_1.Add(sizer_2, 1, wx.EXPAND, 0)
        sizer_1.Add(self.button_1, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)
        self.SetSizer(sizer_1)
        self.Layout()
        self.Centre()
        # end wxGlade

# end of class ScrollMsgDialog


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    try:
        raise "Sample exception"
    except:
        import sys
        import traceback
        typ, val, tback = sys.exc_info()
        lst = traceback.format_tb(tback) + traceback.format_exception_only(typ, val)
        lm = "Traceback (innermost last):\n%-20s %s" % ("".join(lst[:-1]), lst[-1])
    dialog_1 = ScrollMsgDialog(None, -1, short_msg="Foo\nBar\nBaz", long_msg=lm)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
