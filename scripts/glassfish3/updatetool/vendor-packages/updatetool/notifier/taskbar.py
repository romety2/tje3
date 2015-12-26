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

if False:
    import gettext
    _ = gettext.gettext

import sys
import common.utils as utils
import wx
from common.fsutils import fsdec
from common.boot import UPDATETOOL_LOCALE

ID_NOTICE_TIMER = wx.NewId()

ID_MENU_ABOUT = wx.ID_ABOUT
ID_MENU_DETAILS = wx.NewId()
ID_MENU_APPLY = wx.NewId()
ID_MENU_PREFS = wx.ID_PREFERENCES
ID_MENU_EXIT = wx.NewId()
ID_MENU_HELP = wx.NewId()

class NotifierTaskBarIcon(wx.TaskBarIcon):

    _ = wx.GetTranslation

    menu = None

    def __init__(self, app_name, app_version, icon_path, parent,
                                         apply_func, details_func, prefs_func):

        wx.TaskBarIcon.__init__(self)

        self.app_name = app_name
        self.app_version = app_version
        self.parent = parent
        self.help = None

        self.icon = wx.Icon(fsdec(icon_path), wx.BITMAP_TYPE_PNG)

        self.Bind(wx.EVT_MENU, self.OnAbout, id=ID_MENU_ABOUT)
        self.Bind(wx.EVT_MENU, details_func, id=ID_MENU_DETAILS)
        self.Bind(wx.EVT_MENU, apply_func, id=ID_MENU_APPLY)
        self.Bind(wx.EVT_MENU, prefs_func, id=ID_MENU_PREFS)
        self.Bind(wx.EVT_MENU, self.OnExit, id=ID_MENU_EXIT)
        self.Bind(wx.EVT_MENU, self.OnHelp, id=ID_MENU_HELP)

        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, apply_func)


    def CreatePopupMenu(self):
        menu = wx.Menu()
        if 'wxMSW' in wx.PlatformInfo:
            item = wx.MenuItem(menu, ID_MENU_APPLY, _('Show and Apply Updates'))
            font = item.GetFont()
            font.SetWeight(wx.BOLD)
            item.SetFont(font)
            menu.AppendItem(item)
        else:
            menu.Append(ID_MENU_APPLY, _('Show and Apply Updates'))
        menu.Append(ID_MENU_DETAILS, _('Manage Update Details'))
        menu.Append(ID_MENU_PREFS, _('Preferences'))
        menu.AppendSeparator()
        if 'wxMSW' in wx.PlatformInfo:
            item = wx.MenuItem(menu, ID_MENU_ABOUT, _("About %s") % self.app_name)
            font = item.GetFont()
            font.SetWeight(wx.NORMAL)
            item.SetFont(font)
            menu.AppendItem(item)
        else:
            menu.Append(ID_MENU_ABOUT, _("About %s") % self.app_name)
        menu.Append(ID_MENU_HELP, _('Help'))
        menu.AppendSeparator()

        # We get the Exit menu for free on OS X
        if not 'wxMac' in wx.PlatformInfo:
            menu.Append(ID_MENU_EXIT, _('Exit'))

        self.menu = menu

        return menu


    def set_tooltip(self, tip):
        self.SetIcon(self.icon, tip)


    def remove_icon(self):
        self.RemoveIcon()


    def OnAbout(self, e):
        utils.display_about(self.parent.frame)


    def OnExit(self, e):
        self.parent.frame.Destroy()
        # An exit code of 99 means the user quit from the menu.  This will
        # trigger the scheduler to shutdown as well.
        sys.exit(99)


    def OnHelp(self, e):
        from wx.html import HtmlHelpController
        import os.path

        if not self.help:
            filename = "help.hhp"
            helppath = os.path.join(os.path.dirname(__file__), "..", "help", 'C', filename)

            loc = UPDATETOOL_LOCALE
            if loc is not None:
                if len(loc) >= 5 and loc.upper()[:5] == 'ZH_TW':
                    helppath = os.path.join(os.path.dirname(__file__), "..", "help", 'zh_TW', filename)
                elif len(loc) >= 2 and loc.upper()[:2] in ['ZH']:
                    helppath = os.path.join(os.path.dirname(__file__), "..", "help", 'zh_CN', filename)
                elif len(loc) >= 5 and loc.upper()[:5] == 'PT_BR':
                    # XXX: Only use these translations for Brazillian Portguese and no other portguese?
                    helppath = os.path.join(os.path.dirname(__file__), "..", "help", 'pt_BR', filename)
                elif len(loc) >= 2 and loc.upper()[:2] in ['DE', 'ES', 'FR', 'JA', 'KO']:
                    helppath = os.path.join(os.path.dirname(__file__), "..", "help", loc[:2].lower(), filename)

            temp_controller = HtmlHelpController()
            if not temp_controller.AddBook(helppath):
                return

            self.help = temp_controller

        self.help.Display("files/ui-desktop-notifier.html")
        self.help.FindTopLevelWindow().Centre(wx.BOTH)

