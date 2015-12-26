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
import os
import time
import threading
import sys
import re
import traceback


class FileViewer(wx.Panel):
    '''
    A GUI component to display the contents of a file.
    '''

    def __init__(self, parent, ident, *args, **kwargs):

        _ = wx.GetTranslation

        wx.Panel.__init__(self, parent, ident, *args, **kwargs)

        self.current_path = None

        self.file_name = wx.StaticText(self, -1, "")
        self.status = wx.StaticText(self, -1, "")
        self.status_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.status_sizer.Add(self.file_name, 1, wx.ALL, 4)
        self.status_sizer.Add(self.status, 0, wx.ALL|wx.ALIGN_RIGHT, 4)

        #self.status.SetBackgroundColour(wx.Colour(0, 0, 255))

        self.text = wx.TextCtrl(self, -1,
            style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH)
        self.find_label = wx.StaticText(self, -1, _("Find:"))
        self.find_field = wx.TextCtrl(self, -1, style=wx.TE_PROCESS_ENTER,
                                      size=(250, -1))
        self.find_field.SetToolTipString(_("Enter text to find"))
        self.find_previous_button = wx.Button(self, -1, _("Previous"))
        self.find_previous_button.SetToolTipString(_("Find the previous occurrence of the text"))
        self.find_next_button = wx.Button(self, -1, _("Next"))
        self.find_next_button.SetToolTipString(_("Find the next occurrence of the text"))
        self.close_button = wx.Button(self, wx.ID_OK, _("&Close"))

        self.find_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.find_sizer.Add(self.find_label, 0, wx.LEFT|wx.ALIGN_CENTER, 8)
        self.find_sizer.Add(self.find_field, 0,
                            wx.BOTTOM|wx.TOP|wx.LEFT|wx.ALIGN_CENTER, 4)
        self.find_sizer.Add(self.find_previous_button, 0,
                            wx.LEFT|wx.ALIGN_CENTER, 8)
        self.find_sizer.Add(self.find_next_button, 0,
                            wx.ALL|wx.ALIGN_CENTER, 4)
        self.find_sizer.AddStretchSpacer(1)
        self.find_sizer.Add(self.close_button, 0, wx.RIGHT|wx.ALIGN_RIGHT|wx.ALIGN_CENTER, 8)

        # Hide "Close" button. Caller can show it using show_close_button()
        self.find_sizer.Hide(self.close_button)
        self.find_sizer.Layout()

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.main_sizer.Add(self.status_sizer, 0, wx.EXPAND)
        self.main_sizer.Add(self.text, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 4)
        self.main_sizer.Add(self.find_sizer, 0, wx.EXPAND)

        self.SetSizer(self.main_sizer)

        font = self.text.GetFont()
        font.SetFaceName("Monospace")
        self.text.SetFont(font)

        self.find_field.Bind(wx.EVT_CHAR, self.OnFindChar)
        self.find_next_button.Bind(wx.EVT_BUTTON, self.OnNext)
        self.close_button.Bind(wx.EVT_BUTTON, self.OnClose)
        self.find_previous_button.Bind(wx.EVT_BUTTON, self.OnPrev)
        self.text.Bind(wx.EVT_CHAR, self.OnChar)
        self.text.Bind(wx.EVT_LEFT_UP, self.OnMouseClick)
        self.Layout()
        self.find_field.SetFocus()

        self.find_field_bg_color = self.find_field.GetBackgroundColour()
        self.COLOR_PINK = wx.Colour(255, 128, 128)
        self.file_nbytes = 0
        self.poll_thread = None


    def show_close_button(self, parent_frame):
        '''
        Shows an Close button on bottom right of panel that sends a Close
        event to panel's parent

        parent_frame is the window frame we will call Close() on
        when the Close button is clicked
        '''
        self.parent_frame = parent_frame
        self.close_button.Show()
        self.main_sizer.Layout()


    def set_status(self, msg):
        '''
        Set the status message
        '''
        self.status.SetLabel(msg)
        self.status_sizer.Layout()


    def load_file(self, path):
        '''
        Load and display the contents of a file
        '''
        self.file_nbytes = 0
        self.text.Clear()

        try:
            self._load_file_bytes(path)
        except Exception, e:
            self.text.Clear()
            self.text.AppendText(_("Could not load log file.\n"))
            self.text.AppendText(traceback.format_exc())
            return 

        self.current_path = path
        self.text.SetInsertionPointEnd()
        self.text.ShowPosition(self.text.GetInsertionPoint())
        statinfo = os.stat(self.current_path)
        self.file_nbytes = statinfo.st_size
        self.poll_thread = PollFile()
        self.poll_thread.poll(self._poll_callback, 2)
        self.file_name.SetLabel(path)
        self.update_status()

    def unload_file(self):
        '''
        Unload the file and top the polling thread
        '''
        if self.poll_thread is not None:
            self.poll_thread.do_cancel()
        self.file_nbytes = 0
        self.file_name.SetLabel("")
        self.text.Clear()

    def _load_file_bytes(self, path):
        '''
        Load file into the text field. We do this ourselves since using
        textctrl.LoadFile(path) doesn't handle encoding errors gracefully
        (bug 1871)
        '''
        f = open(path)
        try:
            chunk_size = 1024
            s = f.read(chunk_size)
            while len(s) > 0:
                n = self._append_bytes(s)
                if n < 0:
                    break;
                s = f.read(chunk_size)

        finally:
                f.close()

    def _append_bytes(self, bytes):
        '''
        Convert bytes to unicode and append to text field.
        We can't ust call text.AppendText() with the raw bytes
        because it can fail with a UnicodeDecodeError.
        '''
        try:
            # Convert bytes to unicode. Have any unknown characters silently
            # replaced instead of throwing an error.
            s_enc = unicode(bytes, errors='replace')
            self.text.AppendText(s_enc)
            return len(s_enc)
        except Exception, e:
            self.text.Clear()
            self.text.AppendText(_("Could not load log file.\n"))
            self.text.AppendText(traceback.format_exc())
            return -1

    def update_status(self):
        '''
        Update the line number displayed in the status
        '''
        nlines = self.text.GetNumberOfLines()
        if '__WXMAC__' in wx.PlatformInfo:
            # On Mac PositionToXY() does not work well, so we don't
            # show the line number on the Mac
            msg = ("%d" % (nlines))
        else:
            (x, y) = self.text.PositionToXY(self.text.GetInsertionPoint())
            x = x  # Silence pylint
            msg = ("%d:%d" % (y+1, nlines))

        self.set_status(msg)


    def _poll_callback(self):
        '''
        Called by polling thread. Do some work then return True
        to continue polling else return False.
        '''

        try:
            # Make sure file view is up to date
            wx.CallAfter(self.refresh_file)
            return True
        except wx._core.PyDeadObjectError:
            # Dialog is in process of being destroyed
            pass

        return False


    def refresh_file(self):
        '''
        If file has grown, append new content
        '''
        if self.current_path is None or len(self.current_path) == 0:
            return False

        statinfo = os.stat(self.current_path)
        new_byte_count = statinfo.st_size - self.file_nbytes
        #print "new_byte_count = %d" % new_byte_count

        if new_byte_count == 0:
            # File size has not changed -- nothing to do
            return False
        elif new_byte_count < 0:
            # File size has shrunk, reload file
            self.load_file(self.current_path)
            return True
        else:
            # File has grown in size. Load new bytes
            self.text.SetInsertionPointEnd()
            try:
                stream = open(self.current_path)
                stream.seek(self.file_nbytes)
                line = stream.readline()
                while line is not None and len(line) > 0:
                    self._append_bytes(line)
                    line = stream.readline()
            finally:
                stream.close()
            self.file_nbytes += new_byte_count
            self.update_status()
            return True


    def _get_start_position(self, direction):
        '''
        Return position to start search from . This is at the
        current selection
        '''
        (n_from , n_to) = self.text.GetSelection()
        if n_from == n_to:
            return self.text.GetInsertionPoint()
        if direction == 1:
            # Forwards. Start search from end of selection
            return n_to
        else:
            # Backwards. Start search from start of selection
            return n_from


    def find(self, search_pattern, direction=1):
        '''
        Find the next/prev occurance of pattern starting at the current
        insertion point. Scroll window to make line with hit visible
        set direction to -1 to search previous
        '''
        start_pos = self._get_start_position(direction)
        last_pos =  self.text.GetLastPosition()

        # We search by process chunks of text. Set the maximum chunk size
        max_chunk_size = 8 * 1024

        pattern = search_pattern.lower()
        wrapped = False
        pos = start_pos
        while not wrapped or ((direction == 1 and pos < start_pos) or \
                              (direction == -1 and pos > start_pos)) :
            if direction == 1:
                chunk_size = min(max_chunk_size, last_pos - pos)
                text_to_search = self.text.GetRange(pos,
                                                    pos + chunk_size).lower()
                index = text_to_search.find(pattern)
            else:
                chunk_size = min(max_chunk_size, pos)
                text_to_search = self.text.GetRange(pos - chunk_size,
                                                    pos).lower()
                index = text_to_search.rfind(pattern)

            del text_to_search

            if index >= 0:
                # Hit!
                if direction == 1:
                    hit_pos = pos + index
                else:
                    hit_pos = (pos - chunk_size) + index

                # Set insertion point and scroll window
                self.text.SetSelection(hit_pos, hit_pos + len(pattern))
                self.text.ShowPosition(hit_pos)
                # We force focus to the text window to ensure the hilighting
                # of the found text is visible. See bug 2141.
                self.text.SetFocus()
                self.update_status()
                return hit_pos
            pos += (chunk_size * direction)
            #print "wrapped=%s pos=%d start_pos=%d" % (wrapped, pos, start_pos)

            # Check for wrap
            if not wrapped and direction == 1 and pos >= last_pos:
                pos = 0
                wrapped = True
            elif not wrapped and direction == -1 and pos <= 0:
                pos = last_pos
                wrapped = True

        return -1


    def OnFindChar(self, event):
        '''
        Handle Return and Shift Return key in Find field
        '''
        if event.GetKeyCode() == 13:
            if event.ShiftDown():
                self.OnPrev(event)
            else:
                self.OnNext(event)
        else:
            event.Skip()


    def OnChar(self, event):
        '''
        Used to update row number in status message, and
        allow Return key in log text window to find
        '''
        wx.CallAfter(self.update_status)
        if event.GetKeyCode() == 13:
            if event.ShiftDown():
                self.OnPrev(event)
            else:
                self.OnNext(event)
        else:
            event.Skip()


    def OnMouseClick(self, dummyevent):
        '''
        Used to update row number in status message
        '''
        wx.CallAfter(self.update_status)
        dummyevent.Skip()


    def OnNext(self, dummyevent):
        '''
        Find Next button
        '''
        wx.BeginBusyCursor()
        i = self.find(self.find_field.GetValue(), 1)
        wx.EndBusyCursor()
        if i < 0:
            wx.Bell()
            self.find_field.SetBackgroundColour(self.COLOR_PINK)
        else:
            self.find_field.SetBackgroundColour(self.find_field_bg_color)


    def OnClose(self, dummyevent):
        '''
        Handle click on Close button
        '''
        self.parent_frame.Close()


    def OnPrev(self, dummyevent):
        '''
        Find Previous button
        '''
        wx.BeginBusyCursor()
        i = self.find(self.find_field.GetValue(), -1)
        wx.EndBusyCursor()
        if i < 0:
            wx.Bell()


