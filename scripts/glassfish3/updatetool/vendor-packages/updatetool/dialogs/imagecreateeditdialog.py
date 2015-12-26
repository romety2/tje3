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

from common.fsutils import fsenc
from common.mixins import KeywordArgsMixin
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
import os.path
import common.ips as ips
import pkg.misc as pkgmisc
import common.utils as utils
import dialogs
from dialogs.repohelperdialog import RepoHelperDialog

PubListChangedEvent, EVT_APP_PUB_LIST_CHANGED = wx.lib.newevent.NewEvent()


class AppPubListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin, KeywordArgsMixin):
    """
    AppPubListCtrl is a

    1) ListCtrl extended with ListCtrlAutoWidthMixin to automatically resize
    2) holder of image publisher data
    """

    _ = wx.GetTranslation

    def __init__(self, parent, ident, *args, **kwargs):
        KeywordArgsMixin.__init__(self)
        self.kwset(kwargs, 'pubs', default=[])
        kwargs['style'] = wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL | wx.FULL_REPAINT_ON_RESIZE
        wx.ListCtrl.__init__(self, parent, ident, *args, **kwargs)
        ListCtrlAutoWidthMixin.__init__(self)

        # Some GTK themes offset their glyph bitmaps such that they get
        # clipped at the bottom. To compensate we make them a hair larger.
        if wx.Platform == "__WXGTK__":
            self.glyph_size = (18, 18)
        else:
            self.glyph_size = (16, 16)

        self.img_list = wx.ImageList(self.glyph_size[0], self.glyph_size[1])
        self.check_image   = self.img_list.Add(
                utils.create_checkbox_bitmap(self, wx.CONTROL_CHECKED, self.glyph_size))
        self.uncheck_image = self.img_list.Add(
                utils.create_checkbox_bitmap(self, 0, self.glyph_size))
        self.press_image   = self.img_list.Add(
                utils.create_radiobutton_bitmap(self, wx.CONTROL_CHECKED, self.glyph_size))
        self.unpress_image = self.img_list.Add(
                utils.create_radiobutton_bitmap(self, 0, self.glyph_size))


        self.last_key_down = wx.WXK_SPACE
        self.last_item_activated = 0

        self.SetImageList(self.img_list, wx.IMAGE_LIST_SMALL)
        self.SetItemCount(len(self._pubs))
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseClick)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated, self)

        # When the <space>  is pressed we want to toggle the Enabled
        # checkbox. When <return> is pressed we want to set the
        # Preferred radio button. We must detect <return> differently
        # on Windows than on the other platforms. See bug 871
        if wx.Platform == "__WXMSW__":
            self.Bind(wx.EVT_COMMAND_ENTER, self.OnItemEntered, self)
        else:
            self.Bind(wx.EVT_LIST_KEY_DOWN, self.OnKeyDown, self)


    def OnGetItemText(self, item, col):
        """ Interface implemented for virtual list control"""
        if col == 1:
            return self._pubs[item][0]
        else:
            return ""


    def OnGetItemColumnImage(self, item, col):
        """ Interface implemented for virtual list control"""
        if col == 0:
            if self.is_enabled(item):
                return self.check_image
            else:
                return self.uncheck_image
        elif col == 2:
            if self.is_preferred(item):
                return self.press_image
            else:
                return self.unpress_image
        else:
            return -1


    def OnGetItemAttr(self, dummy_item):
        """ Interface implemented for virtual list control"""
        return None


    def OnKeyDown(self, event):
        # We save the key pressed so we know what key was pressed in
        # OnItemActivated to differentiate between <return> and <space>
        # Note: this technique is not used on Windows. See OnItemEntered.
        utils.logger.debug("OnKeyDown keycode=%d" % event.GetKeyCode())
        self.last_key_down = event.GetKeyCode()
        event.Skip()


    def OnItemActivated(self, event):
        # A bit kludgey...
        # If spacebar activated then toggle check, else set preferred
        # Note on Windows last_item_activated will always be SPACE.
        utils.logger.debug("OnItemActivated keycode=%d, index=%d" % (event.GetKeyCode(), event.m_itemIndex))
        self.last_item_activated = event.m_itemIndex
        if self.last_key_down == wx.WXK_SPACE :
            self.toggle_enabled(event.m_itemIndex)
        else:
            self.set_preferred(event.m_itemIndex)
        event.Skip()


    def OnItemEntered(self, dummy_event):
        # More kludge...
        # We only use this event on Windows. On Windows this event is
        # triggered when the user types <enter> on a list item.
        # The event is triggered *after* OnItemActivated. We rely
        # on OnItemActivated to set the item number. More info in bug 871
        utils.logger.debug("OnItemEntered last_item_activated=%d" % self.last_item_activated)
        self.set_preferred(self.last_item_activated)


    def set_preferred(self, index):
        utils.logger.debug("set_preferred(%d)" % index)
        # Check if we are already preferred
        if self._pubs[index][2] == True:
            return

        # Set preferred
        self.prefer_pub_item(index)

        # If item is not already enabled then enable it
        if not self.is_enabled(index):
            self.toggle_enabled(index)

        # Make sure button state is correct
        wx.PostEvent(self.GetTopLevelParent(), PubListChangedEvent(data=None))

        self.Refresh()


    def toggle_enabled(self, index):
        utils.logger.debug("toggle_enabled(%d)" % index)

        if self.is_enabled(index) and self.is_preferred(index):
            # Don't allow disabling the preferred repo
            wx.MessageBox(_("You may not disable the preferred publisher '%s'. " \
                    "Please select a new preferred publisher before disabling this one.") % self._pubs[index][0], \
                    style=wx.OK|wx.ICON_EXCLAMATION|wx.CENTER, caption=_("Disable Publisher"), parent=self)
            return

        # If we are enabling a disabled https repo and there is no client
        # key or cert, automatically bring up Edit dialog
        ipub = self._pubs[index]
        if not self.is_enabled(index) and ipub[1].startswith("https") and (ipub[3] == None or ipub[4] == None or ipub[3].strip() == "" or ipub[4].strip() == ""):
            # Bring up edit dialog
            wx.PostEvent(self.GetTopLevelParent(), PubListChangedEvent(data=index))

        # Toggle Enabled checkbox
        self._pubs[index][5] = not (self._pubs[index][5])

        wx.PostEvent(self.GetTopLevelParent(), PubListChangedEvent(data=None))

        self.Refresh()


    def OnMouseClick(self, event):
        index = self.HitTest(event.GetPosition())[0]
        x = event.GetPosition()[0]
        col = -1
        # Check if we are clicking on one of our glyphs
        if x < self.GetColumnWidth(0):
            if x < self.glyph_size[0]:
                # Clicked on "Enable" glyph
                col = 0
        elif x > self.GetColumnWidth(0) + self.GetColumnWidth(1):
            if x < self.GetColumnWidth(0) + self.GetColumnWidth(1) + self.glyph_size[0]:
                # Clicked on "Preferred" glyph
                col = 2
        else:
            # Clicked on no glyph
            col = -1

        event.Skip()
        if col == 0:
            # Toggle "Enable" state
            self.toggle_enabled(index)
        elif col == 2:
            self.set_preferred(index)
        else:
            # Nothing to do on other columns
            pass


    def _add_pub_item(self, pubname=None, puburl=None, preferred=False, ssl_key=None, ssl_cert=None, disabled=False):
        assert pubname is not None
        assert puburl is not None
        assert isinstance(puburl, basestring)

        if isinstance(puburl, unicode):
            puburl = str(puburl)

        pubnames = [a[0] for a in self._pubs]
        if pubname in pubnames:
            idx = pubnames.index(pubname)
            self._pubs[idx][1:6] = puburl, preferred, ssl_key, ssl_cert, disabled
        else:
            self._pubs.append([pubname, puburl, preferred, ssl_key, ssl_cert, disabled])
            idx = len(self._pubs) - 1
            self.SetItemCount(len(self._pubs))

        self.SetItemState(idx, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        self.SetItemState(idx, wx.LIST_STATE_FOCUSED, wx.LIST_STATE_FOCUSED)
        self.Refresh()


    def remove_pub_item(self, item):
        if 0 <= item < len(self._pubs):
            if self._pubs[item][2]:
                return (False, _("Removal of preferred publisher is not allowed."))
            self._pubs.pop(item)
            self.SetItemCount(len(self._pubs))
            self.Refresh()
            return (True, None)
        return (False, _("Specified item could not be found."))


    def _replace_pub_item(self, old_pub, old_url, old_prefer, old_ssl_key, old_ssl_cert, old_disabled,
                                new_pub, new_url, new_prefer, new_ssl_key, new_ssl_cert, new_disabled):
        """
        Emulates set-publisher
        """
        utils.logger.debug("replace_pubitem: %s,%s with %s,%s" % (old_pub, old_url, new_pub, new_url))

        if [old_pub, old_url, old_prefer, old_ssl_key, old_ssl_cert, old_disabled] not in self._pubs:
            utils.logger.debug("Specified item not found: %s %s %s %s %s %s" % (old_pub, old_url, old_prefer, old_ssl_key, old_ssl_cert, old_disabled))
            utils.logger.debug("known pubs: %s" % self._pubs )
            return (False, _("Specified item could not be found."))

        if old_prefer and not new_prefer:
            return (False, _("The image must have at least one preferred publisher."))

        if not pkgmisc.valid_pub_prefix(new_pub):
            return (False, _("The publisher name contains invalid characters."))

        if not pkgmisc.valid_pub_url(new_url):
            return (False, _("The new publisher URL is invalid."))

        if new_ssl_key and len(new_ssl_key) > 0 and (not os.path.exists(os.path.abspath(new_ssl_key))):
            return (False, _("The SSL key file does not exist"))

        if new_ssl_cert and len(new_ssl_cert) > 0 and (not os.path.exists(os.path.abspath(new_ssl_cert))):
            return (False, _("The SSL certificate file does not exist"))

        old_idx = self._pubs.index([old_pub, old_url, old_prefer, old_ssl_key, old_ssl_cert, old_disabled])
        utils.logger.debug("old_idx=%d" % (old_idx))
        pub_names = [a[0] for a in self._pubs]
        if new_pub not in pub_names:         # easy case
            utils.logger.debug("Adding new pub %s" % new_pub)
            self._pubs[old_idx] = [new_pub, new_url, new_prefer, new_ssl_key, new_ssl_cert, new_disabled]
        else:
            if old_pub == new_pub:
                utils.logger.debug("Pub name unchanged")
                self._pubs[old_idx] = [new_pub, new_url, new_prefer, new_ssl_key, new_ssl_cert, new_disabled]
            else:
                utils.logger.debug("Pub name has changed")
                del_idx = pub_names.index(new_pub)
                self._pubs[old_idx] = [new_pub, new_url, new_prefer, new_ssl_key, new_ssl_cert, new_disabled]
                self._pubs.pop(del_idx)
                if old_idx > del_idx:
                    old_idx -= 1
        if new_prefer:
            for idx, a in enumerate(self._pubs):
                if idx != old_idx:
                    self._pubs[idx][2] = False

        self.Refresh()
        return (True, None)


    def prefer_pub_item(self, item):
        if 0 <= item < len(self._pubs):
            for x in xrange(len(self._pubs)):
                self._pubs[x] = [self._pubs[x][0], self._pubs[x][1], x == item, self._pubs[x][3], self._pubs[x][4], self._pubs[x][5]]
            self.Refresh()
            return (True, None)
        return (False, _("Specified item could not be found."))


    def get_pubs(self):
        """
        @return: a tuples array. Each tuple contains
            1) Name of publisher
            2) URL aka Origin
            3) Preferred boolean flag
            4) SSL Key path or None
            5) SSL Cert path or None
            6) Disabled boolean flag
        """
        return self._pubs


    def is_preferred(self, idx):
        return 0 <= idx < len(self._pubs) and self._pubs[idx][2]


    def is_enabled(self, idx):
        return 0 <= idx < len(self._pubs) and not self._pubs[idx][5]



class ImageCreateEditDialog(wx.Dialog, KeywordArgsMixin):

    _ = wx.GetTranslation

    def __init__(self, *args, **kwds):
        KeywordArgsMixin.__init__(self)
        temp_pubs = []
        self.kwset(kwds, 'opname', default=None)
        self.kwset(kwds, 'image', default=None)
        self.kwset(kwds, 'install', default=False)
        self.kwset(kwds, 'newsw_install', default=False)
        if self._image is not None:
            temp_pubs = ips.get_publishers(fsenc(self._image), opname=self._opname)
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.THICK_FRAME
        wx.Dialog.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)

        self.img_title_label = wx.StaticText(self.panel_1, -1, _("Image Title:"))
        self.img_title_text_ctrl = wx.TextCtrl(self.panel_1, -1, "")
        self.img_dir_label = wx.StaticText(self.panel_1, -1, _("Image Directory:"))
        self.dir_picker = wx.DirPickerCtrl(self.panel_1, style=wx.DIRP_USE_TEXTCTRL)
        self.img_desc_label = wx.StaticText(self.panel_1, -1, _("Image Description:"))
        self.img_desc_text_ctrl = wx.TextCtrl(self.panel_1, -1, "", style=wx.TE_MULTILINE|wx.TE_NO_VSCROLL)
        self.repos_label = wx.StaticText(self.panel_1, -1, _("Software Sources:"))
        self.pub_list_ctrl = AppPubListCtrl(self.panel_1, -1, style=wx.LC_REPORT|wx.LC_SINGLE_SEL|wx.FULL_REPAINT_ON_RESIZE)
        self.pub_list_ctrl.SetToolTipString(_("List of publishers this image installs software from. One publisher is preferred and takes precedence over the others."))
        self.pub_list_ctrl.InsertColumn(0, _("Enabled"), format=wx.LIST_FORMAT_CENTER, width=wx.LIST_AUTOSIZE_USEHEADER)
        self.pub_list_ctrl.InsertColumn(1, _("Publisher"), format=wx.LIST_FORMAT_LEFT, width=wx.LIST_AUTOSIZE_USEHEADER)
        self.pub_list_ctrl.InsertColumn(2, _("Preferred") + " ", format=wx.LIST_FORMAT_LEFT, width=wx.LIST_AUTOSIZE_USEHEADER)
        self.pub_list_ctrl.setResizeColumn(2)

        self.add_repo_button = wx.Button(self.panel_1, -1, _("Add..."))
        self.edit_repo_button = wx.Button(self.panel_1, -1, _("Edit..."))
        self.remove_repo_button = wx.Button(self.panel_1, -1, _("Remove"))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnRepoAdd, self.add_repo_button)
        self.Bind(wx.EVT_BUTTON, self.OnRepoEdit, self.edit_repo_button)
        self.Bind(wx.EVT_BUTTON, self.OnRepoRemove, self.remove_repo_button)

        if self._image is not None:    # Image edit
            self.SetTitle(_("Image Properties"))
            self.set_path(self._image)
            self.dir_picker.Enable(False)
            self.img_title_text_ctrl.SetValue(ips.get_image_title(fsenc(self._image), self._opname))
            self.img_desc_text_ctrl.SetValue(ips.get_image_description(fsenc(self._image), self._opname))
            for pubname, puburl, preferred, ssl_key, ssl_cert, disabled in temp_pubs:
                self.pub_list_ctrl._add_pub_item(pubname, puburl, preferred, ssl_key, ssl_cert, disabled)
            del temp_pubs
        self.pub_list_ctrl.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        self.pub_list_ctrl.SetItemState(0, wx.LIST_STATE_FOCUSED, wx.LIST_STATE_FOCUSED)
        self.img_title_text_ctrl.SetFocus()
        self.Centre()
        self.__set_tab_order()
        self.Bind(EVT_APP_PUB_LIST_CHANGED, self.OnPubListChanged)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.pub_list_ctrl)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected, self.pub_list_ctrl)

        self._set_buttons_state()


    def __set_properties(self):
        if self._install:
            if self._newsw_install:
                self.SetTitle(_("Confirm New Software Install Details"))
            else:
                self.SetTitle(_("Install Software"))
            self.dir_picker.SetToolTipString(_("The directory path where the software is to be installed. The path can be selected visually from the attached button also."))
        else:
            self.SetTitle(_("Create New Installation Image"))
            self.dir_picker.SetToolTipString(_("The directory path where image is to be created. The path can be selected visually from the attached button also."))

        self.img_title_text_ctrl.SetMinSize((300, -1))
        self.img_title_text_ctrl.SetToolTipString(_("For example - My Application Image"))
        self.img_desc_text_ctrl.SetMinSize((-1, 100))
        self.img_desc_text_ctrl.SetToolTipString(_("You can provide a detailed, multiline description of the image here."))
        self.add_repo_button.SetToolTipString(_("Add a new publisher to the image"))
        self.edit_repo_button.SetToolTipString(_("Edit the selected publisher's attributes"))
        self.remove_repo_button.SetToolTipString(_("Remove one or more selected publisher"))
        self.SetMinSize((600, 400))


    def __set_tab_order(self):
        # Explicitly set the tab order
        order = (self.img_title_text_ctrl,
                self.dir_picker,
                self.img_desc_text_ctrl,
                self.pub_list_ctrl,
                self.add_repo_button,
                self.edit_repo_button,
                self.remove_repo_button )
        for i in xrange(len(order) - 1):
            order[i+1].MoveAfterInTabOrder(order[i])


    def __do_layout(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.FlexGridSizer(3, 2, 0, 2)
        main_sizer.Add((20, 10), 0, wx.ALL|wx.EXPAND, 0)

        grid_sizer_1.Add(self.img_title_label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5)
        grid_sizer_1.Add(self.img_title_text_ctrl, 1, wx.ALL|wx.SHAPED, 5)
        grid_sizer_1.Add(self.img_dir_label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5)
        grid_sizer_1.Add(self.dir_picker, 0, wx.ALL|wx.EXPAND|wx.ALIGN_RIGHT, 5)
        grid_sizer_1.Add(self.img_desc_label, 0, wx.ALL|wx.ALIGN_TOP|wx.ALIGN_RIGHT, 5)
        grid_sizer_1.Add(self.img_desc_text_ctrl, 1, wx.ALL|wx.EXPAND, 5)

        grid_sizer_1.Add(self.repos_label, 0, wx.ALL|wx.ALIGN_TOP|wx.ALIGN_RIGHT, 5)

        button_sizer = wx.BoxSizer(wx.VERTICAL)
        button_sizer.Add(self.add_repo_button, 0, wx.ALL, 10)
        button_sizer.Add(self.edit_repo_button, 0, wx.ALL, 10)
        button_sizer.Add(self.remove_repo_button, 0, wx.ALL, 10)

        self.repo_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.repo_sizer.Add(self.pub_list_ctrl, 1, wx.ALL|wx.EXPAND, 0)
        self.repo_sizer.Add(button_sizer, 0, wx.ALL, 0)

        grid_sizer_1.Add(self.repo_sizer, 1, wx.ALL|wx.EXPAND, 5)

        self.panel_1.SetSizer(grid_sizer_1)
        grid_sizer_1.AddGrowableRow(3)
        grid_sizer_1.AddGrowableCol(1)
        main_sizer.Add(self.panel_1, 1, wx.ALL|wx.EXPAND, 5)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()
        if self._newsw_install:
            cancel_tip = _("Do not install software")
            ok_tip = _("Confirm installation details")
        elif self._install:
            cancel_tip = _("Do not install software")
            ok_tip = _("Install software")
        elif self._opname == "image-edit":
            cancel_tip = _("Do not update image properties")
            ok_tip = _("Update image properties")
        else:
            cancel_tip = _("Do not create the image")
            ok_tip = _("Create the image")
        bpanel, dummy1, btn_ok = dialogs.make_std_dlg_btn_szr_panel(self, (
                (wx.ID_CANCEL, _("&Cancel"), cancel_tip),
                (wx.ID_OK, _("&OK"), ok_tip),
                ))
        main_sizer.Add(bpanel, 0, wx.ALL|wx.ALIGN_RIGHT, 10)
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()
        if self._image is None:    # New Image
            self.Bind(wx.EVT_BUTTON, self.OnValidate, btn_ok)


    def OnPubListChanged(self, event):
        if event.data is not None:
            self.edit_publisher(event.data)
        self._set_buttons_state()


    def OnValidate(self, event):
        assert event.GetId() == wx.ID_OK

        chosen_dir = self.get_directory()
        pubs = self.get_pubs()
        if not pubs:
            wx.MessageBox(_("You must specify at least one publisher."),
                    style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
            return

        if chosen_dir.strip() == u"":
            wx.MessageBox(_("You must select a directory for the new image"),
                    style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)

            return

        chosen_dir = os.path.expanduser(chosen_dir)

        # Bail if the directory exists but isn't empty
        if os.path.exists(fsenc(chosen_dir)) and len(os.listdir(fsenc(chosen_dir))) > 0:
            wx.MessageBox(_("The selected directory is not empty. No action was performed."), \
                    style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Non-empty directory"), parent=self)
            return
        event.Skip()


    def _set_buttons_state(self):
        cnt = self.pub_list_ctrl.GetSelectedItemCount()
        if cnt:
            idx = self.pub_list_ctrl.GetFirstSelected()
            isp = self.pub_list_ctrl.is_preferred(idx)
            self.edit_repo_button.Enable(True)
            self.remove_repo_button.Enable(not isp)
        else:
            self.edit_repo_button.Enable(False)
            self.remove_repo_button.Enable(False)


    def OnItemSelected(self, dummy_event):
        self._set_buttons_state()


    def OnItemDeselected(self, dummy_evt):
        self._set_buttons_state()


    def OnDirSelection(self, dummy_event):
        dlg = wx.DirDialog(self, _("Choose or create the directory:"), style=wx.DD_DEFAULT_STYLE)
        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it.
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            # User did not select an image directory
            return

        chosen = dlg.GetPath()

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()

        self.dir_picker.SetPath(chosen)


    def get_image_title(self):
        return utils.protect_unicode(self.img_title_text_ctrl.GetValue())


    def set_image_title(self, title):
        self.img_title_text_ctrl.SetValue(title)


    def get_image_description(self):
        return utils.protect_unicode(self.img_desc_text_ctrl.GetValue(), ".")


    def set_image_description(self, description):
        self.img_desc_text_ctrl.SetValue(description)


    def get_directory(self):
        return self.dir_picker.GetPath()


    def get_pubs(self):
        # XXX : Return the first publisher name for now
        return self.pub_list_ctrl.get_pubs()


    def set_pubs(self, pubs):
        """
        Set publishers. 'pubs' is a list of publishers. Each publisher
        is a list of the following items:
        [name, url, preferred, ssl_key, ssl_cert, disabled]
        """
        if pubs == None:
            return
        for a in pubs:
            if a != None:
                self.pub_list_ctrl._add_pub_item(a[0], a[1], a[2], a[3], a[4], a[5])


    def set_path(self, u_path, focus=False):
        """Mimics DirDialog.SetPath(...)"""
        if u_path:
            self.dir_picker.SetPath(u_path)
            if focus:
                self.dir_picker.SetFocus()


    def OnRepoAdd(self, event):
        event.Skip()

        _msg = _url = _pub = _ssl_key = _ssl_cert = ""
        _disabled = False
        dlg = RepoHelperDialog(self, url=_url, name=_pub, ssl_key=_ssl_key, ssl_cert=_ssl_cert, disabled=_disabled, edit=False)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        _url = str(dlg.get_repo_url().strip())
        _pub = fsenc(dlg.get_repo_name().strip())
        _ssl_key = fsenc(dlg.get_ssl_key().strip())
        _ssl_cert = fsenc(dlg.get_ssl_cert().strip())
        dlg.Destroy()

        pubs = self.get_pubs()
        existing_pub_names = [a[0] for a in pubs]
        if _pub in existing_pub_names:
            idx = existing_pub_names.index(_pub)
            _prefer = pubs[idx][2]
        elif pubs:
            _prefer = False
        else:  # first item being added, make it preferred
            _prefer = True

        if _ssl_key == '':
            _ssl_key = None
        if _ssl_cert == '':
            _ssl_cert = None
        self.pub_list_ctrl._add_pub_item(_pub, _url, _prefer, _ssl_key, _ssl_cert, _disabled)


    def OnRepoEdit(self, event):
        if event != None:
            event.Skip()
        self.edit_publisher(None)


    def edit_publisher(self, item):

        if (item == None):
            item = self.pub_list_ctrl.GetFirstSelected()

        if item == -1:
            wx.MessageBox(_("Please select a publisher to edit first."), style=wx.OK|wx.ICON_EXCLAMATION|wx.CENTER, caption=_("Publisher editing"), parent=self)
            return
        opub, ourl, prefer, ossl_key, ossl_cert, odisabled  = self.get_pubs()[item]
        _pub, _url, _ssl_key, _ssl_cert, _disabled = opub, ourl, ossl_key, ossl_cert, odisabled
        dlg = RepoHelperDialog(self, url=_url, name=_pub, ssl_key=_ssl_key, ssl_cert=_ssl_cert, disabled=_disabled, edit=True)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        _url = str(dlg.get_repo_url().strip())
        _pub = fsenc(dlg.get_repo_name().strip())
        _ssl_key = fsenc(dlg.get_ssl_key().strip())
        _ssl_cert = fsenc(dlg.get_ssl_cert().strip())
        dlg.Destroy()

        if _ssl_key == '':
            _ssl_key = None
        if _ssl_cert == '':
            _ssl_cert = None
        self.pub_list_ctrl._replace_pub_item(opub, ourl, prefer, ossl_key, ossl_cert, odisabled,
                                               _pub, _url, prefer, _ssl_key, _ssl_cert, _disabled)


    def OnRepoRemove(self, dummy_event):
        item = self.pub_list_ctrl.GetFirstSelected()
        if item == -1:
            wx.MessageBox(_("Please select a publisher to remove first."),
                    style=wx.OK|wx.ICON_EXCLAMATION|wx.CENTER, caption=_("Publisher removal"), parent=self)
            return

        ret = wx.MessageBox(_("Are you sure you want to remove this publisher from the image?"),
                style=wx.YES|wx.NO|wx.YES_DEFAULT|wx.ICON_QUESTION|wx.CENTER, caption=_("Publisher removal"),
                parent=self)
        if ret != wx.YES:
            return
        ret, res = self.pub_list_ctrl.remove_pub_item(item)
        if not ret:
            wx.MessageBox(res, style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Publisher removal"), parent=self)
            return


    def OnRepoPrefer(self, dummy_event):
        item = self.pub_list_ctrl.GetFirstSelected()
        if item == -1:
            wx.MessageBox(_("Please select a publisher to mark preferred first."), style=wx.OK|wx.ICON_EXCLAMATION|wx.CENTER, caption=_("Preferred Publisher"), parent=self)
            return

        ret, res = self.pub_list_ctrl.prefer_pub_item(item)
        if not ret:
            wx.MessageBox(res, style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Preferred Publisher"), parent=self)
            return

# end of class ImageCreateEditDialog
