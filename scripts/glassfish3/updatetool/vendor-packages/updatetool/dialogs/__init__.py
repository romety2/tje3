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

import wx
_ = wx.GetTranslation

def make_std_dlg_btn_szr_panel(parent, buttons=None):
    """
    Convenience method to make working with StdDialogButtonSizer easier.

    Takes a buttons iterable with (wxID, Label, ToolTipString) tuples.
    Returns a list [panel, button1, button2, ...]

    Usage example:

    class SomeDialog(...):
        def __init__(...):
            # begin wxGlade: SomeDialog.__init__
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            ...
            # end wx.Glade
            wx.ID_APPLY,  _("&Save"),    _("Tooltip text for Save"),

            bpanel, btn_ok, btn_cancel = make_std_dlg_btn_szr_panel(self, (
                        wx.ID_OK,     _("&OK"),      _("Tooltip for OK"),
                        wx.ID_CANCEL, _("&Cancel"),  _("Tooltip for cancel action"),
                        ))
            main_sizer.Add(bpanel, 0, wx.ALL|wx.ALIGN_RIGHT, 12)
            self.Layout()
            bpanel.MoveAfterInTabOrder(self.<last_panel_name_here>)
    """
    ret = []
    bpanel = wx.Panel(parent, -1, style=wx.TAB_TRAVERSAL)
    ret += [bpanel]
    button_sizer = wx.StdDialogButtonSizer()
    bpanel.SetSizer(button_sizer)
    for wxid, label, tooltipstr in buttons:
        btn = wx.Button(bpanel, wxid, label)
        btn.SetToolTipString(tooltipstr)
        button_sizer.AddButton(btn)
        ret += [btn]
    button_sizer.Realize()
    return tuple(ret)
