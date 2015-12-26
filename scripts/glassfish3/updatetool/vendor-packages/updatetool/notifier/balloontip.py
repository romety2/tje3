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
from wx.lib.buttons import GenButton

_ = wx.GetTranslation

# Define The Values For The BalloonTip Frame Shape
BT_ROUNDED = 1
BT_RECTANGLE = 2

# Define The Value For The BalloonTip Destruction Behavior
BT_LEAVE = 3
BT_CLICK = 4
BT_BUTTON = 5

# OS X balloon offset
OSX_OFFSET = 10


class BalloonFrame(wx.Frame):

    def __init__(self, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, classparent=None, arrow=False,
                 clickfunc=None):
        """Default Class Constructor.

        Used Internally. Do Not Call Directly This Class In Your Application!
        """

        if wx.Platform == "__WXMAC__":
            style=wx.SIMPLE_BORDER | wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP
        else:
            style=wx.SIMPLE_BORDER | wx.FRAME_TOOL_WINDOW | wx.STAY_ON_TOP | wx.FRAME_SHAPED

        wx.Frame.__init__(self, None, -1, "Notifier Notice", pos, size, style=style)

        self.arrow = arrow
        self.win_x = 0
        self.win_y = 0

        self.i = 0

        self._parent = classparent
        self._toptitle = self._parent._toptitle
        self._topicon = self._parent._topicon
        self._message = self._parent._message
        self._shape = self._parent._shape
        self._tipstyle = self._parent._tipstyle
        self._frame_close = self._parent._frame_close

        self._ballooncolour = self._parent._ballooncolour
        self._balloonmsgcolour = self._parent._balloonmsgcolour
        self._balloonmsgfont = self._parent._balloonmsgfont

        if self._toptitle != "":
            self._balloontitlecolour = self._parent._balloontitlecolour
            self._balloontitlefont = self._parent._balloontitlefont

        panel = wx.Panel(self, -1)
        # Transparence does not always work on Windows.  Sometimes the window
        # appears completely black.
        if wx.Platform != "__WXMSW__":
            self.SetTransparent(245)
        #sizer = wx.BoxSizer(wx.VERTICAL)

        self.panel = panel

        subsizer = wx.BoxSizer(wx.VERTICAL)

        # For icon, title
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        if self.arrow:
            subsizer.Add((0,20), 0, wx.EXPAND) #Space for the Arrow

        if self._topicon is not None:
            stb = wx.StaticBitmap(panel, -1, self._topicon)
            hsizer.Add(stb, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 5)
            self._balloonbmp = stb

        if self._toptitle != "":
            stt = wx.StaticText(panel, -1, self._toptitle)
            stt.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD, False))
            if self._topicon is None:
                hsizer.Add((10,0), 0, wx.EXPAND)

            hsizer.Add(stt, 1, wx.EXPAND | wx.TOP, 10)

            self._balloontitle = stt
            self._balloontitle.SetForegroundColour(self._balloontitlecolour)
            self._balloontitle.SetFont(self._balloontitlefont)

        if self._tipstyle == BT_BUTTON:
            self._closebutton = GenButton(panel, -1, "X", style=wx.NO_BORDER)
            self._closebutton.SetMinSize((16,16))
            self._closebutton.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD, False))
            self._closebutton.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterButton)
            self._closebutton.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveButton)
            self._closebutton.SetUseFocusIndicator(False)
            if self._toptitle != "":
                hsizer.Add(self._closebutton, 0, wx.TOP | wx.RIGHT, 5)
            else:
                hsizer.Add((10,0), 1, wx.EXPAND)
                hsizer.Add(self._closebutton, 0, wx.ALIGN_RIGHT | wx.TOP
                           | wx.RIGHT, 5)

        if self._topicon is not None or self._toptitle != "" \
           or self._tipstyle == BT_BUTTON:

            subsizer.Add(hsizer, 0, wx.EXPAND | wx.BOTTOM, 5)

        self._firstline = line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        if wx.Platform != "__WXMSW__":
            self._firstline.SetBackgroundColour(wx.Color(255, 0, 0))

        if self._topicon is not None or self._toptitle != "" \
           or self._tipstyle == BT_BUTTON:
            subsizer.Add(self._firstline, 0, wx.EXPAND | wx.LEFT | wx.RIGHT
                         | wx.BOTTOM, 10)
        else:
            subsizer.Add(self._firstline, 0, wx.EXPAND | wx.LEFT | wx.RIGHT
                         | wx.BOTTOM | wx.TOP, 10)

        mainstt = wx.StaticText(panel, -1, self._message)

        self._balloonmsg = mainstt
        self._balloonmsg.SetForegroundColour(self._balloonmsgcolour)
        self._balloonmsg.SetFont(self._balloonmsgfont)

        #subsizer.Add(self._balloonmsg, 0, wx.EXPAND | wx.LEFT | wx.RIGHT |
        subsizer.Add(self._balloonmsg, 1, wx.EXPAND | wx.LEFT | wx.RIGHT |
                     wx.BOTTOM, 10)
        #self._secondline = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        #subsizer.Add(self._secondline, 0, wx.EXPAND | wx.LEFT | wx.RIGHT
        #                               | wx.BOTTOM, 10)
        #subsizer.Add((0,0),1)
        panel.SetSizer(subsizer)

        #sizer.Add(panel, 1, wx.EXPAND)
        subsizer.Fit(self)

        #self.SetSizerAndFit(sizer)
        #sizer.Layout()

        if self._tipstyle == BT_CLICK:
            if self._toptitle != "":
                self._balloontitle.Bind(wx.EVT_LEFT_DOWN, self.OnClose)

            if self._topicon is not None:
                self._balloonbmp.Bind(wx.EVT_LEFT_DOWN, self.OnClose)

            self._balloonmsg.Bind(wx.EVT_LEFT_DOWN, self.OnClose)
            self.panel.Bind(wx.EVT_LEFT_DOWN, self.OnClose)

        elif self._tipstyle == BT_BUTTON:
            self._closebutton.Bind(wx.EVT_BUTTON, self.OnClose)

        # If a callback for button clicks has been established on the
        # balloon bind to the function
        if clickfunc:
            self.panel.Bind(wx.EVT_LEFT_DOWN, clickfunc)
            stt.Bind(wx.EVT_LEFT_DOWN, clickfunc)
            mainstt.Bind(wx.EVT_LEFT_DOWN, clickfunc)

        self.panel.SetBackgroundColour(self._ballooncolour)

        if wx.Platform == "__WXGTK__":
            self.Bind(wx.EVT_WINDOW_CREATE, self.SetBalloonShape)
        elif wx.Platform != "__WXMAC__":
            self.SetBalloonShape()

        #self.Show(True)


    def SetBalloonShape(self, event=None):
        """Sets The Balloon Shape."""

        size = self.GetSize()

        #WindowCreate Events are being sent for every window in the ballooon
        #frame.  This is probably not what the author wanted.
        #if event:
        #    print "GetEventType: ", event.GetEventType()
        #    if event.GetEventType() == wx.EVT_WINDOW_CREATE:
        #        print "wx.EVT_WINDOW_CREATE"
        #    print "GetId: ", event.GetId()
        #    print "Window: ", event.GetWindow()

        #dc = wx.MemoryDC()
        #textlabel = self._balloonmsg.GetLabel()
        #textfont = self._balloonmsg.GetFont()
        # XXX: We use a bogus label to get the text extents because this
        # method my not work correctly if the label contains multiple
        # lines of text.
        #textextent = dc.GetFullTextExtent("Bogus Label: j", textfont)

        # XXX: Why did they subtract the textextend?
        #boxheight = size.y - textextent[1]*len(textlabel.split("\n"))
        boxheight = size.y
        boxwidth = size.x

        bmp = wx.EmptyBitmap(size.x,size.y)
        dc = wx.BufferedDC(None, bmp)
        dc.BeginDrawing()
        dc.SetBackground(wx.Brush(wx.Color(0,0,0), wx.SOLID))
        dc.Clear()
        dc.SetPen(wx.Pen(wx.Color(0,0,0), 1, wx.TRANSPARENT))

        if self._shape == BT_ROUNDED:
            dc.DrawRoundedRectangle(0, 0, boxwidth, boxheight, 12)
            #dc.DrawRoundedRectangle(0, 20, boxwidth, boxheight-20, 12)

        elif self._shape == BT_RECTANGLE:
            dc.DrawRectangle(0, 20, boxwidth, boxheight-20)

        dc.EndDrawing()

        r = wx.RegionFromBitmapColour(bmp, wx.Color(0,0,0))
        self.hasShape = self.SetShape(r)

        if self._tipstyle == BT_BUTTON:
            colour = self.panel.GetBackgroundColour()
            self._closebutton.SetBackgroundColour(colour)

    def PositionBalloon(self, icon_window):

        cdr_x, cdr_y, cdr_w, cdr_h = wx.ClientDisplayRect()
        display_w, dispaly_h = wx.DisplaySize()

        # If we found the TB icon window we can try to position relative
        # to it.

        if icon_window and wx.Platform != "__WXMAC__":
            x, y = self.FindPosition(icon_window)
        # Otherwise we need to try to position relative to the TB area
        # if we can determine it.
        else:
            x, y = self.FindPositionWindows()

        self.SetPosition((x, y))


    def FindPosition(self, icon_window):
        d_w, d_h = wx.DisplaySize()
        c_x, c_y, c_w, c_h = wx.ClientDisplayRect()

        box_w = self.GetSize().GetWidth()
        box_h = self.GetSize().GetHeight()

        x, y, icon_w, icon_h = icon_window.GetClientRect()
        x, y = icon_window.GetPositionTuple()
        icon_sc_x, icon_sc_y = icon_window.ClientToScreenXY(x, y)

        if TaskBarExists():
            location = GetTaskBarPosition()
            if location is "top":
                xpos = icon_sc_x
                ypos = icon_sc_y + icon_h
            elif location is "bottom":
                xpos = icon_sc_x
                ypos = icon_sc_y - box_h
            elif location is "right":
                xpos = icon_sc_x - box_w
                ypos = icon_sc_y
            elif location is "left":
                xpos = icon_sc_x + icon_w
                ypos = icon_sc_y
        else:
            location = GetWindowScreenQuadrant(icon_sc_x, icon_sc_y)
            if location is "top":
                xpos = icon_sc_x
                ypos = icon_sc_y + icon_h
            elif location is "bottom":
                xpos = icon_sc_x
                ypos = icon_sc_y - box_h
            else:
                xpos = icon_sc_x
                ypos = icon_sc_y

        #print "BalloonFrame: DisplaySize: ", wx.DisplaySize()
        #print "BalloonFrame: ClientDisplayRect: ", wx.ClientDisplayRect()
        #print "BalloonFrame: icon info: ", icon_window.GetClientRect()
        #print "BalloonFrame: icon screen coords x, y: ", icon_sc_x, icon_sc_y
        #print "BalloonFrame: frame pos: ", xpos, ypos, box_w, box_h
        xpos, ypos = AdjustToDisplayRect(xpos, ypos, box_w, box_h, icon_w, icon_h)

        #print "BalloonFrame: frame adjusted pos: ", xpos, ypos

        return xpos, ypos


    def FindPositionWindows(self):
        d_w, d_h = wx.DisplaySize()
        c_x, c_y, c_w, c_h = wx.ClientDisplayRect()

        #print "XXX: DisplaySize: ", wx.DisplaySize()
        #print "XXX: ClientDispalyRect:", wx.ClientDisplayRect()

        box_w = self.GetSize().GetWidth()
        box_h = self.GetSize().GetHeight()

        #DumpWindows()

        # On Mac since we have difficulity placing the icon above the 
        # taskbar (when it is at the bottom of the display) we default
        # the location to the top-right.
        if wx.Platform == "__WXMAC__":
            location = "top"
            xpos = c_w - box_w - OSX_OFFSET
            ypos = c_y + OSX_OFFSET
            return xpos, ypos
        elif TaskBarExists():
            location = GetTaskBarPosition()
        else:
            location = "bottom"

        # Put it at the top-right
        if location is "top":
            xpos = c_w - box_w
            ypos = c_y
        # Put it at the bottom-right
        elif location in ["bottom", "right"]:
            xpos = c_w - box_w
            ypos = c_h - box_h
        # case: left taskbar - put it at the bottom/left
        else:
            xpos = c_x
            ypos = c_h - box_h

        #print "FindPositionWindows: returns: ", xpos, ypos

        return xpos, ypos

    def OnEnterButton(self, event):
        """Handles The wx.EVT_ENTER_WINDOW For The BalloonTip Button.

        When The BalloonTip Is Created With The TipStyle=BT_BUTTON, This Event
        Provide Some Kind Of 3D Effect When The Mouse Enters The Button Area.
        """

        button = event.GetEventObject()
        colour = button.GetBackgroundColour()
        red = colour.Red()
        green = colour.Green()
        blue = colour.Blue()

        if red < 30:
            red = red + 30
        if green < 30:
            green = green + 30
        if blue < 30:
            blue = blue + 30

        colour = wx.Colour(red-30, green-30, blue-30)
        button.SetBackgroundColour(colour)
        button.SetForegroundColour(wx.WHITE)
        button.Refresh()
        event.Skip()


    def OnLeaveButton(self, event):
        """Handles The wx.EVT_LEAVE_WINDOW For The BalloonTip Button.

        When The BalloonTip Is Created With The TipStyle=BT_BUTTON, This Event
        Restore The Button Appearance When The Mouse Leaves The Button Area.
        """

        button = event.GetEventObject()
        colour = self.panel.GetBackgroundColour()
        button.SetBackgroundColour(colour)
        button.SetForegroundColour(wx.BLACK)
        button.Refresh()
        event.Skip()


    def OnClose(self, event):
        """ Handles The wx.EVT_CLOSE Event."""


        #Inform the parent that the frame is being closed
        if self._parent._frame_close:
            self._parent._frame_close(self._parent)

        #if isinstance(self._parent._widget, wx.TaskBarIcon):
            #self._parent.taskbarcreation = 0
            #self._parent.taskbartime.Stop()
            #del self._parent.taskbartime
            #del self._parent.BalloonFrame

        self.Destroy()


