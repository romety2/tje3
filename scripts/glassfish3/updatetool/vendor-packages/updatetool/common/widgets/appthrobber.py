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

from common import utils
from common.mixins import KeywordArgsMixin
import wx

THROBBER_EVENT = wx.NewEventType()
EVT_UPDATE_THROBBER = wx.PyEventBinder(THROBBER_EVENT, 0)



class ThrobberControl(wx.PyControl):
    """
    A simplified version of wx.lib.throbber converted to be a PyControl so that it
    can be used in a wx.ToolBar.
    """
    def __init__(self, parent, id=-1,
                 pos=wx.DefaultPosition,
                 isize=wx.DefaultSize,
                 vsize=wx.DefaultSize,
                 name="throbber",
                 bitmaps=None,         # list of bitmaps
                 frameDelay=0.1       # time between frames
                 ):
        """
        The first argument is  a list of  strings of image names that will be treated
        as individual frames. The first frame is treated as the "at rest" frame (it is not
        shown during animation, but only when Throbber.Rest() is called.
        """
        _seqTypes = (type([]), type(()))
        assert type(bitmaps) in _seqTypes and len(bitmaps) > 0 # The "at rest" image plus the rest
        wx.PyControl.__init__(self, parent, id=id, pos=pos, size=vsize, style=wx.NO_BORDER, name=name)
        self.name = name

        # set size, guessing if necessary
        width, height = isize
        if width == -1:
            width = bitmaps[0].GetWidth()
        if height == -1:
            height = bitmaps[0].GetHeight()
        self.width, self.height = width, height

        # double check it
        assert width != -1 and height != -1, "Unable to guess size"

        vwidth, vheight = vsize
        if vwidth == -1:
            vwidth = self.width
        if vheight == -1:
            vheight == self.height
        self.vwidth, self.vheight = vwidth, vheight

        assert self.vwidth >= self.width
        assert self.vheight >= self.vheight

        self.frameDelay = frameDelay
        self.current = -1

        # do we have a sequence of images?
        self.submaps = bitmaps
        self.frames = len(self.submaps)

        self.SetClientSize((self.vwidth, self.vheight))

        self.timer = wx.Timer(owner=self)

        wx.EVT_TIMER(self, -1, self.OnTick)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnErase)


    def DoGetBestSize(self):
        return (self.vwidth, self.vheight)


    def OnTick(self, event):
        self.current += 1
        self._wrap()
        self.Refresh()


    def OnDestroyWindow(self, event):
        self.current += 1
        self.Stop()
        event.Skip()


    def OnErase(self, event):
        dc = wx.ClientDC(self)
        if '__WXMAC__' != wx.Platform:
            dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        if '__WXMAC__' == wx.Platform:
            self.Refresh()


    def OnPaint(self, event):
        if '__WXMAC__' == wx.Platform:
            dc = wx.ClientDC(self)
        else:
            dc = wx.BufferedPaintDC(self)
        if '__WXMAC__' != wx.Platform:
            dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        if self.current != -1:
            dc.DrawBitmap(self.submaps[self.current], (self.vwidth - self.width)/2, (self.vheight - self.height)/2, True)
        if '__WXMAC__' == wx.Platform:
            self.Refresh()


    def _wrap(self):
        if self.current >= self.frames:
            self.current = 0 # skips 0
        if self.current < -1:
            self.current = self.frames - 1


    def Rest(self):
        """Stop the animation and return to frame 0"""
        self.Stop()
        self.current = -1
        self.Refresh()


    def Start(self):
        """Start the animation"""
        if not self.timer.IsRunning():
            self.timer.Start(int(self.frameDelay * 1000))


    def Stop(self):
        """Stop the animation"""
        self.timer.Stop()


    def AcceptsFocus(self):
        """Non-interactive, so don't accept focus"""
        return False


    def ShouldInheritColours(self):
        """Get colours from our parent..."""
        return True



class AppThrobber(ThrobberControl):
    def __init__(self, parent, id, isize=(16, 16), vsize=(16, 16)):
        assert vsize >= isize
        iw, ih = isize
        images = [
            utils.get_image("throbber", "throbber00-%dx%d.png" % (iw, ih)),
            utils.get_image("throbber", "throbber01-%dx%d.png" % (iw, ih)),
            utils.get_image("throbber", "throbber02-%dx%d.png" % (iw, ih)),
            utils.get_image("throbber", "throbber03-%dx%d.png" % (iw, ih)),
            utils.get_image("throbber", "throbber04-%dx%d.png" % (iw, ih)),
            utils.get_image("throbber", "throbber05-%dx%d.png" % (iw, ih)),
            utils.get_image("throbber", "throbber06-%dx%d.png" % (iw, ih)),
            utils.get_image("throbber", "throbber07-%dx%d.png" % (iw, ih)),
            utils.get_image("throbber", "throbber08-%dx%d.png" % (iw, ih)),
            utils.get_image("throbber", "throbber09-%dx%d.png" % (iw, ih)),
            utils.get_image("throbber", "throbber10-%dx%d.png" % (iw, ih)),
            utils.get_image("throbber", "throbber11-%dx%d.png" % (iw, ih)),
                ]
        ThrobberControl.__init__(self, parent, id, bitmaps=images, frameDelay=0.1, isize=isize, vsize=vsize)
        del images



class ThrobberLabel(wx.Panel, KeywordArgsMixin):
    def __init__(self, parent, id, text=None, *args, **kwargs):
        KeywordArgsMixin.__init__(self)
        self.kwset(kwargs, 'font_weight', default=wx.BOLD)
        self.kwset(kwargs, 'font_size', default=12)

        kwargs['style'] = wx.NO_BORDER
        wx.Panel.__init__(self, parent, id, *args, **kwargs)
        self.throbber = AppThrobber(self, -1)
        if text:
            self.label = wx.StaticText(self, -1, text)
        else:
            self.label = wx.StaticText(self, -1, "")
        self.label.SetFont(wx.Font(self._font_size, wx.DEFAULT, wx.NORMAL, self._font_weight, 0, ""))
        sizer_3 = wx.FlexGridSizer(1, 2, 0, 10)
        sizer_3.Add(self.label, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_3.Add(self.throbber, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.SetSizer(sizer_3)
        sizer_3.Fit(self)
        sizer_3.AddGrowableCol(0)
        self.Layout()


    def SetFont(self, font):
        self.label.SetFont(font)


    def throb(self, on=True):
        """
        Show the throbbing throbber or hide it.
        """
        if on:
            self.throbber.Start()
        else:
            self.throbber.Rest()
        self.Layout()


    def set_status(self, msg=None):
        if msg:
            self.label.SetLabel(msg)
        else:
            self.label.SetLabel("")
        self.Layout()
