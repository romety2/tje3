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
import dialogs
import os

class AuthDialog(wx.Dialog):

    _ = wx.GetTranslation

    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.auth_panel = wx.Panel(self, -1, style=wx.NO_BORDER|wx.TAB_TRAVERSAL)
        self.label_username = wx.StaticText(self.auth_panel, -1, _("Username:"), style=wx.ALIGN_RIGHT)
        self.text_ctrl_proxy_username = wx.TextCtrl(self.auth_panel, -1, "")
        self.label_password = wx.StaticText(self.auth_panel, -1, _("Password:"), style=wx.ALIGN_RIGHT)
        self.text_ctrl_proxy_password = wx.TextCtrl(self.auth_panel, -1, "", style=wx.TE_PASSWORD)
        self.Center()
        self.__do_layout()

    def set_auth_info(self, username):
        self.text_ctrl_proxy_username.SetMinSize((120, -1))
        self.text_ctrl_proxy_password.SetMinSize((120, -1))
        self.text_ctrl_proxy_username.SetValue(username)
        self.text_ctrl_proxy_username.Enable(False)


    def __do_layout(self):
        border = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.FlexGridSizer(0, 2, 5, 5)
        self.sizer.Add(self.label_username, 0, wx.LEFT|wx.BOTTOM|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.sizer.Add(self.text_ctrl_proxy_username, 0, wx.LEFT|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)
        self.sizer.Add(self.label_password, 0, wx.LEFT|wx.BOTTOM|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.sizer.Add(self.text_ctrl_proxy_password, 0, wx.LEFT|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)
        self.auth_panel.SetSizer(self.sizer)
        border.Add(self.auth_panel, 0,  wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)
        self.SetSizer(border)
        border.Fit(self)
        self.Layout()

        bpanel, cancel_button, ok_button = \
                dialogs.make_std_dlg_btn_szr_panel(self, (
                    (wx.ID_CANCEL, _("&Cancel"), _("Cancel application of any unsaved changes and close this dialog box")),
                    (wx.ID_OK, _("&OK"), _("Apply any changes and close this dialog box")),
                    ))
        border.Add(bpanel, 0, wx.ALL|wx.ALIGN_RIGHT, 10)
        self.SetSizer(border)
        border.Fit(self)
        self.Layout()
        self.Bind(wx.EVT_BUTTON, self.OnOk, ok_button)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, cancel_button)

    def OnOk(self, event):
        assert event.GetId() == wx.ID_OK

        if len(self.text_ctrl_proxy_username.GetValue().strip()) != 0:
            username = self.text_ctrl_proxy_username.GetValue().strip()
        else:
            wx.MessageBox(_("Password can't be empty."), \
                    style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Proxy Authentication"), parent=self)
            return

        if len(self.text_ctrl_proxy_password.GetValue().strip()) != 0:
            password = self.text_ctrl_proxy_password.GetValue().strip()
        else:
            wx.MessageBox(_("Password can't be empty."), \
                    style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Proxy Authentication"), parent=self)
            return
        os.environ['HTTP_PROXY_USERNAME']=username
        os.environ['HTTP_PROXY_PASSWORD']=password
        event.Skip()

    def OnCancel(self, event):
        assert event.GetId() == wx.ID_CANCEL
        os.environ['HTTP_PROXY_USERNAME']=""
        os.environ['HTTP_PROXY_PASSWORD']=""
        event.Skip()