# ---------------------------------------------------------------
# Class BalloonTip
# ---------------------------------------------------------------
# This Is The Main BalloonTip Implementation
# ---------------------------------------------------------------

class BalloonTip:

    def __init__(self, topicon=None, toptitle="",
                 message="", shape=BT_ROUNDED, tipstyle=BT_LEAVE, clickfunc=None):
        """Deafult Class Constructor.

        BalloonTip.__init__(self, topicon=None, toptitle="", message="",
                            shape=BT_ROUNDED, tipstyle=BT_LEAVE,
                            clickfunc=clickfunc)

        Parameters:

        - topicon: An Icon That Will Be Displayed On The Top-Left Part Of The
          BalloonTip Frame. If Set To None, No Icon Will Be Displayed;
        - toptile: A Title That Will Be Displayed On The Top Part Of The
          BalloonTip Frame. If Set To An Empty String, No Title Will Be Displayed;
        - message: The Tip Message That Will Be Displayed. It Can Not Be Set To
          An Empty String;
        - shape: The BalloonTip Shape. It Can Be One Of:
          a) BT_RECTANGLE (A Rectangle);
          b) BT_ROUNDED (Rounded Rectangle, The Default).
        - tipstyle: The BalloonTip Destruction Behavior. It Can Be One Of:
          a) BT_LEAVE: The BalloonTip Is Destroyed When The Mouse Leaves The
             Target Control/Window;
          b) BT_CLICK: The BalloonTip Is Destroyed When You Click On Any Area
             Of The Target Control/Window;
          c) BT_BUTTON: The BalloonTip Is Destroyed When You Click On The
             Top-Right Close Button;
        """

        self.displayed = False


        self._shape = shape
        self._topicon = topicon
        self._toptitle = toptitle
        self._message = message
        self._tipstyle = tipstyle
        self._clickfunc = clickfunc

        self._frame_close = self.OnFrameClose

        app = wx.GetApp()
        self._runningapp = app
        self._runningapp.__tooltipenabled__ = True

        if self._message == "":
            raise "\nERROR: You Should At Least Set The Message For The BalloonTip"

        if self._shape not in [BT_ROUNDED, BT_RECTANGLE]:
            raise '\nERROR: BalloonTip Shape Should Be One Of "BT_ROUNDED", "BT_RECTANGLE"'

        if self._tipstyle not in [BT_LEAVE, BT_CLICK, BT_BUTTON]:
            msg = '\nERROR: BalloonTip TipStyle Should Be One Of "BT_LEAVE", '\
                  '"BT_CLICK", "BT_BUTTON"'
            raise msg

        self.SetStartDelay()
        self.SetEndDelay()
        self.SetBalloonColour()

        if toptitle != "":
            self.SetTitleFont()
            self.SetTitleColour()

        if topicon is not None:
            self.SetBalloonIcon(topicon)

        self.SetMessageFont()
        self.SetMessageColour()

    def OnFrameClose(self, parent):
        self.displayed = False

    def IsDisplayed(self):
        return self.displayed

    def SetTarget(self, widget):
        """Sets The Target Control/Window For The BalloonTip."""

        self._widget = widget


    def GetTarget(self):
        """Returns The Target Window For The BalloonTip."""

        if not hasattr(self, "_widget"):
            raise "\nERROR: BalloonTip Target Has Not Been Set"

        return self._widget


    def SetStartDelay(self, delay=1):
        """Sets The Delay Time After Which The BalloonTip Is Created."""

        if delay < 1:
            raise "\nERROR: Delay Time For BalloonTip Creation Should Be Greater Than 1 ms"

        self._startdelaytime = float(delay)


    def GetStartDelay(self):
        """Returns The Delay Time After Which The BalloonTip Is Created."""

        return self._startdelaytime


    def SetEndDelay(self, delay=2147483640):
        """Sets The Delay Time After Which The BalloonTip Is Destroyed."""

        if delay < 1:
            raise "\nERROR: Delay Time For BalloonTip Destruction Should Be Greater Than 1 ms"

        self._enddelaytime = float(delay)


    def GetEndDelay(self):
        """Returns The Delay Time After Which The BalloonTip Is Destroyed."""

        return self._enddelaytime


    def DisplayBalloon(self, icon_window):
        #self.BalloonFrame = BalloonFrame(self._widget, classparent=self)
        self.BalloonFrame = BalloonFrame(classparent=self, clickfunc=self._clickfunc)

        if wx.Platform != "__WXMAC__":
            self.BalloonFrame.SetBalloonShape(self)
        self.BalloonFrame.PositionBalloon(icon_window)
        self.destroytime = wx.PyTimer(self.DestroyTimer)
        self.destroytime.Start(self._enddelaytime)

        self.displayed = True
        self.BalloonFrame.Show(True)


    def UnDisplayBalloon(self):
        try:
            self.BalloonFrame.Destroy()
        except:
            pass

        self.displayed = False
        self.destroytime.Stop()
        del self.destroytime


    def DestroyTimer(self):
        """The Destruction Timer Has Expired. Destroys The BalloonTip Frame."""

        self.displayed = False
        self.destroytime.Stop()
        del self.destroytime

        try:
            self.BalloonFrame.Destroy()
        except:
            pass


    def SetBalloonShape(self, shape=BT_ROUNDED):
        """Sets The BalloonTip Frame Shape.

        It Should Be One Of BT_ROUNDED, BT_RECTANGLE.
        """

        if shape not in [BT_ROUNDED, BT_RECTANGLE]:
            raise '\nERROR: BalloonTip Shape Should Be One Of "BT_ROUNDED", "BT_RECTANGLE"'

        self._shape = shape


    def GetBalloonShape(self):
        """Returns The BalloonTip Frame Shape."""

        return self._shape


    def SetBalloonIcon(self, icon):
        """Sets The BalloonTip Top-Left Icon."""

        if icon.IsOk():
            self._topicon = icon
        else:
            raise "\nERROR: Invalid Image Passed To BalloonTip"


    def GetBalloonIcon(self):
        """Returns The BalloonTip Top-Left Icon."""

        return self._topicon


    def SetBalloonTitle(self, title=""):
        """Sets The BalloonTip Top Title."""

        self._toptitle = title


    def GetBalloonTitle(self):
        """Returns The BalloonTip Top Title."""

        return self._toptitle


    def SetBalloonMessage(self, message):
        """Sets The BalloonTip Tip Message. It Should Not Be Empty."""

        if len(message.strip()) < 1:
            raise "\nERROR: BalloonTip Message Can Not Be Empty"

        self._message = message


    def GetBalloonMessage(self):
        """Returns The BalloonTip Tip Message."""

        return self._message


    def SetBalloonTipStyle(self, tipstyle=BT_LEAVE):
        """Sets The BalloonTip TipStyle.

        It Should Be One Of BT_LEAVE, BT_CLICK, BT_BUTTON.
        """

        if tipstyle not in [BT_LEAVE, BT_CLICK, BT_BUTTON]:
            msg = '\nERROR: BalloonTip TipStyle Should Be One Of "BT_LEAVE", '\
                  '"BT_CLICK", "BT_BUTTON"'
            raise msg

        self._tipstyle = tipstyle


    def GetBalloonTipStyle(self):
        """Returns The BalloonTip TipStyle."""

        return self._tipstyle


    def SetBalloonColour(self, colour=None):
        """Sets The BalloonTip Background Colour."""

        if colour is None:
            colour = wx.Color(128, 128, 128)

        self._ballooncolour = colour


    def GetBalloonColour(self):
        """Returns The BalloonTip Background Colour."""

        return self._ballooncolour


    def SetTitleFont(self, font=None):
        """Sets The Font For The Top Title."""

        if font is None:
            font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD, False)

        self._balloontitlefont = font


    def GetTitleFont(self):
        """Returns The Font For The Top Title."""

        return self._balloontitlefont


    def SetMessageFont(self, font=None):
        """Sets The Font For The Tip Message."""

        if font is None:
            font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL, False)

        self._balloonmsgfont = font


    def GetMessageFont(self):
        """Returns The Font For The Tip Message."""

        return self._balloonmsgfont


    def SetTitleColour(self, colour=None):
        """Sets The Colour For The Top Title."""

        if colour is None:
            colour = wx.BLACK

        self._balloontitlecolour = colour


    def GetTitleColour(self):
        """Returns The Colour For The Top Title."""

        return self._balloontitlecolour


    def SetMessageColour(self, colour=None):
        """Sets The Colour For The Tip Message."""

        if colour is None:
            colour = wx.BLACK

        self._balloonmsgcolour = colour


    def GetMessageColour(self):
        """Returns The Colour For The Tip Message."""

        return self._balloonmsgcolour


    def OnDestroy(self, event):
        """Handles The Target Destruction."""

        if hasattr(self, "BalloonFrame"):
            if self.BalloonFrame:
                try:
                    #if isinstance(self._widget, wx.TaskBarIcon):
                        #self._widget.UnBind(wx.EVT_TASKBAR_MOVE)
                        #self.taskbartime.Stop()
                        #del self.taskbartime
                    #else:
                    #    self._widget.Unbind(wx.EVT_MOTION)
                    #    self._widget.Unbind(wx.EVT_LEAVE_WINDOW)
                    #    self._widget.Unbind(wx.EVT_ENTER_WINDOW)

                    self.BalloonFrame.Destroy()

                except:
                    pass

                del self.BalloonFrame


    def EnableTip(self, enable=True):
        """Enabel/Disable Globally The BalloonTip."""

        self._runningapp.__tooltipenabled__ = enable


