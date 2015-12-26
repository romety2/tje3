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

import sys
from time import localtime, strftime

import wx
import wx.lib.mixins.listctrl  as  listmix

import common.task as task
import common.info as INFO
import common.basicfeed as BF
import swupdate.consts as CONST
from common.fsutils import fsenc
from common import ips, utils
from common.widgets.appthrobber import ThrobberLabel

from swupdate.logdialog import LogDialog

APP_LONG_NAME = INFO.UPDATE_APP_NAME

DLG_UPDATE_START    = -1
DLG_UPDATE_PROGRESS = -2
DLG_UPDATE_ERROR    = -3
DLG_UPDATE_DONE     = -4

IMAGE_EMPTY   = 0
IMAGE_WORKING = 1
IMAGE_DONE    = 2
IMAGE_ERROR   = 3

class ImageListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):

    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

# The InstallDialog will return the number of images updated as its
# return code.
class InstallDialog(wx.Dialog):

    def __init__(self, *args, **kwds):
        self.task = kwds['task']
        del kwds['task']
        self.frame = kwds['frame']
        del kwds['frame']

        wx.Dialog.__init__(self, *args, **kwds)

        self.selected_row = -1
        self.total_images_count = 0
        self.successful_images_count = 0

        self.bit_image_list = wx.ImageList(16, 16)

        bmp = wx.EmptyBitmap(16, 16)
        dc = wx.MemoryDC(bmp)
        dc.Clear()
        dc.SelectObject(wx.NullBitmap)

        self.im_empty = self.bit_image_list.Add(bmp)

        self.im_arrow = self.bit_image_list.Add(
                                     wx.ArtProvider.GetBitmap(
                                                      wx.ART_GO_FORWARD,
                                                      wx.ART_OTHER, (16, 16)))
        #self.im_done = self.bit_image_list.Add(
        #                            wx.ArtProvider.GetBitmap(
        #                                              wx.ART_TICK_MARK,
        #                                              wx.ART_OTHER, (16, 16)))
        self.im_done = self.bit_image_list.Add(
                                     utils.get_image("check-16x16.png"))
        self.im_warn = self.bit_image_list.Add(
                                     wx.ArtProvider.GetBitmap(
                                                      wx.ART_WARNING,
                                                      wx.ART_OTHER, (16, 16)))

        self.list = ImageListCtrl(self, -1, style=wx.LC_REPORT
                                             | wx.BORDER_SUNKEN
                                             | wx.LC_SINGLE_SEL)

        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListItemSelected,
                       self.list)
        self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnListItemDeSelected,
                       self.list)
        self.list.SetImageList(self.bit_image_list, wx.IMAGE_LIST_SMALL)

        columns = \
            [ # Label                  Width      Format
              (_(" "),                 22,        wx.LIST_FORMAT_CENTER),
              (_("Application Image"), 260,       wx.LIST_FORMAT_LEFT),
              (_("Size"),              65,        wx.LIST_FORMAT_RIGHT)
            ]

        col_info = wx.ListItem()
        col_info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT | wx.LIST_MASK_WIDTH
        for index, col in enumerate(columns):
            col_info.m_text = col[0]
            col_info.m_width = col[1]
            col_info.m_format = col[2]
            self.list.InsertColumnInfo(index, col_info)
            # On Windows wx.LIST_AUTOSIZE_USEHEADER seems to be ignored if
            # if it is set via InsertColumnInfo.
            if col[1] ==  wx.LIST_AUTOSIZE_USEHEADER:
                self.list.SetColumnWidth(index, wx.LIST_AUTOSIZE_USEHEADER)

        self.list.setResizeColumn(2)

        # On Windows the list needs to know its size.
        self.list.SetMinSize((410, 200))

        # On Mac OS a 10 point font is too small.
        if '__WXMAC__' == wx.Platform:
            font_size = 12
        else:
            font_size = 10

        self.image_name = ThrobberLabel(self, -1, " ",
                                               font_size=font_size,
                                               font_weight=wx.NORMAL)

        self.status_text = wx.StaticText(self, -1, " ")
        self.status_text.SetFont(wx.Font(font_size, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False))
        self.status_text.Wrap(410)
        # Workaround for issue 1301
        if '__WXMAC__' == wx.Platform:
            self.status_text.SetMinSize((410, 20))

        self.log_button = wx.Button(self, -1, _("Show Install Details"))
        self.Bind(wx.EVT_BUTTON, self.OnLog, self.log_button)
        self.log_button.SetToolTipString(
             _("Display the installation log for a selected application image"))
        self.log_button.Disable()

        self.cancel_button = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.cancel_button)
        self.cancel_button.SetToolTipString("Stop Installation")
        self.cancel_button.SetDefault()

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self.list, 1, wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, 8)
        vsizer.Add(self.image_name, 0, wx.EXPAND | wx.RIGHT | wx.LEFT | wx.BOTTOM, 8)
        vsizer.Add(self.status_text, 0, wx.RIGHT | wx.LEFT | wx.BOTTOM | wx.EXPAND, 8)
        vsizer.Add((8,8))

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(self.log_button, 0, wx.RIGHT |  wx.ALIGN_RIGHT, 8)
        hsizer.Add(self.cancel_button, 0, wx.ALIGN_RIGHT, 8)
        vsizer.Add(hsizer, 0, wx.ALL | wx.ALIGN_RIGHT, 8)

        self.SetSizer(vsizer)
        vsizer.Fit(self)
        #vsizer.SetSizeHints(self)
        self.Layout()

        # Center the dialog over the frame.
        self.Centre()

        # These events are generated by the Tracker.
        self.Bind(task.EVT_TASK_PROGRESS_START, self.OnTaskProgressStart)
        self.Bind(task.EVT_TASK_PROGRESS, self.OnTaskProgress)
        self.Bind(task.EVT_TASK_FINISHED, self.OnTaskFinished)
        self.Bind(task.EVT_CANCEL_ABILITY_CHANGE, self.OnCancelEnable)
        self.Bind(task.EVT_TASK_DURATION_CHANGED, self.OnTaskDurationChanged)
        self.Bind(task.EVT_TASK_LOG, self.OnTaskLog)

        # Set the focus to the canel button to enable proper tab nav.
        self.cancel_button.SetFocus()


    def OnCancel(self, event):
        self.cancel_button.SetFocus()
        if self.task.is_running():
            self.task.interrupt()
        else:
            self.SetReturnCode(self.successful_images_count)
            event.Skip()


    def OnLog(self, event):

        for img_details in self.images_to_be_updated:
            if img_details['id'] == self.selected_row:
                dlg = LogDialog(self, -1,
                                       _("%(APP_NAME)s: Installation Details") %
                                                    {'APP_NAME':APP_LONG_NAME},
                                       img_details=img_details)
                dummy = dlg.ShowModal()
                dlg.Destroy()


    def OnCancelEnable(self, event):
        self.cancel_button.Enable(event.enable)
        self.cancel_button.SetFocus()
        wx.YieldIfNeeded()


    def OnListItemSelected(self, evt):
        list = evt.GetEventObject()
        self.selected_row = list.GetItemData(evt.m_itemIndex)
        self.log_button.Enable()


    def OnListItemDeSelected(self, evt):
        self.log_button.Disable()


    def OnTaskProgressStart(self, event):
        pass


    def OnTaskLog(self, event):
        log(self.working_image, utils.to_unicode(event.msg))


    def OnTaskProgress(self, event):

        # The event.id maps to the list's row data

        # An update of an image has started
        if event.sequence == DLG_UPDATE_START:
            self.working_image = None

            # Mark the row as working (being updated)
            index = self.list.FindItemData(-1, event.id)
            self.list.SetItemImage(index, IMAGE_WORKING)

            for img_details in self.images_to_be_updated:
                if event.id == img_details['id']:
                    self.working_image = img_details
                    break

            if self.working_image == None:
                # XXX: Assert working_image is not None
                pass

            if img_details['type'] == CONST.T_NORMAL:
                status_msg = _("Updating: ") + \
                              ips.get_image_title(
                                          fsenc(self.working_image['imgroot']),
                                          opname='image-update')
            elif img_details['type'] == CONST.T_ADD_ON:
                item = self.working_image['add_on_image_list'][0]
                target_id = item['id']
                imgroot = self.image_list[target_id]['imgroot']

                status_msg = _("Installing Add-On for: ") + \
                              ips.get_image_title(fsenc(imgroot),
                                                  opname='image-update')
            elif img_details['type'] == CONST.T_NEW_IMAGE:
                status_msg = _("Installing application: ") + \
                                                  self.working_image['title']

            self.image_name.set_status(status_msg)
            self.image_name.throb(on=True)
            self.status_text.SetLabel(utils.to_unicode(self.task.__str__()))
        elif event.sequence == DLG_UPDATE_DONE:
            index = self.list.FindItemData(-1, event.id)
            self.image_name.throb(on=False)
            self.list.SetItemImage(index, IMAGE_DONE)
            self.successful_images_count+=1
            # Mark installation as successful
            self.working_image['installed'] = True
        elif event.sequence == DLG_UPDATE_ERROR:
            index = self.list.FindItemData(-1, event.id)
            self.list.SetItemImage(index, IMAGE_ERROR)
            self.image_name.throb(on=False)
            log(self.working_image, _("Installation failed"))
            # Mark installation as not successful
            self.working_image['installed'] = False
        else:
            self.status_text.SetLabel(utils.to_unicode(self.task.__str__()))


    def OnTaskFinished(self, event):

        if self.task.get_result()[0] == task.TASK_END_USER_ABORT:
            self.image_name.set_status (_("Software update cancelled"))
            # The user aborted.  Clear the arror in the first column.
            index = self.list.FindItemData(-1, self.working_image['id'])
            self.list.SetItemImage(index, IMAGE_EMPTY)
        else:
            self.image_name.set_status (_("Software update complete"))

        self.status_text.SetLabel(_("    %s of %s image(s) updated") % \
                        (self.successful_images_count, self.total_images_count))
        self.image_name.throb(on=False)
        self.cancel_button.SetLabel(_("&Close"))
        self.cancel_button.SetToolTipString("Close Dialog")
        self.cancel_button.SetFocus()

        # Select the first item in the list.
        self.list.Select(0)

        self.frame.Raise()
        self.frame.Show()
        self.Raise()


    def OnTaskDurationChanged(self, event):
        pass


    def set_image_list(self, selected_image_list, all_dict):

        self.image_list = all_dict

        # From the list of images with updates we only want to update those
        # that have the checkbox checked.

        self.images_to_be_updated = selected_image_list
        self.total_images_count = 0

        for img_details in selected_image_list:

            if img_details['type'] == CONST.T_NORMAL or \
               img_details['type'] == CONST.T_NEW_IMAGE:
                index = self.list.InsertImageItem(sys.maxint, IMAGE_EMPTY)
                self.list.SetItemData(index, img_details['id'])

                if img_details['type'] == CONST.T_NORMAL:
                    self.list.SetStringItem(index, 1,
                             ips.get_image_title(fsenc(img_details['imgroot']),
                             opname='image-update'))
                else:
                    self.list.SetStringItem(index, 1, img_details['title'])

                self.list.SetStringItem(index, 2,
                     utils.readable_size(img_details['size']))

            elif img_details['type'] == CONST.T_ADD_ON:
                index = self.list.InsertImageItem(sys.maxint, IMAGE_EMPTY)
                self.list.SetItemData(index, img_details['id'])

                item = img_details['add_on_image_list'][0]

                if img_details['feed_entry'].has_key(BF.TITLE):
                    title = img_details['feed_entry'][BF.TITLE]
                else:
                    title = _("Untitled Add-On")

                if item['sequence'] > 0:
                    title += " (#%d)" % item['sequence']

                self.list.SetStringItem(index, 1, title)
                self.list.SetStringItem(index, 2,
                     utils.readable_size(img_details['size']))

            # Reset the installation log
            img_details['log'] = []
            self.total_images_count += 1


def log(img, msg):
    img['log'].append(strftime("%H:%M:%S: ", localtime()) + msg + "\n")
