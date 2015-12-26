#!/usr/bin/env python
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

"""The Main Frame of the Software Update application"""

if False:    # Keep Pylint happy
    import gettext
    _ = gettext.gettext

###############################################################################
####### T H E  O R D E R  O F  I M P O R T S  I S  I M P O R T A N T
###############################################################################
import common.boot as boot
import os.path
import sys

import Queue

import wx
import wx.richtext
import wx.html
from pkg.client import global_settings

from common import ips, ipcservice, utils, fileutils
from common.fsutils import fsenc, fsdec
import common.lockmanager as lockmanager
import gui.views as views

from common import listers

import common.info as INFO
import common.basicfeed as BF
import swupdate.consts as CONST
import swupdate.licensedialog as LD
from common.basicfeed import BasicFeed
from common.widgets.checklistctrl import CheckListCtrl
from swupdate.checklistctrl import UpdatesCheckListCtrl
from common.widgets.appthrobber import ThrobberLabel
from swupdate.installdialog import InstallDialog
from common.ips.installtask import MultiImageTask

APP_LONG_NAME = INFO.UPDATE_APP_NAME
APP_CMD_NAME = INFO.CMD_NAME
APP_CLIENT_NAME = INFO.UPDATE_CLIENT_NAME

LOGO_IMAGE_NAME = "application-update-tool-48x48.png"
SECURITY_IMAGE_NAME = "security-16-12.png"
REFRESH_IMAGE_NAME = "menu-refresh-16x16.png"

ADVERT_BASE_URL = "http://pkg.oracle.com/layered/ads/"
ADVERT_COUNT = 10

ID_APP_CENTER = wx.NewId()
ID_CLOSE = wx.NewId()
ID_VAR_BTN = wx.NewId()
ID_LICENSE_BTN = wx.NewId()

BTNS_CHECKING = 1
BTNS_INSTALL  = 2
BTNS_CLOSING  = 3
BTNS_STOPPING = 4
BTNS_STOPPED  = 5

TEXT_NEW_SW_AVAILABLE = _("New software is available.")
TEXT_UPDATES_AVAILABLE = _("Select the items you want, then click Install.")
TEXT_NO_UPDATES_AVAILABLE = _("Software is up-to-date.")
TEXT_NO_UPDATES_FOUND = _("No updates found.")