@staticmethod
def DumpWindows():
    for w in wx.GetTopLevelWindows():
        print "-----------------------------------------------\n"
        print "GetId: ", w.GetId()
        print "GetLabel: ", w.GetLabel()
        print "GetName: ", w.GetName()
        print "GetPosition: ", w.GetPosition()
        print "GetPositionTuple: ", w.GetPositionTuple()
        print "GetClientRect: ", w.GetClientRect()
        print "GetScreenRect: ", w.GetScreenRect()
        spt = w.GetScreenPositionTuple()
        print "GetScreenPositionTuple(): ", spt
        print "Converted to Screen Coord: ", spt[0], spt[1]
        x, y = w.GetPositionTuple()
        x, y = w.ClientToScreenXY(x, y)
        print "ClientToScreenXY: x and y ", x, y
        print "ClientDisplayRect: ", wx.ClientDisplayRect()
        print "DisplaySize: ", wx.DisplaySize()
        print "ToolTip: ", w.GetToolTip()
        print "Class Name: ", w.GetClassName()
        print "GetTopLevelParent: ", w.GetTopLevelParent()
        print "IsTopLevel: ", w.IsTopLevel()
        print "-----------------------------------------------\n"


# Attempt to determine if a Taskbar is in use.  We assume that if the
# height and width of the Client Display rect is different than the
# Display rect then the task bar is available.  This obviously doesn't
# work in the case where the taskbar is closed, withdrawn or allows
# other windows on top.
def TaskBarExists():
    d_w, d_h = wx.DisplaySize()
    c_x, c_y, c_w, c_h = wx.ClientDisplayRect()

    if d_w != c_w: return True

    if d_h != c_h: return True

    return False