class PollFile(threading.Thread):
    '''
    Small thread that detects when the file has changed and updates
    it in the tet window
    '''

    def __init__(self, *args, **kwds):
        threading.Thread.__init__(self, name="PollLogFile")

        self.interval = 5
        self.cancel = False
        self._poll_callback = None
        self.daemon = True

    def poll(self, callback, interval):
        '''
        Start polling for changes on file
        callback is the function called every poll interval
        '''
        self._poll_callback = callback
        self.interval = interval
        self.cancel = False
        self.start()

    def do_cancel(self):
        '''
        Cancel polling
        '''
        self.cancel = True

    def run(self):
        '''
        Do poll
        '''
        while not self.cancel:
            if self._poll_callback():
                # If _poll_callback() returns True keep going
                time.sleep(self.interval)
            else:
                self.cancel = True


if __name__ == "__main__":
    class MainWindow(wx.Frame):
        '''
        Main window when running standalone
        '''

        def __init__(self, parent, wid, title, file_path=""):

            wx.Frame.__init__(self, parent, wid, title, size=(800, 400))

            logfileviewer = FileViewer(self, -1)
            logfileviewer.load_file(file_path)

            sizer = wx.BoxSizer(wx.VERTICAL)

            sizer.Add(logfileviewer, 1, wx.EXPAND)
            self.SetSizer(sizer)
            self.Layout()
            self.Show(True)


    if len(sys.argv) > 1:
        fpath = sys.argv[1]
    else:
        fpath = ""

    app = wx.PySimpleApp()
    frame = MainWindow(None, wx.ID_ANY, 'File Viewer', file_path=fpath)
    app.MainLoop()