class MainFrame(wx.Frame):
    """The main frame of the Software Update application"""

    _ = wx.GetTranslation

    def __init__(self, *args, **kwargs):

        self.config = kwargs['prefs']
        del kwargs['prefs']
        self.options = kwargs['options']
        del kwargs['options']
        self.image_list = kwargs['image_list']
        del kwargs['image_list']
        self.on_close_func = kwargs['on_close_func']
        del kwargs['on_close_func']
        self.update_notifier_func = kwargs['update_notifier_func']
        del kwargs['update_notifier_func']
        self.add_on_exists = kwargs['add_on_exists']
        del kwargs['add_on_exists']

        #self.debug = self.options['debug']

        wx.Frame.__init__(self, *args, **kwargs)

        global_settings.client_name = APP_CLIENT_NAME
        self.last_id = -1
        self.ad_displayed = False
        self.addon_check_lock = False

        # Indicates to the notifier that it should not update the SW Update
        # with a new image list because it is busy installing updates.
        self.busy = False

        # This queue holds update data from the worker threads to be processed
        # by the main GUI thread.
        self.update_queue = Queue.Queue()
        # This queue holds add-on and new sw data from the worker thread to
        # be processed by the main GUI thread.
        self.newsw_queue = Queue.Queue()

        icon_bundle = wx.IconBundle()
        if wx.Platform == "__WXMSW__":
            # Using an .ico file results in the icon being displayed
            # when a user uses alt-tab.
            for size in [16, 32, 48]:
                try:
                    icon = wx.Icon(os.path.join(
                                     os.path.dirname(__file__),
                                     "..", "images",
                                     'application-update-tool.ico'),
                                   wx.BITMAP_TYPE_ICO,
                                   desiredWidth=size, desiredHeight=size)
                    icon_bundle.AddIcon(icon)
                except:
                    pass
        else:
            for size in [16, 48, 72]: # glob module
                icon_bundle.AddIconFromFile(fsdec(os.path.join(
                                      os.path.dirname(__file__), "..",
                                      "images",
                                      "application-update-tool-%sx%s.png" % (size, size))),
                                      wx.BITMAP_TYPE_ANY)
        self.SetIcons(icon_bundle)


        self.lists = {}

        # This is a dict of dicts that contain information about images
        # which have pending updates, new software to install or add-ons
        # to be applied to existing images.
        # The outer dict uses an 'id':value pair per entry
        # The value is a dict that contains information about the image:
        #   'id'                 ID for the image
        #   'type'               Updates, Add-on, New Software
        #   'imgroot'            Path of the image
        #   'size'               Size of the update/add-on across all pkgs
        #   'security'           This update contains pkgs with security fixes
        #   'pkgs'               A list of pkgs which have pending updates.
        #   'log'                Installation log (if updates applied).
        #   'checked'            Is this item selected in the UI list
        #   'installed'          Boolean: Was installation successful?
        #   'imageplan'          The imageplan generated during the update
        #                        check.
        #   'feed_entry'         The feed entry for this add-on/new sw
        #   'title'              NewSW: Image title
        #   'description'        NewSW: Image description
        #   'publishers'         NewSW: list of tuples containing:
        #                              (pubname, origin, preferred flag,
        #                               ssl key, ssl cert, disabled flag)
        #   'add_on_image_list'  A list of dicts of images the add-on could
        #                        apply to.
        #
        # A pkg in the pkgs list is a dict defined as:
        #   'fmri'               The pkg fmri string
        #   'size'               Size of the update in bytes
        #   'title'              Title of the pkg
        #   'version'            Version of the pkg
        #   'security'           Whether this update contains a security fix.
        #   'publisher'          The publisher of the update for this pkg.
        #   'detailed-url'       A URL to more info about this pkg.
        #
        # The add_on_image_list dict looks like this:
        #   'id'                 ID of image from the image_list that this
        #                        add-on could be applied to.
        #   'selected'           Whether this image is currently selected to
        #                        have this add-on applied to it.
        #   'sequence'           Tracks sequence of add_on (1, 2, 3, etc)
        #
        if self.image_list == None:
            self.image_list = self.load_images_list()
            self.standalone = True
        else:
            self.image_list_count = len(self.image_list)
            self.standalone = False

        # Indicates the license agreement has not be accepted.
        self.license_accepted = False

        utils.set_net_proxy(self.config)

        self.SetTitle(APP_LONG_NAME)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.panel = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.logo_bitmap = utils.get_image(LOGO_IMAGE_NAME)
        if not self.logo_bitmap:
            utils.logger.error("Could not create logo image.")
            sys.exit(1)
        stb = wx.StaticBitmap(self.panel, -1, self.logo_bitmap)

        self.top_bold_stt = wx.StaticText(self.panel, -1, " ")
        if wx.Platform == "__WXMAC__":
            self.top_bold_stt.SetFont(
                             wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD, False))
        else:
            self.top_bold_stt.SetFont(
                             wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, False))

        self.top_stt = wx.StaticText(self.panel, -1, " ")
        if wx.Platform == "__WXMAC__":
            self.top_stt.SetFont(
                          wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False))
        else:
            self.top_stt.SetFont(
                          wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False))

        intro_sizer = wx.BoxSizer(wx.VERTICAL)
        intro_sizer.Add(self.top_bold_stt, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        intro_sizer.Add(self.top_stt, 0, wx.ALL | wx.ALIGN_LEFT, 5)

        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_sizer.Add(stb, 0, wx.ALL | wx.ALIGN_CENTER, 5)
        top_sizer.Add(intro_sizer, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # List Control: Software Updates
        update_columns = \
                  [ # Label                Width      Format
                   (_("  "),               26,        wx.LIST_FORMAT_CENTER),
                   (_("Software Updates"), 355,       wx.LIST_FORMAT_LEFT),
                   (_(" "),                25,        wx.LIST_FORMAT_RIGHT),
                   (_("Size"),             70,        wx.LIST_FORMAT_RIGHT),
                   (_(" "),                 0,        wx.LIST_FORMAT_RIGHT)
                  ]
        self.lists["updates"] = self._init_list_ctrl(
                                        columns=update_columns,
                                        size_col=2,
                                        sort_col=1)

        self.lists["updates"]._prev_sort_flag = 1
        self.lists["updates"]._sort_col = -1
        self.lists["updates"].old_OnCheckItem = self.lists["updates"].OnCheckItem
        self.lists["updates"].OnCheckItem = self.OnUpdateListCheckItem

        if wx.Platform == "__WXMSW__":
            self.lists["updates"].Bind(wx.EVT_KEY_UP, self.OnUpdateListKeyUp)

        self.refresh_bitmap = utils.get_image(REFRESH_IMAGE_NAME)
        self.refresh_btn = wx.BitmapButton(self.panel, wx.ID_REFRESH,
                                           self.refresh_bitmap)
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.refresh_btn)
        self.refresh_btn.SetToolTipString(_("Check for new updates"))
        self.refresh_btn.Disable()

        self.security_bitmap = utils.get_image(SECURITY_IMAGE_NAME)
        if not self.security_bitmap:
            utils.logger.error("Could not create security image.")
            sys.exit(1)
        self.security_stb = wx.StaticBitmap(self.panel, -1,
                                            self.security_bitmap)

        self.security_stt = wx.StaticText(self.panel, -1,
                                        _("- Includes security enhancement"))
        if wx.Platform == "__WXMAC__":
            self.security_stt.SetFont(wx.Font(10, wx.DEFAULT,
                                                  wx.NORMAL,
                                                  wx.NORMAL, False))
        else:
            self.security_stt.SetFont(wx.Font(8, wx.DEFAULT,
                                                 wx.NORMAL,
                                                 wx.NORMAL, False))
        self.security_stt.Hide()
        self.security_stb.Hide()

        self.middle_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.middle_sizer.Add(self.refresh_btn, 0, wx.LEFT | wx.ALIGN_LEFT, 3)
        self.middle_sizer.Add((1,1), 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 4)
        self.middle_sizer.Add(self.security_stb, 0, wx.BOTTOM
                                                          | wx.ALIGN_RIGHT
                                                          | wx.ALIGN_TOP, 0)
        self.middle_sizer.Add(self.security_stt, 0,  wx.LEFT
                                                   | wx.TOP
                                                   | wx.RIGHT
                                                   | wx.ALIGN_TOP, 3)

        # On Mac OS a 10 point font is too small.
        if '__WXMAC__' == wx.Platform:
            font_size = 12
        else:
            font_size = 10

        # Need to initialize this with at least a space so that the throbber
        # will correctly layout on Mac OS.
        self.status = ThrobberLabel(self.panel, -1, " ",
                                              font_size=font_size,
                                              font_weight=wx.NORMAL)

        self.middle_sizer.Add(self.status, 0, wx.LEFT | wx.RIGHT |
                                           wx.EXPAND, 10)

        # Forces the list to paint the rows in alternating colors
        self.lists["updates"].OnSortOrderChanged()

        # Perform the intial sort of the contents.
        #self.lists["updates"].sort(
        #               column=self.lists["updates"]._sort_col,
        #               order=self.lists["updates"]._prev_sort_flag)

        tmp_str = _("New Software and Add-Ons")

        # List Control: New Software
        new_sw_columns = \
                  [ # Label             Width         Format
                   (_("  "),            26,           wx.LIST_FORMAT_CENTER),
                   (tmp_str,            320,          wx.LIST_FORMAT_LEFT),
                   (_("Version"),       60,           wx.LIST_FORMAT_LEFT),
                   (_("Size"),          70,           wx.LIST_FORMAT_RIGHT),
                   (_(" "),              0,           wx.LIST_FORMAT_RIGHT)
                  ]
        self.lists["new"] = self._init_list_ctrl(
                                        columns=new_sw_columns,
                                        size_col=3,
                                        sort_col=1,
                                        update_list_type=False)

        self.lists["new"]._prev_sort_flag = 1
        self.lists["new"]._sort_col = -1
        self.lists["new"].old_OnCheckItem = self.lists["new"].OnCheckItem
        self.lists["new"].OnCheckItem = self.OnNewListCheckItem
        if not self.add_on_exists:
            self.lists["new"].Show(False)

        if wx.Platform == "__WXMSW__":
            self.lists["new"].Bind(wx.EVT_KEY_UP, self.OnNewListKeyUp)

        # Forces the list to paint the rows in alternating colors
        self.lists["new"].OnSortOrderChanged()

        # Perform the intial sort of the contents.
        #self.lists["new"].sort(
        #               column=self.lists["new"]._sort_col,
        #               order=self.lists["new"]._prev_sort_flag)

        self.desc_html = InfoHtmlWindow(self.panel, size=(495, 85), style=wx.SUNKEN_BORDER)

        self.license_sizer = self._build_license_area()
        self.bottom_sizer = self._build_bottom_buttons()

        self.main_sizer.Add(top_sizer, 0, wx.LEFT
                                        | wx.RIGHT, 8)
        #self.main_sizer.Add((0,2))
        self.main_sizer.Add(self.lists["updates"], 4, wx.LEFT
                                                    | wx.RIGHT
                                                    | wx.ALIGN_CENTER
                                                    | wx.EXPAND, 8)
        self.main_sizer.Add(self.middle_sizer, 0,
                                                      wx.ALIGN_LEFT
                                                    | wx.EXPAND
                                                    | wx.LEFT
                                                    | wx.RIGHT
                                                    | wx.TOP
                                                    | wx.BOTTOM, 5)
        self.main_sizer.Add(self.lists["new"], 4,
                                                      wx.LEFT
                                                    | wx.RIGHT
                                                    | wx.ALIGN_CENTER
                                                    | wx.EXPAND, 8)
        if self.add_on_exists:
            self.main_sizer.Add((0,8))
        self.main_sizer.Add(self.desc_html, 7,
                                                      wx.LEFT
                                                    | wx.RIGHT
                                                    | wx.ALIGN_CENTER
                                                    | wx.EXPAND, 8)
        self.main_sizer.Add((0,8))
        self.main_sizer.Add(self.license_sizer, 0,
                                                      wx.LEFT
                                                    | wx.RIGHT
                                                    | wx.BOTTOM
                                                    | wx.EXPAND, 8)
        self.main_sizer.Add(self.bottom_sizer, 0,
                                                      wx.LEFT
                                                    | wx.RIGHT
                                                    | wx.EXPAND, 8)
        self.main_sizer.Add((0,8))

        self.panel.SetSizer(self.main_sizer)
        self.main_sizer.Fit(self)

        self.set_frame_size(self.add_on_exists)
        #self.SetMinSize((420, 500))

        self.Layout()
        self.Centre()

        # When the tool is initialized ensure it initially has keyboard
        # focus so that a mouseless user can begin interacting with the
        # tool prior to the update check completing (for the standalone
        # version).
        self.close_btn.SetFocus()

        self.load_ad_page()

        if self.standalone:
            wx.CallAfter(self.populate_update_list, self.image_list)
        else:
            wx.CallAfter(self.update_lists, self.image_list, self.add_on_exists)


    def OnLicNavigationKey(self, event):
        '''
        The HyperLinkCtrl does not indicate it has the focus thus during
        mouseless operations we need to provide some indication that the
        control has the focus.  We do so by changing the color of the text.
        While this is not ideal for the colorblind it is at least an
        improvement over the current behavior.
        '''

        # On Windows GetCurrentFocus() always returns None but FindFocus()
        # appears to work.
        #focus_window = event.GetCurrentFocus()
        focus_window = self.license_checkbox.FindFocus()

        if focus_window == self.license_checkbox or \
           focus_window == self.app_center_btn:
            self.license_link.SetNormalColour(self.license_link.GetHoverColour())
            self.license_link.SetFocus()
            return
        elif focus_window == self.license_link:
            self.license_link.SetNormalColour(self.license_link_normal_color)

        event.Skip()


    def OnUpdateListKeyUp(self, event):
        self.OnListKeyUp(event, self.lists["updates"])


    def OnNewListKeyUp(self, event):
        self.OnListKeyUp(event, self.lists["new"])


    def OnListKeyUp(self, event, list):
        '''
        This is a workaround for issue 1446.  We intercept the SPACE key
        press and select the first item if no items are already selected.
        This avoids the infinite loop that occasionally happens on Windows.
        This event handler is only established on Windows.
        '''

        if event.GetKeyCode() == wx.WXK_SPACE:
            if list.GetItemCount() == 0:
                # Ignore SPACE presses when no items are in the list.
                return
            elif list.GetSelectedItemCount() != 0:
                # Process SPACE presses normally when selected items are
                # in the list.
                event.Skip()
                return
            else:
                # Intercept SPACE presses when items are in the list but
                # are not selected.
                list.SetItemState(0, wx.LIST_STATE_SELECTED,
                                                      wx.LIST_STATE_SELECTED)
                list.SetItemState(0, wx.LIST_STATE_FOCUSED,
                                                      wx.LIST_STATE_FOCUSED)
                return

        event.Skip()


    def raise_frame(self):
        self.Raise()
        self.Restore()
        # If the "Check For Updates" button is enabled then it is safe
        # to run the update check.
        if self.refresh_btn.IsEnabled():
            self._check_for_updates()


    def OnToggle(self, event):
        if self.hidden:
            self.SetSize((520, 680))
            #self.main_sizer.Add((0,8))
            self.main_sizer.Insert(4, (0,8))
            self.lists["new"].Show(True)
            self.hidden = False
        else:
            self.lists["new"].Show(False)
            self.main_sizer.Remove(4)
            self.SetSize((520, 538))
            self.hidden = True
        self.main_sizer.Layout()


    def OnClose(self, event):

        # XXX: Need to handle the new software/add-ons thread too!

        # If the img_count is greater then 0 then there still are active
        # threads.  We need to abort the remaining threads.
        if self.img_count > 0:

            # Disable the buttons
            self._set_button_state(BTNS_CLOSING)

            self.Unbind(listers.EVT_LISTING_COMPONENT)
            self.status.set_status(_("Aborting update checks..."))

            self._abort_threads()

        self.Hide()

        # This tells the invoking party that the dialog has been closed.
        if self.on_close_func != None:
            self.on_close_func(restart_check=False)

        self.Destroy()


    def OnClick(self, event):
        if event.GetId() == ID_VAR_BTN:

            # If the Stop button is displayed...
            if self.button_is_stop:

                # If the img_count is greater then 0 then the user pressed the
                # Stop button and we need to abort the remaining threads.
                if self.img_count > 0:
                    self._set_button_state(BTNS_STOPPING)
                    self.Unbind(listers.EVT_LISTING_COMPONENT)
                    wx.YieldIfNeeded()
                    self.status.set_status(_("Aborting update checks..."))
                    self._abort_threads()

                # We stopped so we are no longer waiting on any threads
                # to complete their update check.
                self.img_count = 0

                self.status.throb(False)
                self.status.set_status("")
                if self._lists_have_item():
                    self.top_bold_stt.SetLabel(TEXT_NEW_SW_AVAILABLE)
                    self.top_stt.SetLabel(TEXT_UPDATES_AVAILABLE)
                else:
                    self.top_bold_stt.SetLabel(" ")
                    self.top_stt.SetLabel(TEXT_NO_UPDATES_FOUND)

                # Some items may have been put in the list.  Update the
                # Install button state.
                self._update_var_btn_label()
                self._set_button_state(BTNS_STOPPED)
                self._manage_keyboard_focus()

                self._update_check_end(None)


            elif not self.button_is_stop and self.license_accepted:
                self.busy = True
                tracker_task = MultiImageTask()

                # Generate a list of images selected in the list.
                selected_imgs = self._gen_selected_list(self.image_list)

                tracker_task.set_image_list(selected_imgs, self.image_list)

                dlg = InstallDialog(self, -1,
                      _("%(APP_NAME)s: Install") % {'APP_NAME':APP_LONG_NAME},
                      task=tracker_task,
                      frame=self)
                dlg.set_image_list(selected_imgs, self.image_list)
                tracker_task.set_progress_dialog(dlg)
                tracker_task.start()

                dlg.ShowModal()

                # After the dialog is dismissed we must update the main
                # update list since some images may have been updated.
                self._update_image_list(selected_imgs)
                self.regenerate_ui_lists()
                self._update_var_btn_label()
                self._set_button_state(BTNS_INSTALL)
                self._manage_keyboard_focus()

                self.license_checkbox.SetValue(False)
                self.license_accepted = False
                # Tell the GUI to check to see if it needs to restart
                ipcservice.send_command("ut_lock", "RESTART_CHECK")

                # Reload the ad
                self.load_ad_page()

                # This tells the notifier to update its' list of updates.
                if self.update_notifier_func != None:
                    self._update_check_end(self.image_list)
                else:
                    if dlg.GetReturnCode() > 0:
                        # The notifier is a separate process
                        ipcservice.send_command("nt_lock", "RESTART_CHECK")

                dlg.Destroy()
                self.busy = False
                return
            else:
                self.busy = True
                msg = _("Please accept the license terms prior to installing the software.")
                dlg = wx.MessageDialog(self, msg,
                                             _("License Agreement Required"),
                                             wx.OK | wx.ICON_EXCLAMATION |
                                             wx.STAY_ON_TOP)
                dlg.ShowModal()
                dlg.Destroy()
                self.busy = False
        elif event.GetId() == ID_APP_CENTER:
            # Start the GUI

            image_path = ips.get_python_image_path()
            utils.logger.debug("image path to launch GUI: " + image_path)

            # If the image_path is empty then we are running from the workspace
            # so we will use the tool-path option.
            alternate_path = None
            if image_path == "":
                alternate_path = self.options["tool_path"]

            return_code, msg = start_gui(image_path, alt_path=alternate_path)
            if return_code:
                error_msg = _("Unable to start application.\n%s" % msg)
                dlg = wx.MessageDialog(self, error_msg,
                                        caption=_("%(APP_NAME)s: Error") % \
                                                     {'APP_NAME':APP_LONG_NAME},
                                        style=wx.OK | wx.ICON_ERROR |
                                        wx.STAY_ON_TOP)
                dlg.ShowModal()
                dlg.Destroy()
        elif event.GetId() == wx.ID_REFRESH:
            # When the Refresh button is pressed it is disabled.  This causes
            # the focus to be lost.
            self.lists["updates"].SetFocus()
            # Recheck for updates
            self._check_for_updates()
        else:
            print "Not implemented."


    def OnLicenseLinkKeyEvent(self, event):
         # The Hyperlink Control is not responding to mouseless keyboard
         # events so we catch the spacebar and trigger the LicenseDialog
         # display.
         if event.GetKeyCode() == wx.WXK_SPACE:
             evnt = wx.HyperlinkEvent(self.license_link, -1, "")
             wx.PostEvent(self.license_link, evnt)
             return

         event.Skip()


    def OnLicenseView(self, event):
         self.busy = True
         wx.BeginBusyCursor()
         self.license_link.SetVisited(False)
         lic_list, img_details, reason = LD.generate_license_list(self.image_list)
         if lic_list is None:
             wx.EndBusyCursor()
             error_msg = _("Error retrieving license for '%(TITLE)s'.\n\n" %
                                 {'TITLE':img_details['title']})
             error_msg += _("The following error occurred:\n")
             error_msg += reason
             utils.logger.error(error_msg)
             utils.logger.error("Image location: " + img_details['imgroot'])

             wx.MessageBox(error_msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                           caption=_("%(APP_NAME)s: License Retrieval Error") %
                                     {'APP_NAME':APP_LONG_NAME},
                           parent=self)
             self.busy = False
             return

         dlg = LD.LicenseDialog(self, -1,
                                     _("%(APP_NAME)s: License Agreement(s)") %
                                                     {'APP_NAME':APP_LONG_NAME},
                                     lic_list=lic_list)
         wx.EndBusyCursor()
         dlg.ShowModal()
         dlg.Destroy()

         if dlg.lic_accepted:
             self.license_checkbox.SetValue(True)
             self.license_accepted = True
         self.busy = False


    # This is called whenever an update list checkbox item is
    # selected/deselected
    def OnUpdateListCheckItem(self, index, flag):
        # During mouseless operations if there is only one item in the
        # list there is no way to select that item using the arrow buttons
        # or any other buttons.   So if the user checks the item in the
        # list and there are currently no items selected in the list then
        # we select that item.  Issue 1575
        if wx.Platform != "__WXMSW__" and \
           self.lists["updates"].GetSelectedItemCount() == 0:
            self.lists["updates"].SetItemState(index, wx.LIST_STATE_SELECTED,
                                                      wx.LIST_STATE_SELECTED)
            self.lists["updates"].SetItemState(index, wx.LIST_STATE_FOCUSED,
                                                      wx.LIST_STATE_FOCUSED)

        self.lists["updates"].old_OnCheckItem(index, flag)
        # Ignore checked item notification until we have checked for
        # new updates in all threads.
        if self.img_count == 0:
            self._set_button_state(BTNS_INSTALL)

        # Record the state of the check box.  Needed when we regenerate the
        # list after the user updates a subset of the images.
        list = self.lists["updates"]
        img_details = self.image_list[list.get_fmri(index)]
        img_details['checked'] = flag

        # If they add a new item they must accept the lic terms again.
        if flag:
            self.license_checkbox.SetValue(False)
            self.license_accepted = False


    # This is called whenever a new list checkbox item is selected/deselected
    def OnNewListCheckItem(self, index, flag):

        self.lists["new"].old_OnCheckItem(index, flag)

        # During mouseless operations if there is only one item in the
        # list there is no way to select that item using the arrow buttons
        # or any other buttons.   So if the user checks the item in the
        # list and there are currently no items selected in the list then
        # we select that item.  Issue 1575
        if wx.Platform != "__WXMSW__" and \
           self.lists["new"].GetSelectedItemCount() == 0:
            self.lists["new"].SetItemState(index, wx.LIST_STATE_SELECTED,
                                                  wx.LIST_STATE_SELECTED)
            self.lists["new"].SetItemState(index, wx.LIST_STATE_FOCUSED,
                                                  wx.LIST_STATE_FOCUSED)

        # Item is being checked.
        img_details = self.image_list[self.lists['new'].get_fmri(index)]

        if img_details['type'] == CONST.T_NEW_IMAGE:
            self._handle_newsw_selection(index, img_details, flag)
        elif img_details['type'] == CONST.T_ADD_ON:
            self._handle_addon_selection(index, img_details, flag)

        # Ignore checked item notification until we have checked for
        # new updates in all threads.
        if self.img_count == 0:
            self._set_button_state(BTNS_INSTALL)


    def _handle_addon_selection(self, index, img_details, flag):
        # If the check box is selected and there are more than one image
        # in which the add-on can be applied to we must ask the user to
        # confirm which images to apply the add-on to.
        if flag:
            # Item is being checked.
            add_on_image_list = img_details['add_on_image_list']

            if len(add_on_image_list) == 1:
                add_on_image_list[0]['selected'] = True
                img_details['checked'] = True
            else:
                choice_list = []
                select_list = []
                selected_index = 0

                for img_data in add_on_image_list:
                    img_root = self.image_list[img_data['id']]['imgroot']
                    img_title = ips.get_image_title(fsenc(img_root))

                    choice_list.append("%s (%s)" % (img_title, img_root))

                    if img_data['selected']:
                        select_list.append(selected_index)
                    selected_index += 1

                # If nothing is selected then select them all
                if len(select_list) == 0:
                    select_list = range(len(choice_list))
                    entry = img_details['feed_entry']
                if entry.has_key(BF.TITLE):
                    title = "%s" % (entry[BF.TITLE])
                else:
                    title = _("%s: Untitled Add-On") % (APP_LONG_NAME )

                text = _("This Add-On can be applied to more than one application image.\n")
                text += _("Please confirm the application images the Add-On will be applied to:")

                dlg = wx.MultiChoiceDialog(self, text, title, choice_list)

                dlg.SetSelections(select_list)

                if (dlg.ShowModal() == wx.ID_OK):
                    selections = dlg.GetSelections()
                    # No items selected so unselect the list item
                    if len(selections) == 0:
                        self.lists["new"].CheckItem(index, False)
                        for img_data in add_on_image_list:
                            img_data['selected'] = False
                        img_details['checked'] = False
                    else:
                        for img_data in add_on_image_list:
                            img_data['selected'] = False
                        for item in selections:
                            add_on_image_list[item]['selected'] = True
                        img_details['checked'] = True
                else:
                    # They cancalled the dialog so unselect the list item
                    self.lists["new"].CheckItem(index, False)
                    img_details['checked'] = False

            # If they add a new item they must accept the lic terms again.
            if flag:
                self.license_checkbox.SetValue(False)
                self.license_accepted = False
        else:
            # They unchecked the box so unselect the items.
            add_on_image_list = img_details['add_on_image_list']
            for img_data in add_on_image_list:
                img_data['selected'] = False
            img_details['checked'] = False


    def _handle_newsw_selection(self, index, img_details, flag):
        if flag:
            from dialogs.imagecreateeditdialog import ImageCreateEditDialog
            img_details['checked'] = True

            dlg = ImageCreateEditDialog(self, opname='image-create',
                                                           install=True,
                                                           newsw_install = True)
            self._populate_new_image_dialog(dlg, img_details)

            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                # User did not select an image directory
                img_details['checked'] = False
                self.lists["new"].CheckItem(index, False)
                return None

            img_details['imgroot'] = dlg.get_directory()
            img_details['title'] = dlg.get_image_title()
            img_details['description'] = dlg.get_image_description()
            img_details['publishers'] = dlg.get_pubs()
        else:
            img_details['checked'] = False


    def OnLicenseCheck(self, event):
        self.license_accepted = event.IsChecked()


    def _populate_new_image_dialog(self, dlg, img_details):
        # When new sw is selected to be installed we display a dialog
        # to allow the user to modify the default installation choices.

        # If the title has been set then the dialog as already been displayed
        # for this image so we reuse the prior contents.  Otherwise we use
        # the defaults from the feed entry.
        if img_details['title'] != "":
            dlg.set_image_title(img_details['title'])
            dlg.set_image_description(img_details['description'])
            dlg.set_pubs(img_details['publishers'])
            dlg.set_path(img_details['imgroot'], focus=True)
        else:
            entry = img_details['feed_entry']

            dlg.set_image_title(entry[BF.TITLE])
            dlg.set_image_description(entry[BF.TITLE])

            pubs = [ ( a[BF.NAME], a[BF.ORIGIN], a[BF.PREFERRED], None,
                     None, a[BF.DISABLED] ) for a in entry[BF.PUBLISHERS] ]
            dlg.set_pubs(pubs)

            # Set a default installation path
            installpath = entry[BF.INSTALL_PATH]
            if installpath is not None and len(installpath) > 0:
                installpath = utils.expand_path_tokens(installpath)
            else:
                installpath = ""

            dlg.set_path(installpath, focus=True)


    def _manage_keyboard_focus(self):

        no_items = False
        # Determine if there are any checked items in the lists.
        if not self._list_has_checked_item(self.lists["updates"]):
            if not self._list_has_checked_item(self.lists["new"]):
                no_items = True

        if no_items:
            self.close_btn.SetFocus()
        else:
            self.lists["updates"].SetFocus()

        #print "focus", wx.Window_FindFocus().GetLabel()


    def _check_for_updates(self):
        # Check for updates and new add-ons

        self.top_stt.SetLabel(" ")
        self.top_bold_stt.SetLabel(" ")

        self.lists["updates"].DeleteAllItems()
        self.lists["new"].DeleteAllItems()

        self._manage_security_emblem(False)

        if self.config:
            self.config.load_config()
            utils.set_net_proxy(self.config)

        self._set_button_state(BTNS_CHECKING)

        # Reload the ad
        self.load_ad_page()

        # Reload our list of images from the config file.
        self.image_list = self.load_images_list()

        # Note: process_update_queue() kicks off an add-on check once the
        # update check is complete.
        wx.CallAfter(self.populate_update_list, self.image_list)


    def reload_config(self):
        """
        If the pref's are updated via the notifier prefs dialog the GUI is
        sent a LOAD_CONFIG IPC message.  This method is called to respond
        to the reload request.
        """
        if self.config:
            self.config.load_config()
            utils.set_net_proxy(self.config)


    def _update_var_btn_label(self):

        self.button_is_stop = False

        self.var_btn.SetLabel(_("Install"))
        self.var_btn.SetToolTipString(_("Update/Install selected items"))


    def _build_license_area(self):
        license_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.license_checkbox = wx.CheckBox(self.panel, -1,
                                               _("I accept the "))
        self.license_checkbox.SetToolTipString(
                       _("Check this item to accept the license agreements. "))
        self.license_checkbox.Bind(wx.EVT_NAVIGATION_KEY, self.OnLicNavigationKey)
        self.Bind(wx.EVT_CHECKBOX, self.OnLicenseCheck, self.license_checkbox)

        self.license_link = wx.HyperlinkCtrl(self.panel, -1,
                            style=wx.HL_ALIGN_LEFT|wx.NO_BORDER,
                            label=_("license terms"), url="")
        self.license_link.Bind(wx.EVT_NAVIGATION_KEY, self.OnLicNavigationKey)
        self.license_link_normal_color = self.license_link.GetNormalColour()
        #XXX On Windows may want to use 161,161,146?
        self.license_link_disabled_color = wx.Colour(117,117,117)
        self.license_link.SetNormalColour(self.license_link_disabled_color)
        self.license_link.SetToolTipString(
                       _("View software license agreements for selected items"))
        self.license_link.Bind(wx.EVT_HYPERLINK, self.OnLicenseView)
        self.license_link.Bind(wx.EVT_KEY_DOWN, self.OnLicenseLinkKeyEvent)

        #license_sizer.Add(self.license_btn, 0, wx.LEFT
        #                                     | wx.RIGHT
        #                                     | wx.ALIGN_LEFT, 0)
        license_sizer.Add((1,1), 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 4)
        license_sizer.Add(self.license_checkbox, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER, 0)
        license_sizer.Add(self.license_link, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER, 0)
        self.license_checkbox.Disable()
        self.license_link.Disable()
        #self.license_btn.Disable()

        return license_sizer


    def _build_bottom_buttons(self):

        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.app_center_btn = wx.Button(self.panel, ID_APP_CENTER,
                                                           _("Manage Details"))
        self.app_center_btn.Bind(wx.EVT_NAVIGATION_KEY, self.OnLicNavigationKey)
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.app_center_btn)
        self.app_center_btn.SetToolTipString(_("Start Update Tool to view and manage product and component level update details"))

        bottom_sizer.Add(self.app_center_btn, 0, wx.RIGHT | wx.ALIGN_LEFT, 4)
        bottom_sizer.Add((1,1), 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 4)

        #self.test_btn = wx.Button(self.panel, -1, _("Toggle List "))
        #self.Bind(wx.EVT_BUTTON, self.OnToggle, self.test_btn)
        #self.hidden = True

        #bottom_sizer.Add(self.test_btn, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_RIGHT, 4)

        self.close_btn = wx.Button(self.panel, ID_CLOSE, _("Close"))
        self.Bind(wx.EVT_BUTTON, self.OnClose, self.close_btn)
        self.close_btn.SetToolTipString(_("Close"))

        bottom_sizer.Add(self.close_btn, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_RIGHT, 4)

        self.var_btn = wx.Button(self.panel, ID_VAR_BTN, _("Stop"))
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.var_btn)
        self.var_btn.SetToolTipString(_("Stop searching for updates in known application images"))
        #self.var_btn.SetDefault()
        self.button_is_stop = True

        bottom_sizer.Add(self.var_btn, 0, wx.LEFT | wx.ALIGN_RIGHT, 4)

        return bottom_sizer


    def _init_list_ctrl(self, columns=None, size_col=-1, sort_col=1, update_list_type=True):

        num_columns = len(columns)

        if update_list_type:
            list_ctrl = UpdatesCheckListCtrl(self.panel, -1,
                                                num_cols=num_columns,
                                                size_column=size_col,
                                                default_sort_column=sort_col)
        else:
            list_ctrl = CheckListCtrl(self.panel, -1,
                                                num_cols=num_columns,
                                                size_column=size_col,
                                                default_sort_column=sort_col)
        col_info = wx.ListItem()
        col_info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT | wx.LIST_MASK_WIDTH
        for index, col in enumerate(columns):
            col_info.m_text = col[0]
            col_info.m_width = col[1]
            col_info.m_format = col[2]
            list_ctrl.InsertColumnInfo(index, col_info)
            # On Windows wx.LIST_AUTOSIZE_USEHEADER seems to be ignored if
            # if it is set via InsertColumnInfo.
            if col[1] ==  wx.LIST_AUTOSIZE_USEHEADER:
                list_ctrl.SetColumnWidth(index, wx.LIST_AUTOSIZE_USEHEADER)

        list_ctrl.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, list_ctrl)
        list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListItemSelected, list_ctrl)

        list_ctrl.old_OnSortOrderChanged = list_ctrl.OnSortOrderChanged
        list_ctrl.OnSortOrderChanged = self.OnSortOrderChangedUpdate

        return list_ctrl


    def OnSortOrderChangedUpdate(self):
        # HACK : Till we figure out proper threading
        if isinstance(self.lists["updates"], wx.ListCtrl):
            #self.lists.["updates"]._prev_update_sort_flag = self.lists["updates"].get_sort_flag(self._sort_col)
            self.lists["updates"].old_OnSortOrderChanged()


    def OnColClick(self, evt):
        self.lists["updates"]._sort_col = evt.GetColumn()
        evt.Skip()


    def OnListItemSelected(self, evt):

        # We are managing two lists.  Allow only one item between the two
        # lists to be selected at any time.
        list = evt.GetEventObject()
        if list == self.lists["updates"]:
            selected = self.lists["new"].GetFirstSelected()
            if selected >= 0:
                self.lists["new"].Select(selected, 0)
        else:
            selected = self.lists["updates"].GetFirstSelected()
            if selected >= 0:
                self.lists["updates"].Select(selected, 0)

        # XXX: We are overloading view_fmris to hold the image_list id
        # of the image_details.
        #    When we put an item on the list (append_data_row) we set
        #    fmri=id.  This is stored in list.view_fmris[list row #].  This
        #    id is the img_details['id'] that was passed to the
        #    UpdatesListerThread (stored as _uid).  When the Lister calls
        #    us back it included this _uid in the event.
        self._update_desc_pane(list, list.get_fmri(evt.m_itemIndex))
        evt.Skip()


    def OnListingEvent(self, event):

        a, b = event.value

        #id = event.GetId()

        if a == listers.LISTING_DATA:
            self.update_queue.put(event)
        elif a == listers.LISTING_INFORMATION:
            pass
        elif a in [listers.LISTING_WARNING,
                   listers.LISTING_ERROR,
                   listers.LISTING_LONG_ERROR,
                   listers.LISTING_SUCCESS]:
            self.update_queue.put(event)
            wx.CallAfter(self.process_update_queue)
        else:
            utils.logger.error("Unknown type sent as Update ListingEvent: %s.",
                                                                        str(a))
        wx.YieldIfNeeded()


    def OnNewSWListingEvent(self, event):

        a, b = event.value

        #id = event.GetId()

        if a == listers.LISTING_DATA:
            self.newsw_queue.put(event)
        elif a == listers.LISTING_INFORMATION:
            pass
        elif a in [listers.LISTING_WARNING,
                   listers.LISTING_ERROR,
                   listers.LISTING_LONG_ERROR,
                   listers.LISTING_SUCCESS]:
            self.newsw_queue.put(event)
            wx.CallAfter(self.process_newsw_queue)
        else:
            utils.logger.error("Unknown type sent as Add-on ListingEvent: %s.",
                                                                        str(a))
        wx.YieldIfNeeded()


    def _perform_addon_check(self):

        if not self.options["enable_feature_feed"]: 
            return

        # The following prevents a second addon_check starting before
        # the current check completes.
        if self.addon_check_lock:
            utils.logger.warning("New software check aborted.  Existing check has not completed.")
            return
        else:
            self.addon_check_lock = True

        # Atom feed for New Software and Add-ons list
        featured_feed_url = self.config.get('main', 'featured.feed.url')
        if featured_feed_url is not None and len(featured_feed_url) > 0:
            basicfeed = BasicFeed(url=featured_feed_url)
            #basicfeed.set_debug_delay(2)
            basicfeed.parse(self.featured_feed_callback)
        else:
            self.addon_check_lock = False


    def featured_feed_callback(self, basicfeed):
        '''
        After the featured software Atom feed is loaded we are called
        with the feed
        '''

        try:
            feeddata = basicfeed.get_feed()
            # Split feed into lists of apps and addons
            (apps, addons) = split_feed(feeddata)

        except Exception, e:
            utils.logger.info("Unable to get featured software feed %s: %s",
                              basicfeed.get_url(), e)
            utils.logger.debug(utils.format_trace())
            self.addon_check_lock = False
            return

        try:
            # Load feed into the list
            self.lists["new"].Bind(listers.EVT_LISTING_COMPONENT,
                                                      self.OnNewSWListingEvent)

            img_list = [img_details['imgroot'] for img_details in self.image_list.itervalues() if img_details['type'] == CONST.T_NORMAL]

            if img_list:
                lockmanager.lock()
                lockmanager.flag_running("unused lock", views.UPDATES)
                lockmanager.release()

                global_settings.client_name = APP_CLIENT_NAME
                self.lists["new"].set_updating(True)

                # The results on the UpdatesListerThread's work is placed on the
                # XXX_queue.
                self.not_used = listers.NewSWListerThread(parent=self.lists["new"],
                                            uid=12356,
                                            imagedir="unused lock",
                                            max_recent=1,
                                            image_list=img_list,
                                            feed_addon_entries=addons,
                                            feed_newsw_entries=apps)
            else:
                self.addon_check_lock = False
        except Exception, e:
            utils.logger.warning("Unable to load feed %s into UI: %s",
                              basicfeed.get_url(), e)
            utils.logger.debug(utils.format_trace())
            self.addon_check_lock = False
            return


    def process_newsw_queue(self):

        # The AddOnsListerThread puts the results of the work in the
        # newsw_queue.  This method drains from the queue.
        while not self.newsw_queue.empty():
            event = self.newsw_queue.get()
            type, entry_data = event.value

            if type == listers.LISTING_DATA:
                # Since we found an add-on we need to display the add-on
                # list (it may not be currently shown: issue 1605)
                self._show_add_on_list()

                addon_entry_dict = entry_data['addon_dict']

                for entry in addon_entry_dict.itervalues():
                    self._process_addon_entry(entry)

                newsw_list = entry_data['newsw_list']

                for entry in newsw_list:
                    self._process_newsw_entry(entry)

            elif type == listers.LISTING_SUCCESS:
                self.lists["new"].set_updating(False)
                self.addon_check_lock = False
            elif type == listers.LISTING_ERROR or \
                 type == listers.LISTING_LONG_ERROR:
                # XXX: Currently the AddOnsListerThread will not generate
                #      any of these events.
                self.lists["new"].set_updating(False)
                self.addon_check_lock = False
            else:
                print "XXX: unknown type: " + str(type)

        if self._lists_have_item():
            self.top_bold_stt.SetLabel(TEXT_NEW_SW_AVAILABLE)
            self.top_stt.SetLabel(TEXT_UPDATES_AVAILABLE)
        else:
            self.top_bold_stt.SetLabel(" ")
            self.top_stt.SetLabel(TEXT_NO_UPDATES_AVAILABLE)

        # Only set to Install if there are items to install.
        self._update_var_btn_label()
        self._set_button_state(BTNS_INSTALL)


    def _process_addon_entry(self, entry):

        add_on_image_list = []
        id = self.image_list_count

        assert not self.image_list.has_key(id), \
                           "process_newsw_queue: ID already in use: " + str(id)

        img_details = self._initialize_img_details(id, CONST.T_ADD_ON, "",
                                                 feed_entry=entry['feed_entry'])

        for img in entry['image_list']:
            add_on_images = {}
            add_on_images['id'] = self.get_id_from_image(img)
            add_on_images['selected'] = False

            add_on_image_list.append(add_on_images)

        img_details['add_on_image_list'] = add_on_image_list

        feed_entry=entry['feed_entry']
        if feed_entry.has_key(BF.SIZE) and \
                                   utils.is_integer_string(feed_entry[BF.SIZE]):
            img_details['size'] = int(feed_entry[BF.SIZE]) * 1024
        else:
            img_details['size'] = 0

        self.image_list[id] = img_details
        self.image_list_count += 1

        itemCols = self.prepare_addon_list_cols(id)
        #XXX fmri=id - use more generic option (not fmri)
        self.lists["new"].append_data_row(fmri=id, size=0, items=itemCols)


    def _process_newsw_entry(self, entry):

        # We only handle pkg(5) based images.
        if entry[BF.APP_TYPE] != 'pkg':
            return

        id = self.image_list_count

        assert not self.image_list.has_key(id), \
                           "process_newsw_queue: ID already in use: " + str(id)

        img_details = self._initialize_img_details(id, CONST.T_NEW_IMAGE, "",
                                                              feed_entry=entry)

        if entry.has_key(BF.SIZE) and \
                                   utils.is_integer_string(entry[BF.SIZE]):
            img_details['size'] = int(entry[BF.SIZE]) * 1024
        else:
            img_details['size'] = 0

        self.image_list[id] = img_details
        self.image_list_count += 1

        itemCols = self.prepare_addon_list_cols(id)
        #XXX fmri=id - use more generic option (not fmri)
        self.lists["new"].append_data_row(fmri=id, size=0, items=itemCols)


    def _update_desc_pane(self, list, selected_item):

        # XXX: On SPARC if you arrow up/down quickly in the list this
        # callback may be reentered.  self.desc_html.SetPage() will not
        # have returned.  This tends to cause the tool to crash.

        # Allow scrollbars to appear in window.
        if self.ad_displayed:
            self.desc_html.SetVirtualSizeHintsSz((395, 10), maxSize=(495, -1))
            self.main_sizer.Layout()
            self.ad_displayed = False

        if list == self.lists["updates"]:
            img_details = self.image_list[selected_item]
            self.desc_html.SetPage(
                        self._construct_update_html(img_details, selected_item))
        else: # New SW list
            img_details = self.image_list[selected_item]
            self.desc_html.SetPage(self._construct_newsw_html(img_details))

        list.SetFocus()


    def load_images_list(self):

        self.image_list_count = 0

        img_list_dict = {}

        if not self.config.has_option('main', 'image_list'):
            return img_list_dict

        for path in utils.to_unicode(self.config.get('main', 'image_list')).splitlines():
            directory = path.strip()

            if os.path.exists(fsenc(directory)):
                imgroot = ips.get_user_image_rootdir(fsenc(directory))
                if not imgroot:
                    utils.logger.warning("Not a valid image: %s", directory)
                    continue
                imgroot = fileutils.canonical_path(imgroot)
                img_list_dict[self.image_list_count] = \
                        self._initialize_img_details(
                                           self.image_list_count,
                                           CONST.T_NORMAL,
                                           imgroot)
                self.image_list_count += 1

        return img_list_dict


    def _initialize_img_details(self, id, type, imgroot, feed_entry = None):

        img_details = {}
        img_details['id'] = id
        img_details['type'] = type
        img_details['imgroot'] = fsdec(imgroot)
        img_details['size'] = 0
        img_details['security'] = False
        img_details['pkgs'] = []
        img_details['log'] = []
        img_details['checked'] = False
        img_details['installed'] = False
        img_details['imageplan'] = None
        img_details['feed_entry'] = feed_entry
        img_details['title'] = ""
        img_details['description'] = ""
        img_details['publishers'] = []
        img_details['add_on_image_list'] = []

        return img_details


    # Generate a list of images selected in the list.
    def _gen_selected_list(self, image_list):

        selected_list = []

        for img_details in self.image_list.itervalues():
            if not img_details['checked']:
                continue

            if img_details['type'] == CONST.T_NORMAL:
                selected_list.append(img_details)

            # Since the add on items may need to apply to more than one
            # image we create new image_detail items for each of those
            # target images which the user has selected.
            elif img_details['type'] == CONST.T_ADD_ON:
                # Items with an id < 0 are to be ignored.  They have already
                # been applied.
                if img_details['id'] < 0:
                    continue

                n = (img_details['id'] + 1) * 10000
                count = 0
                do_count = False

                # We need to know how many times this add-on will be installed
                # so that we can properly indicate that in the install dialog.
                if len([item for item in img_details['add_on_image_list'] if item['selected']]) > 1:
                    do_count = True

                for item in img_details['add_on_image_list']:
                    if not item['selected']:
                        continue

                    if count > 0:
                        primary_id = n
                    else:
                        primary_id = img_details['id']

                    if do_count:
                        count += 1

                    selected_list.append(
                                 self._copy_img_details(img_details,
                                                        primary_id,
                                                        item['id'],
                                                        count))
                    n += 1
            elif img_details['type'] == CONST.T_NEW_IMAGE:
                # Items with an id < 0 are to be ignored.  They have already
                # been applied.
                if img_details['id'] < 0:
                    continue

                selected_list.append(img_details)

        return selected_list


    def _copy_img_details(self, img_details, id, target_id, count):

        new_img_d = self._initialize_img_details(id,
                                                 img_details['type'],
                                                 img_details['imgroot'],
                                                 img_details['feed_entry'])
        new_img_d['id'] = id
        new_img_d['size'] = img_details['size']
        new_img_d['security'] = img_details['security']
        new_img_d['pkgs'] = img_details['pkgs']
        new_img_d['log'] = img_details['log']
        new_img_d['checked'] = img_details['checked']
        new_img_d['installed'] = img_details['installed']
        new_img_d['imageplan'] = None
        new_img_d['feed_entry'] = img_details['feed_entry']
        new_img_d['title'] = img_details['title']
        new_img_d['description'] = img_details['description']
        new_img_d['publishers'] = img_details['publishers']

        target_img = {}
        target_img['id'] = target_id
        target_img['selected'] = True
        target_img['sequence'] = count

        new_img_d['add_on_image_list'] = [target_img]

        return new_img_d


    def _update_image_list(self, selected_list):

        image_list_str = u""

        # Synch the existing image_list to the selected_list.
        # For images that are updated successfully we clear the pkgs list
        # which means they have nothing to update.
        # For add-ons we ...
        for img in selected_list:
            if img['installed']:
                if img['type'] == CONST.T_NORMAL:
                    self.image_list[img['id']]['pkgs'] = []
                    self.image_list[img['id']]['checked'] = False
                elif img['type'] == CONST.T_ADD_ON:
                    if img['id'] > 10000:
                        orig_id = img['id']/10000 - 1
                    else:
                        orig_id = img['id']
                    # If there is only one image in the add-on list then we
                    # can mark (to ignore) this item in the image list.
                    if len(self.image_list[orig_id]['add_on_image_list']) == 1:
                        self.image_list[orig_id]['id'] = -1
                    else:
                        self._update_add_on_image_list(orig_id,
                                                    img['add_on_image_list'][0])
                elif img['type'] == CONST.T_NEW_IMAGE:
                    if img['id'] > 10000:
                        orig_id = img['id']/10000 - 1
                    else:
                        orig_id = img['id']
                    self.image_list[orig_id]['id'] = -1

                    image_list_str = image_list_str + img['imgroot'] + u"\n"

        # If we added a new image or two we must update the defaults.cfg
        if image_list_str != u"":
            self.reload_config()
            if self.config.has_option('main', 'image_list'):
                for path in utils.to_unicode(
                            self.config.get('main', 'image_list')).splitlines():
                    directory = path.strip()

                    if os.path.exists(fsenc(directory)):
                        image_list_str = image_list_str + directory + u"\n"

            self.config.set("main", "image_list", image_list_str.encode('utf8'))
            self.config.save_config()
            # Inform both the notifier and the GUI that the image list has
            # been modified.
            # XXX: For the GUI we really need to tell it to update the image
            #      tree.
            ipcservice.send_command("ut_lock", "LOAD_CONFIG")
            ipcservice.send_command("nt_lock", "LOAD_CONFIG")


    def _update_add_on_image_list(self, img_id, add_on_image_item):

        target_id = add_on_image_item['id']

        # For this image_list item update its add_on_image_list be removing
        # the installed item.
        new_add_on_image_list = \
                    [item \
                       for item in self.image_list[img_id]['add_on_image_list']\
                          if item['id'] != target_id]

        # If the list is empty mark (to ignore) this item in the image list.
        if len(new_add_on_image_list) == 0:
            self.image_list[img_id]['id'] = -1
        else:
            self.image_list[img_id]['add_on_image_list'] = new_add_on_image_list


    def populate_update_list(self, img_list):

        security_attr, security_keywords = ips.get_security_defs(self.config)

        # Tracks whether any pkg to be updated has security fixes.  If it
        # does then the security emblem definition needs to be displayed in
        # the status area
        self.show_security_emblem = False

        self.Bind(listers.EVT_LISTING_COMPONENT, self.OnListingEvent)

        self.img_count = len(img_list)

        # Update the top status
        if self.img_count == 0:
            self.top_stt.SetLabel(TEXT_NO_UPDATES_AVAILABLE)
            self._set_button_state(BTNS_INSTALL)
            self._update_var_btn_label()
            utils.logger.info("No application images available to check for updates")
            # No images to update so set the focus to the Close button.
            self.close_btn.SetFocus()
            return
        else:
            if self.img_count == 1:
                self.status.set_status(
                                     _("Checking for updates in 1 application"))
            else:
                self.status.set_status(
                                 _("Checking for updates in %d applications") %
                                                                 self.img_count)

            self.status.throb()
            self.middle_sizer.Layout()

        self._update_check_begin()
        update_thread_started = False

        for img_details in img_list.itervalues():
            assert img_details['type'] == CONST.T_NORMAL, \
                        "populate_update_list: T_ADD_ON in img_list: " + \
                                                    str(img_details['imgroot'])

            if img_details['type'] != CONST.T_NORMAL:
                continue

            # XXX: If the user has 50 images, 50 threads will be spawned.
            #      Need to limit the number of thread in use.

            #print "Starting UpdatesLister for %d (%s)" % (img_details['id'], fsenc(img_details['imgroot']))
            utils.logger.debug("%d: Checking for updates in %s" % \
                            (img_details['id'], fsenc(img_details['imgroot'])))

            lockmanager.lock()
            if lockmanager.get_image_state(img_details['imgroot'])[1] is not None:
                self.img_count -= 1
                utils.logger.warning("Unable to perform update check in: " + img_details['imgroot'])
                utils.logger.warning("An update check may be already occurring in this directory.")
                utils.logger.warning("The desktop notifier may be performing this check.  Wait a minute or two and retry the update check.")
                continue
            else:
                lockmanager.flag_running(img_details['imgroot'], views.UPDATES)
            lockmanager.release()

            global_settings.client_name = APP_CLIENT_NAME

            # The results on the UpdatesListerThread's work is placed on the
            # update_queue.
            self.worker = listers.UpdatesListerThread(parent=self,
                                            uid=img_details['id'],
                                            imagedir=img_details['imgroot'],
                                            max_recent=1,
                                            security_attr=security_attr,
                                            security_keywords=security_keywords)
            if not update_thread_started:
                update_thread_started = True
                self._update_check_begin()


    def process_update_queue(self):

        # The UpdatesListerThreads put the results of their work in the
        # update_queue.  This method drains from the queue.
        while not self.update_queue.empty():
            event = self.update_queue.get()

            type, item = event.value
            id = event.GetId()

            if type == listers.LISTING_DATA:
                pkg = {}
                pkg['fmri'] = item['fmri']
                pkg['size'] = item['size']
                pkg['title'] = item['items'][1]    # pkg.summary/description
                pkg['version'] = item['items'][4]  # pkg version
                pkg['security'] = item['items'][2]
                pkg['publisher'] = item['items'][7]

                # XXX: Note we are only using the first URL in the list.
                if item['detailed-url'] and len(item['detailed-url']) > 0:
                    pkg['detailed-url'] = item['detailed-url'].split()[0]
                else:
                    pkg['detailed-url'] = None

                # If a package has a security fix then enable the security
                # emblem text.
                if pkg['security']:
                    self.show_security_emblem = True

                self.image_list[id]['pkgs'].append(pkg)
                self.image_list[id]['imageplan'] = item['imageplan']

                utils.logger.debug("%d: -------> Found an update for: %s (%s)" % \
                                        (id,
                                         pkg['fmri'],
                                         fsenc(self.image_list[id]['imgroot'])))

            elif type == listers.LISTING_SUCCESS:
                self.img_count -= 1

                # Only update the list if there are pkgs with pending updates.
                if self.image_list[id]['pkgs'] != []:
                    itemCols = self.prepare_update_list_cols(id)
                    #XXX fmri=id - use more generic option (not fmri)
                    self.lists["updates"].append_data_row(fmri=id, size=0, items=itemCols)
                    self.top_bold_stt.SetLabel(TEXT_NEW_SW_AVAILABLE)
                    self.top_stt.SetLabel(TEXT_UPDATES_AVAILABLE)
                    utils.logger.debug("%d: -------> Listing Success for: %s" % \
                                        (id,
                                         fsenc(self.image_list[id]['imgroot'])))
            elif type == listers.LISTING_WARNING:
                image_details = self.image_list[id]
                title = ips.get_image_title(fsenc(image_details['imgroot']),
                                            opname='list')
                utils.logger.warning("%d: Unable to check for updates in ``%s'':\n%s",
                                     id, title, item)
            elif type == listers.LISTING_ERROR or \
                 type == listers.LISTING_LONG_ERROR:
                self.img_count -= 1
                image_details = self.image_list[id]
                title = ips.get_image_title(fsenc(image_details['imgroot']),
                                            opname='list')
                utils.logger.warning("%d: Unable to check for updates in ``%s'':\n%s",
                                     id, title, item)
            else:
                image_details = self.image_list[id]
                title = ips.get_image_title(fsenc(image_details['imgroot']),
                                            opname='list')
                utils.logger.error("Unknown type returned from Update Lister: %s for image %s.",
                                     str(type), title)

            # Update the top status each time we process an item in the
            # queue.
            if self.img_count == 1:
                self.status.set_status(
                                     _("Checking for updates in 1 application"))
            else:
                self.status.set_status(
                                 _("Checking for updates in %d applications") %
                                                                 self.img_count)

            # If the pending image count reaches 0 and the status text is
            # still displayed update the status text since there are no
            # images with pending updates.
            if self.img_count == 0:
                self.status.throb(False)
                self.status.set_status("")
                self.button_is_stop = False
                self.var_btn.SetLabel(_("Install"))

                self._set_button_state(BTNS_INSTALL)

                if self._lists_have_item():
                    self.lists["updates"].SetFocus()
                else:
                    self.top_bold_stt.SetLabel(" ")
                    self.top_stt.SetLabel(TEXT_NO_UPDATES_AVAILABLE)
                    self.close_btn.SetFocus()

                if self.show_security_emblem:
                    self._manage_security_emblem(True)

                self.Unbind(listers.EVT_LISTING_COMPONENT)

                # Once we complete the update checks we see if there is any
                # addon SW available.
                # XXX: We have to wait to avoid performing simultaneous
                # operations in the same image.
                wx.CallAfter(self._perform_addon_check)
                self._update_check_end(self.image_list)


    # This is invoked when the SW Update UI is instantiated from the
    # notifier or it is already running and the notifier wants it to
    # reload.
    def update_lists(self, image_list, add_on_exists):

        # If this is called before the prior add-on check completes
        # we ignore this request to update the list.
        if self.lists["new"].is_updating():
            utils.logger.debug("update_lists: aborting. is_updating is True")
            return

        self.image_list = image_list
        self.image_list_count = len(self.image_list)

        # If there are add-ons and the add-on list is not shown we need
        # to display it.
        if add_on_exists:
            self._show_add_on_list()

        # Clear existing add-ons from the image_list.  They will be added
        # after we display the updates.
        self._clear_addons(self.image_list)

        self.img_count = 0
        self.regenerate_ui_lists()
        wx.YieldIfNeeded()

        # Get the current set of add-ons.
        self._perform_addon_check()

        # Only set to install if there are items to install.
        self._update_var_btn_label()
        self._set_button_state(BTNS_INSTALL)


    # If the add-on list is not shown - add it and resize the frame
    def _show_add_on_list(self):
        if not self.lists["new"].IsShown():
            self.lists["new"].DeleteAllItems()
            self.set_frame_size(True)
            self.main_sizer.Insert(4, (0,8))
            self.lists["new"].Show(True)
            self.main_sizer.Layout()


    # Indicates an update check has started.
    def _update_check_begin(self):
        # If the update_notifier_func is set then we were
        # invoked in-process by the notifier.  So we ping the
        # notifier via this callback to tell it that an update check
        # has started.
        if self.update_notifier_func != None:
            self.update_notifier_func(None, CONST.UC_BEGIN)

        self.lists["updates"].set_updating(True)


    # Indicates the current update check has finished or that we finished
    # installing an update.
    def _update_check_end(self, img_list):
        # If the update_notifier_func is set then we were
        # invoked in-process by the notifier.  So we ping the
        # notifier via this callback to tell it that an update check
        # has completed.
        if self.update_notifier_func != None:
            self.update_notifier_func(img_list, CONST.UC_END)

        self.lists["updates"].set_updating(False)


    def regenerate_ui_lists(self):

        self.lists["updates"].DeleteAllItems()
        self.lists["new"].DeleteAllItems()

        has_security_fix = False

        self.lists["new"].set_updating(True)
        self.lists["updates"].set_updating(True)

        for img_details in self.image_list.itervalues():
            if img_details['type'] == CONST.T_NORMAL:
                # Only update the list if there are pkgs with pending updates.
                if img_details['pkgs'] != []:
                    for pkg in img_details['pkgs']:
                        if pkg['security']:
                            has_security_fix = True
                    id = img_details['id']
                    itemCols = self.prepare_update_list_cols(id,
                                                 preserve_check_box_state=False)
                    #XXX fmri=id - use more generic option (not fmri)
                    self.lists["updates"].append_data_row(fmri=id,
                                                       size=0,
                                                       items=itemCols)
            elif img_details['type'] == CONST.T_ADD_ON or \
                 img_details['type'] == CONST.T_NEW_IMAGE:
                if img_details['id'] == -1:
                    continue

                itemCols = self.prepare_addon_list_cols(
                                                img_details['id'],
                                                preserve_check_box_state=True)
                #XXX fmri=id - use more generic option (not fmri)
                self.lists["new"].append_data_row(fmri=img_details['id'],
                                               size=0,
                                               items=itemCols)

        self.lists["new"].set_updating(False)
        self.lists["updates"].set_updating(False)

        if has_security_fix:
            self._manage_security_emblem(True)
        else:
            self._manage_security_emblem(False)

        if self._lists_have_item():
            self.top_bold_stt.SetLabel(TEXT_NEW_SW_AVAILABLE)
            self.top_stt.SetLabel(TEXT_UPDATES_AVAILABLE)
            self.lists["updates"].SetFocus()
        else:
            self.top_bold_stt.SetLabel(" ")
            self.top_stt.SetLabel(TEXT_NO_UPDATES_AVAILABLE)
            self.close_btn.SetFocus()


    def prepare_update_list_cols(self, id, preserve_check_box_state=False):
        img_details = self.image_list[id]

        self.compute_update_attrs(img_details)

        itemCols = []
        if preserve_check_box_state:
            if img_details['checked']:
                itemCols.append(True) # 0 - This is the checkbox field
            else:
                itemCols.append(False) # 0 - This is the checkbox field
        else:
            itemCols.append(True) # 0 - This is the checkbox field
            img_details['checked'] = True
        itemCols.append(
                 ips.get_image_title(fsenc(img_details['imgroot']), opname='list')) #1
        itemCols.append(img_details['security'])
        itemCols.append(utils.readable_size(img_details['size'])) # 3
        itemCols.append(" ") # 4

        return itemCols


    def prepare_addon_list_cols(self, id, preserve_check_box_state=False):
        img_details = self.image_list[id]
        entry = img_details['feed_entry']

        itemCols = []
        if preserve_check_box_state:
            if img_details['checked']:
                itemCols.append(True) # 0 - This is the checkbox field
            else:
                itemCols.append(False) # 0 - This is the checkbox field
        else:
            itemCols.append(False) # 0 - This is the checkbox field
            img_details['checked'] = False

        if entry.has_key(BF.TITLE):
            itemCols.append(entry[BF.TITLE]) # 1
        else:
            itemCols.append(_("Title missing in feed entry")) # 1

        if entry.has_key(BF.VERSION):
            itemCols.append(entry[BF.VERSION]) # 2
        else:
            itemCols.append("") # 2

        if entry.has_key(BF.SIZE) and utils.is_integer_string(entry[BF.SIZE]):
            itemCols.append(utils.readable_size(int(entry[BF.SIZE]) * 1024)) # 3
        else:
            itemCols.append("") # 3

        itemCols.append(" ") # 4

        return itemCols


    def compute_update_attrs(self, img_details):

        # Compute the size of the update and determine if any of the changes
        # impact security.
        img_details['size'] = 0
        img_details['security'] = False
        for pkg in img_details['pkgs']:
            img_details['size'] += pkg['size']
            if pkg['security']:
                img_details['security'] = True


    def get_id_from_image(self, img_path):

        # Given an image path return the image's ID in the image_list.
        for img_details in self.image_list.itervalues():
            if img_details['imgroot'] == img_path:
                return img_details['id']

        # Not found
        return -1


    def _construct_update_html(self, img_details, id):
        html = "<html>\n<body>\n" + \
               _("<center><h3>%s - Update</h3></center>\n") % \
                      ips.get_image_title(fsenc(img_details['imgroot']), opname='list')

        # If any of the packages have a security fix then we will display
        # the emblem in the table and a description of what the emblem means
        # below the table.
        has_security_fix = False
        for pkg in self.image_list[id]['pkgs']:
            if pkg['security']:
                has_security_fix = True

        html = html + \
               _("An update is available for this application image. ")

        if has_security_fix:
            html = html + \
                   _("This update contains enhancments related to the ") +\
                   _("security of the product. ")

        html = html + \
               _("Applying this update will modify ") +\
               str(len(self.image_list[id]['pkgs']))

        if len(self.image_list[id]['pkgs']) > 1:
            html = html + \
                   _(" components.  The components to be modified are listed below.\n")
        else:
            html = html + \
                   _(" component.  The component to be modified is listed below.\n")

        html = html + \
            "<DL>" + \
            _("<DT>This application image is located at:") + \
            "<DD>%s" % img_details['imgroot'] + \
            "</DL>\n"

        html = html + \
               _("<P>The following component(s) will be updated:") + \
               "<P><TABLE border=0><TR>"

        if has_security_fix:
            html = html + \
                _("<TH align=left BGCOLOR=lightgrey><B>Component</B><TH BGCOLOR=lightgrey>  </TH></TH><TH BGCOLOR=lightgrey><B>New Version</B></TH><TH BGCOLOR=lightgrey><B>Source</B></TH></TR>\n")
            img_path = os.path.join(os.path.dirname(__file__), "..",
                                                    "images",
                                                    SECURITY_IMAGE_NAME)
        else:
            html = html + \
                _('<TH align="left" BGCOLOR=lightgrey><B>Component</B></TH><TH BGCOLOR=lightgrey><B>New Version</B></TH><TH BGCOLOR=lightgrey><B>Source</B></TH></TR>\n')

        for pkg in self.image_list[id]['pkgs']:
            if has_security_fix:
                html = html + "<TR>\n"

                if pkg['detailed-url'] and len(pkg['detailed-url']) > 0:
                    html = html + \
                        '<TD><a href="%s">%s</a></TD>\n' % \
                                    (pkg['detailed-url'], pkg['title'])

                else:
                    html = html + "<TD>%s</TD>\n" % pkg['title']

                if pkg['security']:
                    html = html + '<TD><IMG SRC="' + \
                                  img_path + '" ALIGN=BOTTOM ALT="!"></TD>\n'
                else:
                    html = html + '<TD></TD>\n'
            else:
                html = html + "<TR>\n"

                if pkg['detailed-url'] and len(pkg['detailed-url']) > 0:
                    html = html + \
                        '<TD><a href="%s">%s</a></TD>\n' % \
                                    (pkg['detailed-url'], pkg['title'])
                else:
                    html = html + "<TD>%s</TD>\n" % pkg['title']

            html = html + "<TD>%s</TD>\n</TR>\n" % pkg['version']
            html = html + "<TD>%s</TD></TR>\n" % pkg['publisher']

        html = html + \
               "</TABLE></DL>\n"

        if has_security_fix:
            html = html + \
                _('<BR><DD><IMG SRC="' + img_path + '" ALT="!"> - Indicates update contains a security enhancement.')

        html = html + \
               "<P></body></html>\n"

        return html


    def _construct_newsw_html(self, img_details):

        entry = img_details['feed_entry']
        add_on_image_list = img_details['add_on_image_list']
        s = ""

        s = s + '<table border="0"><tr>'
        if entry.has_key(BF.ICON_URL):
            i_url = entry[BF.ICON_URL]
            s = s + '<td><img src="' + i_url + '"/></td>'

        if entry.has_key(BF.TITLE):
            t = entry[BF.TITLE]
            s = s + '<td><h3>' + t + '</h3></td>'

        s = s + "</tr></table>"

        if entry.has_key(BF.SUMMARY):
            s = s + entry[BF.SUMMARY]

        s = s + "<P>"

        if img_details['type'] == CONST.T_NEW_IMAGE:
            if entry.has_key(BF.ALT_URL):
                s = s + _('Additional information about this software is available at the <a href="%s">%s</a> website.<P>' % (entry[BF.ALT_URL], entry[BF.TITLE]))
        else: # type == CONST.T_ADD_ON
            found_selected = False
            for img_data in add_on_image_list:
                if img_data['selected']:
                    found_selected = True
                    break

            if found_selected or len(add_on_image_list) == 1:
                s = s + _("This 'Add-On' software will be applied to the following application image(s):<P>")
            else:
                s = s + _("This 'Add-On' software may be applied to the following application image(s):<P>")

            s = s + self._construct_addon_img_table(add_on_image_list,
                                                selected_only = found_selected)
        return s


    def _construct_addon_img_table(self, add_on_image_list, selected_only=False):

        s = "<DD><TABLE border=0><TR>" + \
            _("<TH BGCOLOR=lightgrey><B>Title</B></TH><TH BGCOLOR=lightgrey><B>Directory</B></TH></TR>\n")

        for img_data in add_on_image_list:
            if selected_only and not img_data['selected']:
                continue

            img_root = self.image_list[img_data['id']]['imgroot']
            title = ips.get_image_title(fsenc(img_root), opname='list')

            s = s + \
                   "<TR>\n" + \
                   "<TD>%s</TD>\n" % title + \
                   "<TD>%s</TD>\n" % img_root + \
                   "</TR>\n"

        s = s + \
               "</TABLE></DL>\n"

        return s


    def _abort_threads(self):

        lockmanager.lock()
        lockmanager.abort_all()
        lockmanager.release()

        while lockmanager.any_active():
            import time

            if time.time() % 5 < 1:
                utils.logger.debug("Waiting on thread: %s" % lockmanager.any_active())
            wx.Sleep(1.0)
            wx.YieldIfNeeded()

        utils.logger.debug("All threads are dead.")


    def _enable_lic_checkbox(self, enable):

        if enable:
            self.license_link.SetNormalColour(self.license_link_normal_color)
            self.license_checkbox.Enable()
            self.license_link.Enable()
        else:
            self.license_link.SetNormalColour(self.license_link_disabled_color)
            self.license_checkbox.Disable()
            self.license_link.Disable()


    def _set_button_state(self, state):

        if state == BTNS_CHECKING:
            self.app_center_btn.Enable()
            self.refresh_btn.Disable()
            self._enable_lic_checkbox(False)
            self.close_btn.Enable()
            self.var_btn.Enable()
            self.button_is_stop = True
            self.var_btn.SetLabel(_("Stop"))
            self.var_btn.SetToolTipString(_("Stop searching for application updates"))
        elif state == BTNS_INSTALL:
            self.app_center_btn.Enable()
            self.refresh_btn.Enable()
            self.close_btn.Enable()

            self.var_btn.SetToolTipString(_("Update/Install selected items"))

            # Determine if there are any checked items in the lists.
            if not self._list_has_checked_item(self.lists["updates"]):
                if not self._list_has_checked_item(self.lists["new"]):
                    # No checked items, disable the button.
                    self.var_btn.Disable()
                    self._enable_lic_checkbox(False)
                    return

            self._enable_lic_checkbox(True)
            self.var_btn.Enable()
        elif state == BTNS_CLOSING:
            self.app_center_btn.Disable()
            self.refresh_btn.Disable()
            self._enable_lic_checkbox(False)
            self.close_btn.Disable()
            self.var_btn.Disable()
        elif state == BTNS_STOPPING:
            self.app_center_btn.Enable()
            self.refresh_btn.Disable()
            self._enable_lic_checkbox(False)
            self.close_btn.Disable()
            self.var_btn.Disable()
            # On MAC the button is not wide enough to accomodate the text.
            if '__WXMAC__' == wx.Platform:
                self.var_btn.SetLabel(_("Stop"))
            else:
                self.var_btn.SetLabel(_("Stopping..."))
        else: #BTNS_STOPPED:
            self.app_center_btn.Enable()
            self.refresh_btn.Enable()
            self.close_btn.Enable()

            # Determine if there are any checked items in the lists.
            if not self._list_has_checked_item(self.lists["updates"]):
                if not self._list_has_checked_item(self.lists["new"]):
                    # No checked items, disable the button.
                    self.var_btn.Disable()
                    self._enable_lic_checkbox(False)
                    return

            self._enable_lic_checkbox(True)
            self.var_btn.Enable()


    def _manage_security_emblem(self, enable):
        if enable:
            self.status.Hide()
            self.security_stb.Show()
            self.security_stt.Show()
        else:
            self.security_stb.Hide()
            self.security_stt.Hide()
            self.status.Show()

        self.middle_sizer.Layout()


    def _list_has_checked_item(self, l):
        for i in xrange(l.GetItemCount()):
            if l.IsChecked(i):
                return True
        return False


    def load_ad_page(self):
        self.desc_html.SetBorders(0)

        # Don't allow scrollbars to appear in window.
        self.desc_html.SetVirtualSizeHintsSz((395, 10), maxSize=(495, 200))
        self.main_sizer.Layout()
        self.ad_displayed = True

        url = self.get_advert_url()
        if url == "":
            self.desc_html.SetPage(get_advert_html())
        else:
            self.desc_html.LoadPage(url)
        self.desc_html.SetBorders(5)


    # The notifer informs us when it is starting or ending an update check.
    # Issue 1603
    def update_check_in_progress(self, in_progress):
        if in_progress:
            self.refresh_btn.Disable()
        else:
            self.refresh_btn.Enable()


    def get_advert_url(self):
        import random
        import urllib2

        ad_id = random.randrange(1, ADVERT_COUNT + 1)
        while ad_id == self.last_id:
            ad_id = random.randrange(1, ADVERT_COUNT + 1)
        self.last_id = ad_id

        # Advertisement feed for ads appearing in the tool
        ad_feed_url = self.config.get('main', 'ad.feed.url')
        if ad_feed_url is not None and len(ad_feed_url) > 0:
            url = ad_feed_url + "ad_" + str(ad_id) + ".html"
        else:
            url = ADVERT_BASE_URL + "ad_" + str(ad_id) + ".html"

        try:
            f = urllib2.urlopen(url)
            url = f.geturl()
        except IOError, e:
            if hasattr(e, 'reason'):
                utils.logger.info("Unable to access ad server: %s (%s)" %
                                                                  (str(e), url))
            elif hasattr(e, 'code'):
                utils.logger.info("Ad server request failed: %s (%s)" %
                                                                  (str(e), url))
            else:
                utils.logger.info("Ad server request failed: %s (%s)" %
                                                                  (str(e), url))
            url = ""
        except Exception, e:
            utils.logger.info("(E) Ad server request failed: %s (%s)" %
                                                                  (str(e), url))
            url = ""

        return url


    def set_frame_size(self, with_add_on_list):

        if with_add_on_list:
            height = 680
        else:
            height = 538

        if wx.Platform == "__WXMSW__":
            self.SetSize((530, height))
        else:
            self.SetSize((520, height))


    def _clear_addons(self, image_list):

        for img_details in image_list.itervalues():
            if img_details['type'] == CONST.T_ADD_ON or \
               img_details['type'] == CONST.T_NEW_IMAGE:
                img_details['id'] = -1


    def _lists_have_item(self):
        if self.lists["updates"].GetItemCount() or \
           self.lists["new"].GetItemCount():
            return True
        return False


