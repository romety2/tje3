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
#from wx.lib.throbber import Throbber

'''
A BitmapTextButton is a text button with a bitmap on the left.
The bitmap should typically be a small 16x16 bitmap
You must provide the "bitmap" attribute in the constructor
'''
class BitmapTextButton(wx.BitmapButton):

    def __init__(self, *args, **kwds):

        self.label = None
        self.bitmap = None

        if 'label' in kwds:
            tmp_label = kwds['label']
            del kwds['label']

        if 'bitmap' in kwds:
            self.bitmap = kwds['bitmap']
        else:
            raise "bitmap attribute must be supplied"

        wx.BitmapButton.__init__(self, *args, **kwds)

        self.SetLabel(tmp_label)
        self.Layout()


    def SetLabel(self, label=""):
        '''
        Set a text label on the button
        '''

        if self.label is not None and self.label == label:
            return

        button_size = self.GetSize()

        # Figure out how much vertical padding the button has around the
        # bitmap
        h_pad = button_size.GetHeight() - self.bitmap.GetHeight()
        self.label = label

        # Create a new bitmap from the button glyph and the label string
        bmp = self._create_bitmap_with_text(self.bitmap, label)

        # Put bitmap on button
        self.SetBitmapLabel(bmp)

        # Make sure button is the correct size
        self.SetSize(wx.Size(bmp.GetWidth() + 8, bmp.GetHeight() + h_pad))

    def _create_bitmap_with_text(self, bmp=None, label=""):

        if bmp is None:
            return bmp

        # Use the client DC to get the font to use and the dimensions
        # of the text label
        dc = wx.ClientDC(self)
        (t_width, t_height) = dc.GetTextExtent(label)
        font = self.GetFont()

        # Get dimenions of glyph
        b_width = bmp.GetWidth()
        b_height = bmp.GetHeight()

        # Figure out dimensions of new bitmap for button
        # The width is the text width + glyph width + padding
        # The height is the max(text height, glyph height)
        new_width = t_width + b_width + 5
        if b_height > t_height:
            new_height = b_height
        else:
            new_height = t_height

        # Allocate empty bitmap and draw glyph and text into it
        new_bmp = wx.EmptyBitmap(new_width, new_height)
        dc = wx.MemoryDC(new_bmp)
        dc.SetFont(font)
        dc.Clear()

        # Draw glyph, then draw text
        y = (new_height - b_height) / 2
        dc.DrawBitmap(bmp, 0, y, useMask=True)

        y = (new_height - t_height) / 2
        dc.DrawText(label, b_width + 5, y)

        return new_bmp
