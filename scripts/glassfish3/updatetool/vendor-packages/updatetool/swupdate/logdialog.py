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


import wx

import common.info as INFO
import common.basicfeed as BF
from common.fsutils import fsenc
import swupdate.consts as CONST
from common import ips

APP_LONG_NAME = INFO.UPDATE_APP_NAME

class LogDialog(wx.Dialog):

    def __init__(self, *args, **kwds):
        self.img_details = kwds['img_details']
        del kwds['img_details']

        wx.Dialog.__init__(self, *args, **kwds)

        # Add a panel so it looks correct on all platforms
        #self.panel = wx.Panel(self, wx.ID_ANY)

        self.top_text = wx.StaticText(self, -1, "Installation details for: " +
                                              self._get_title(self.img_details))

        if wx.Platform == "__WXMAC__":
            self.top_text.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False))
        else:
            self.top_text.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False))

        log_str = "".join(self.img_details['log'])

        if log_str == "":
            log_str = _("Installation not started")

        self.log_text = wx.TextCtrl(self, -1, log_str,
                                    style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.log_text.SetMinSize((500, 400))

        self.close_button = wx.Button(self, wx.ID_CANCEL, _("&Close"))
        self.Bind(wx.EVT_BUTTON, self.onClose, self.close_button)
        self.close_button.SetToolTipString("Close the dialog")
        self.close_button.SetDefault()

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self.top_text, 0, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND, 8)
        vsizer.Add(self.log_text, 1, wx.EXPAND | wx.RIGHT | wx.LEFT | wx.BOTTOM, 8)
        vsizer.Add(self.close_button, 0, wx.RIGHT | wx.LEFT | wx.BOTTOM| wx.ALIGN_RIGHT, 8)

        self.SetSizer(vsizer)
        vsizer.Fit(self)
        vsizer.SetSizeHints(self)
        self.Layout()

        # Center the dialog over the frame.
        self.Centre()

        # Set the focus to the first control to enable proper tab nav.
        self.log_text.SetFocus()


    def onClose(self, event):
        event.Skip()


    def _get_title(self, img_details):

        title = ""

        if img_details['type'] == CONST.T_NORMAL:
            title = ips.get_image_title(fsenc(img_details['imgroot']),
                                        opname='install')
        elif img_details['type'] == CONST.T_ADD_ON:
            item = img_details['add_on_image_list'][0]

            if img_details['feed_entry'].has_key(BF.TITLE):
                title = img_details['feed_entry'][BF.TITLE]
            else:
                title = _("Untitled Add-On")

            if item['sequence'] > 0:
                title += " (#%d)" % item['sequence']

        return title