def split_feed(feeddata):
    """
    Split a single feeddata into two lists of entries. The
    first is for app_types of "pkg" or "native", the
    second is for app_types of "addon
    """

    apps = []
    addons = []
    for e in feeddata[BF.ENTRIES]:
        if e[BF.APP_TYPE] == "addon":
            addons.append(e)
        else:
            apps.append(e)

    return (apps, addons)


class InfoHtmlWindow(wx.html.HtmlWindow):

    def __init__(self, parent, *args, **kwargs):
        wx.html.HtmlWindow.__init__(self, parent, *args, **kwargs)


    def OnLinkClicked(self, link):
        #print "wx.LaunchDefaultBrowser(): " + link.GetHref()
        wx.LaunchDefaultBrowser(link.GetHref())


def get_advert_html():

    html = '<html><body bgcolor="#E6E6E6"></body></html>'

    try:
        pass
        #f = urllib2.urlopen(ADVERT_BANNER_URL)
        #banner_target_url = f.geturl()
        #
        #html = "<html><body>\n<a href='" + ADVERT_TARGET_URL + \
        #       "' target='_blank'><img src='" + banner_target_url + \
        #       "' border='0' /></a>"
    except IOError, e:
        if hasattr(e, 'reason'):
            utils.logger.warning("Unable to access ad server: %s" % str(e))
        elif hasattr(e, 'code'):
            utils.logger.warning("Ad server request failed: %s" % str(e))
        else:
            utils.logger.warning("Ad server request failed: %s" % str(e))

    return html