def GetWindowScreenQuadrant(x, y):
    d_w, d_h = wx.DisplaySize()
    c_x, c_y, c_w, c_h = wx.ClientDisplayRect()

    if x < d_w / 2:
        x_orient = "left"
    else:
        x_orient = "right"

    if y < d_h / 2:
        y_orient = "top"
    else:
        y_orient = "bottom"

    #print "GetWindowScreenQuadrent returns: ", y_orient

    return y_orient

def GetTaskBarPosition():
    d_w, d_h = wx.DisplaySize()
    c_x, c_y, c_w, c_h = wx.ClientDisplayRect()

    l = [(c_y, "top"), (d_h - c_y - c_h, "bottom"),
         (c_x, "left"), (d_w - c_x - c_w, "right")]

    def sorter(a, b):

        if a[0] < b[0] : return 1
        if a[0] > b[0] : return -1
        return 0

    l.sort(sorter)

    #print "GetTaskBarPosition:", l[0][1]
    return l[0][1]

def AdjustToDisplayRect(box_x, box_y, box_w, box_h, icon_w, icon_h):
    cdr_x, cdr_y, cdr_w, cdr_h = wx.ClientDisplayRect()

    # If it looks like a Taskbar exists then we probably don't need
    # to adjust for the icon_w and icon_h.  For example on Ubuntu
    # running on VirtualBox.  I've found that Ubuntu running natively
    # we can't tell if the Taskbar exists so we do need to adjust for
    # the icon.
    if TaskBarExists():
        icon_w = 0
        icon_h = 0

    # If we are to the left of the screen adjust to the edge of the screen
    if box_x < cdr_x:
        box_x = cdr_x

    # If we are off or extending off the right of the screen adjust
    # to so that our right edge touches the screen edge.
    elif box_x + box_w > cdr_w:
        # Why subtract the width of the icon?  On some systems the
        # cdr_w does not account for the taskbar so if we don't
        # account for the icon width (which is generally the width
        # of the taskbar) we could overlap the taskbar with the balloon
        # frame.  We prefer to error on the side of not overlapping with
        # the risk that we may not be positioned at the edge of the screen.
        box_x = cdr_w + cdr_x - box_w - icon_w

    # If we are above the top of the screen then adjust down.
    if box_y < cdr_y:
        box_y = cdr_y

    # If we are below the bottom of the screen adjust up
    elif box_y + box_h > cdr_h:
        # Why subtract the height of the icon?  On some systems the
        # cdr_h does not account for the taskbar so if we don't
        # account for the icon height (which is generally the height
        # of the taskbar) we could overlap the taskbar with the balloon
        # frame.  We prefer to error on the side of not overlapping with
        # the risk that we may not be positioned at the edge of the screen.
        box_y = cdr_h + cdr_y - box_h - icon_h

    return box_x, box_y
