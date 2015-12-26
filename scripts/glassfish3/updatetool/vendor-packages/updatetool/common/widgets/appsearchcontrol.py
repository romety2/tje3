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

"""The search control"""
import wx

if False:    # Keep Pylint happy
    import gettext
    _ = gettext.gettext



class AppSearchCtrl(wx.SearchCtrl):

    _ = wx.GetTranslation

    maxSearches = 10

    def __init__(self, parent, id=-1, value="",
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0,
                 doSearch=None):
        style |= wx.TE_PROCESS_ENTER
        wx.SearchCtrl.__init__(self, parent, id, value, pos, size, style)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEntered)
        self.Bind(wx.EVT_MENU_RANGE, self.OnMenuItem, id=1, id2=self.maxSearches)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        if wx.Platform in ['__WXGTK__', '__WXMSW__']:
            for child in self.GetChildren():
                if isinstance(child, wx.TextCtrl):
                    child.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
                    break
        else:
            self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.ShowCancelButton(True)
        self.ShowSearchButton(True)
        self.doSearch = doSearch
        self.searches = []


    def OnKeyDown(self, evt):
        e_key = evt.GetKeyCode()
        if e_key == wx.WXK_SPACE and not len(self.GetValue()):
            # Swallow space key when the field is empty
            pass
        elif e_key in [wx.WXK_TAB, wx.WXK_NUMPAD_TAB]:
            flags = 0
            if not evt.ShiftDown():
                 flags |= wx.NavigationKeyEvent.IsForward
            self.Navigate(flags)
        else:
            evt.Skip()


    def OnTextEntered(self, evt):
        text = self.GetValue()
        if self.doSearch(text):
            self.searches.append(text)
            if len(self.searches) > self.maxSearches:
                del self.searches[0]
            self.SetMenu(self.MakeMenu())


    def OnMenuItem(self, evt):
        text = self.searches[evt.GetId()-1]
        self.SetValue(text)
        self.doSearch(text)


    def MakeMenu(self):
        menu = wx.Menu()
        item = menu.Append(-1, _("Recent Searches"))
        item.Enable(False)
        for idx, txt in enumerate(self.searches):
            menu.Append(1 + idx, txt)
        return menu


    def OnCancel(self, event):
        self.Clear()
        self.doSearch(u"")



class UTSearchCtrl(AppSearchCtrl):
    _ = wx.GetTranslation

    def __init__(self, parent, id=-1, value="",
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0,
                 doSearch=None, focusForward=None, focusBackward=None):
        self.focus_forward = focusForward
        self.focus_backward = focusBackward
        AppSearchCtrl.__init__(self, parent, id, value, pos, size,
                style, doSearch)

    def OnKeyDown(self, evt):
        e_key = evt.GetKeyCode()
        if e_key == wx.WXK_SPACE and not len(self.GetValue()):
           # Swallow space key when the field is empty
            pass
        elif e_key in [wx.WXK_TAB, wx.WXK_NUMPAD_TAB]:
            if not evt.ShiftDown():
                if self.focus_forward:
                    for window in self.focus_forward:
                        if window.IsShown():
                            window.SetFocus()
                            break
                flags = 0
                flags |= wx.NavigationKeyEvent.IsForward
                self.Navigate(flags)
            else:
                if self.focus_backward:
                    for window in self.focus_backward:
                        if window.IsShown():
                            window.SetFocus()
                            break
        else:
            evt.Skip()