def start_gui(image_path, alt_path="run"):

    import subprocess

    if image_path == "":
        exec_path = alt_path
        utils.logger.debug("starting gui: using alt path: %s", exec_path)
    elif wx.Platform == "__WXMSW__":
        exec_path = os.path.join(image_path, 'updatetool', 'bin',
                                 'updatetool.exe')
    else:
        exec_path = os.path.join(image_path, 'updatetool', 'bin',
                                             'updatetool')
    err = ""
    error_code = 0

    if os.path.exists(exec_path):
        args =  " --silentstart"

        # Launch the GUI.
        try:
            utils.logger.debug("launching: %s %s", exec_path, args)

            if "__WXMSW__" in wx.PlatformInfo:
                # close_fds is not supported on Windows.
                close_fds_on_popen = False
            else:
                close_fds_on_popen = True

            dummy_proc = subprocess.Popen('"' + exec_path + '"' + args,
                                    stdout=None,
                                    stderr=None,
                                    shell=True,
                                    close_fds=close_fds_on_popen)
        except OSError, e:
            utils.logger.warning("updatetool start up: failed: %s", e)
            err = str(e)
            error_code = 1
        except Exception, e:
            utils.logger.warning("updatetool start up: failed: %s", e)
            err = str(e)
            error_code = 1
    else:
        utils.logger.warning("updatetool start up: failed: path does not exist: %s", exec_path)
        err = _("Path does not exist: %s" % exec_path)
        error_code = 1

    return (error_code, err)
