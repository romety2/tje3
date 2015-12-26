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

if False:    # Keep Pylint happy
    import gettext
    _ = gettext.gettext


import wx
from wx.lib.intctrl import IntCtrl
import ConfigParser
import dialogs
from common import utils, preferences
import notifier.manage as nt_manage
import re

# Dictionary which maps freq option to radio box positions
CHECK_FREQ_DICT = { 'never':   9,
                    'daily':   0,
                    'weekly':  1,
                    'monthly': 2,
                    9:         'never',
                    0:         'daily',
                    1:         'weekly',
                    2:         'monthly'}

class PreferencesDialog(wx.Dialog):

    _ = wx.GetTranslation

    def __init__(self, *args, **kwds):
        # begin wxGlade: PreferencesDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.pref_notebook = wx.Notebook(self, -1, style=0)
        self.pref_notebook_notifier_pane = wx.Panel(self.pref_notebook, -1)
        self.pref_notebook_network_pane = wx.Panel(self.pref_notebook, -1)
        self.pref_notebook_view_pane = wx.Panel(self.pref_notebook, -1)

        self.label_proxy_setting = wx.StaticText(self.pref_notebook_network_pane, -1, _("Proxy Settings"))
        self.radiobutton_direct_conn = wx.RadioButton(self.pref_notebook_network_pane, -1, _("Direct connection to the Internet"), style=wx.RB_GROUP)
        self.radiobutton_proxy_conn = wx.RadioButton(self.pref_notebook_network_pane, -1, _("Manual proxy configuration"))
        self.label_http_proxy_host = wx.StaticText(self.pref_notebook_network_pane, -1, _("HTTP Proxy:"))
        self.text_ctrl_http_proxy = wx.TextCtrl(self.pref_notebook_network_pane, -1, "")
        self.label_http_proxy_port = wx.StaticText(self.pref_notebook_network_pane, -1, _("Port:"))
        if wx.Platform == "__WXMAC__":
            # XXX : Workaround for issue 267 till the red color field bug on
            # Mac gets fixed. The bug happens because pure black is treated as
            # a special flag color on Mac by wxPython (as per Robin Dunn of
            # wxPython)
            int_ctrl_color = wx.Colour(0, 0, 1)
        else:
            int_ctrl_color = wx.Colour(0, 0, 0)
        self.int_ctrl_http_proxy_port = IntCtrl(self.pref_notebook_network_pane, -1, value=0, min=0, max=65535, limited = True, \
                default_color=int_ctrl_color, style=wx.TE_NOHIDESEL|wx.TE_RIGHT)
        self.panel_1 = wx.StaticText(self.pref_notebook_network_pane, -1)
        self.panel_2 = wx.StaticText(self.pref_notebook_network_pane, -1)
        self.checkbox_http_proxy_for_all = wx.CheckBox(self.pref_notebook_network_pane, -1, _("Use the HTTP proxy server for SSL"))
        self.label_ssl_proxy = wx.StaticText(self.pref_notebook_network_pane, -1, _("SSL Proxy:"))
        self.text_ctrl_ssl_proxy_host = wx.TextCtrl(self.pref_notebook_network_pane, -1, "")
        self.label_ssl_proxy_port = wx.StaticText(self.pref_notebook_network_pane, -1, _("Port:"))
        self.int_ctrl_ssl_proxy_port = IntCtrl(self.pref_notebook_network_pane, -1, value=0, min=0, max=65535, limited = True, \
                default_color=int_ctrl_color, style=wx.TE_NOHIDESEL|wx.TE_RIGHT)
        self.label_no_proxy = wx.StaticText(self.pref_notebook_network_pane, -1, _("No Proxy for:"))
        self.text_ctrl_no_proxy = wx.TextCtrl(self.pref_notebook_network_pane, -1, "")
        self.static_text_no_proxy = wx.StaticText(self.pref_notebook_network_pane, -1, _("(Example: localhost, *.sun.com, 127.0.0.1)"))
        self.checkbox_proxies_need_auth = wx.CheckBox(self.pref_notebook_network_pane, -1, _("Proxy Requires Authentication"))
        self.label_username = wx.StaticText(self.pref_notebook_network_pane, -1, _("Username:"), style=wx.ALIGN_RIGHT)
        self.text_ctrl_proxy_username = wx.TextCtrl(self.pref_notebook_network_pane, -1, "")
        self.label_password = wx.StaticText(self.pref_notebook_network_pane, -1, _("Password:"), style=wx.ALIGN_RIGHT)
        self.text_ctrl_proxy_password = wx.TextCtrl(self.pref_notebook_network_pane, -1, "", style=wx.TE_PASSWORD)
        self.label_warning = wx.StaticText(self.pref_notebook_network_pane, -1, _("If you enter a proxy password it will be stored in a file in \
your home folder as plain text. \nIf you do not enter a proxy password here then you will be \
prompted for the password\neach time you start Update Tool, \
and you will not receive automatic notifications of \nupdates."), style=wx.ALIGN_LEFT)

        self.checkbox_auto_update_check = wx.CheckBox(self.pref_notebook_notifier_pane, -1, _("Automatically check for updates"))
        self.label_update_frequency = wx.StaticText(self.pref_notebook_notifier_pane, -1, _("Frequency to check for updates:"))
        self.radiobutton_update_daily = wx.RadioButton(self.pref_notebook_notifier_pane, -1, _("Daily"), style=wx.RB_GROUP)
        self.radiobutton_update_weekly = wx.RadioButton(self.pref_notebook_notifier_pane, -1, _("Weekly"))
        self.radiobutton_update_monthly = wx.RadioButton(self.pref_notebook_notifier_pane, -1, _("Monthly"))

        self.label_recent_versions = wx.StaticText(self.pref_notebook_view_pane, -1, _("Show Recent Versions"))
        self.recent_count_btn = wx.RadioButton(self.pref_notebook_view_pane, -1, _("Maximum number of recent versions to show:"), style=wx.RB_GROUP)
        self.recent_unlimit_rbtn = wx.RadioButton(self.pref_notebook_view_pane, -1, _("Show all versions"))
        self.recent_int_ctrl = IntCtrl(self.pref_notebook_view_pane, -1, value=2, min=1, max=preferences.MAX_RECENT_ITEMS, limited = True, \
                default_color=int_ctrl_color, style=wx.TE_NOHIDESEL|wx.TE_RIGHT)
        self.recent_int_ctrl.Enable(False)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_RADIOBUTTON, self.OnProxyRadioButtonEvent, self.radiobutton_direct_conn)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnProxyRadioButtonEvent, self.radiobutton_proxy_conn)
        self.Bind(wx.EVT_CHECKBOX, self.OnUseHttpProxyForSSL, self.checkbox_http_proxy_for_all)
        self.Bind(wx.EVT_CHECKBOX, self.OnProxiesRequireAuth, self.checkbox_proxies_need_auth)
        self.Bind(wx.EVT_CHECKBOX, self.OnAutoUpdateCheckEvent, self.checkbox_auto_update_check)
        self.Bind(wx.EVT_TEXT, self.OnHttpProxyCharEvent, self.text_ctrl_http_proxy)
        self.Bind(wx.EVT_TEXT, self.OnHttpPortIntEvent, self.int_ctrl_http_proxy_port)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRecentViewLimit, self.recent_unlimit_rbtn)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRecentViewLimit, self.recent_count_btn)
        # end wxGlade
        self.Centre()
        self.radiobutton_direct_conn.SetFocus()


    def __set_properties(self):
        # begin wxGlade: PreferencesDialog.__set_properties
        self.SetTitle(_("Preferences"))
        self.radiobutton_direct_conn.SetValue(True)
        self.label_http_proxy_host.Enable(False)
        self.text_ctrl_http_proxy.SetToolTipString(_("IP address or host name of the http proxy server"))
        self.text_ctrl_http_proxy.Enable(False)
        self.text_ctrl_http_proxy.SetMinSize((350, -1))
        self.label_http_proxy_port.Enable(False)
        self.int_ctrl_http_proxy_port.SetToolTipString(_("Port number of the HTTP proxy server"))
        self.int_ctrl_http_proxy_port.Enable(False)
        self.int_ctrl_http_proxy_port.SetMinSize((40, -1))
        self.checkbox_http_proxy_for_all.Enable(False)
        self.label_ssl_proxy.Enable(False)
        self.text_ctrl_ssl_proxy_host.SetToolTipString(_("IP address or host name of the https/ssl proxy server"))
        self.text_ctrl_ssl_proxy_host.Enable(False)
        self.text_ctrl_ssl_proxy_host.SetMinSize((350, -1))
        self.label_ssl_proxy_port.Enable(False)
        self.int_ctrl_ssl_proxy_port.SetToolTipString(_("Port number of the HTTPS/SSL proxy server"))
        self.int_ctrl_ssl_proxy_port.Enable(False)
        self.int_ctrl_ssl_proxy_port.SetMinSize((40, -1))
        self.label_no_proxy.Enable(False)
        self.text_ctrl_no_proxy.SetToolTipString(_("(Not Implemented) Comma separated list of hosts and domains that will not be contacted through the proxy"))
        self.text_ctrl_no_proxy.Enable(False)
        self.static_text_no_proxy.Enable(False)
        self.checkbox_proxies_need_auth.Enable(False)
        self.label_username.Enable(False)
        self.text_ctrl_proxy_username.SetMinSize((150, -1))
        self.text_ctrl_proxy_username.SetToolTipString(_("User name to use with the proxies"))
        self.text_ctrl_proxy_username.Enable(False)
        self.label_password.Enable(False)
        self.text_ctrl_proxy_password.SetMinSize((150, -1))
        self.text_ctrl_proxy_password.SetToolTipString(_("Password to use with the proxies"))
        self.text_ctrl_proxy_password.Enable(False)
        self.checkbox_auto_update_check.SetToolTipString(_("Controls whether the desktop update notifier will be started automatically at log in."))
        self.checkbox_auto_update_check.SetValue(True)
        self.radiobutton_update_daily.SetToolTipString(_("Controls the frequency the notifier checks for new updates"))
        self.radiobutton_update_weekly.SetToolTipString(_("Controls the frequency the notifier checks for new updates"))
        self.radiobutton_update_monthly.SetToolTipString(_("Controls the frequency the notifier checks for new updates"))
        self.radiobutton_update_daily.SetValue(True)
        self.recent_count_btn.SetToolTipString(_("Show at most this number of recent versions of components when Show Recent Versions is in effect."))
        self.recent_int_ctrl.SetToolTipString(_("Maximum number of recent versions."))
        self.recent_unlimit_rbtn.SetToolTipString(_("Show all versions of components when Show Recent Versions is in effect."))
        # end wxGlade


    def __do_layout(self):
        # begin wxGlade: PreferencesDialog.__do_layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        sizer_network_pane = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_3 = wx.FlexGridSizer(2, 1, 5, 5)
        grid_sizer_4 = wx.FlexGridSizer(2, 2, 5, 5)
        grid_sizer_1 = wx.FlexGridSizer(5, 2, 0, 0)
        grid_sizer_2_copy = wx.FlexGridSizer(1, 3, 0, 0)
        grid_sizer_2 = wx.FlexGridSizer(1, 3, 0, 0)
        grid_sizer_5 = wx.FlexGridSizer(1, 1, 0, 0)
        sizer_network_pane.Add(self.label_proxy_setting, 0, wx.ALL, 5)
        sizer_network_pane.Add(self.radiobutton_direct_conn, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        sizer_network_pane.Add(self.radiobutton_proxy_conn, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        grid_sizer_1.Add(self.label_http_proxy_host, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_2.Add(self.text_ctrl_http_proxy, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_2.Add(self.label_http_proxy_port, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_2.Add(self.int_ctrl_http_proxy_port, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_2.AddGrowableCol(0)
        grid_sizer_1.Add(grid_sizer_2, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.checkbox_http_proxy_for_all, 0, wx.ALL, 5)
        grid_sizer_1.Add(self.label_ssl_proxy, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_2_copy.Add(self.text_ctrl_ssl_proxy_host, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_2_copy.Add(self.label_ssl_proxy_port, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_2_copy.Add(self.int_ctrl_ssl_proxy_port, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_2_copy.AddGrowableCol(0)
        grid_sizer_1.Add(grid_sizer_2_copy, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.label_no_proxy, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_1.Add(self.text_ctrl_no_proxy, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_1.Add(self.panel_2, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.static_text_no_proxy, 1, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 5)

        # Hide these since we don't support this yet. Bug 1017
        grid_sizer_1.Hide(self.label_no_proxy)
        grid_sizer_1.Hide(self.text_ctrl_no_proxy)
        grid_sizer_1.Hide(self.static_text_no_proxy)

        grid_sizer_1.AddGrowableCol(1)
        sizer_network_pane.Add(grid_sizer_1, 1, wx.LEFT|wx.EXPAND, 20)
        grid_sizer_5.AddGrowableCol(0)
        sizer_network_pane.Add(grid_sizer_5, 0, wx.LEFT|wx.EXPAND, 20)
        grid_sizer_3.Add(self.checkbox_proxies_need_auth, 0, wx.LEFT|wx.TOP, 5)
        grid_sizer_4.Add(self.label_username, 0, wx.LEFT|wx.BOTTOM|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_4.Add(self.text_ctrl_proxy_username, 1, wx.LEFT|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)
        grid_sizer_4.Add(self.label_password, 0, wx.LEFT|wx.BOTTOM|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_4.Add(self.text_ctrl_proxy_password, 1, wx.LEFT|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)
        grid_sizer_3.Add(grid_sizer_4, 1, wx.TOP|wx.BOTTOM|wx.EXPAND, 3)
        grid_sizer_3.Add(self.label_warning, 0, wx.LEFT|wx.BOTTOM|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer_network_pane.Add(grid_sizer_3, 0, wx.LEFT|wx.EXPAND, 20)
        self.pref_notebook_network_pane.SetSizer(sizer_network_pane)

        sizer_notifier_pane = wx.BoxSizer(wx.VERTICAL)
        sizer_notifier_pane.Add(self.checkbox_auto_update_check, 0, wx.ALL, 5)
        sizer_notifier_pane.Add(self.label_update_frequency, 0, wx.TOP|wx.LEFT, 5)
        sizer_notifier_pane.Add(self.radiobutton_update_daily, 0, wx.TOP|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        sizer_notifier_pane.Add(self.radiobutton_update_weekly, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        sizer_notifier_pane.Add(self.radiobutton_update_monthly, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        self.pref_notebook_notifier_pane.SetSizer(sizer_notifier_pane)

        sizer_view_pane = wx.BoxSizer(wx.VERTICAL)
        sizer_view_pane.Add(self.label_recent_versions, 0, wx.ALL, 5)
        grid_sizer_view_pane = wx.FlexGridSizer(2, 2, 0, 0)
        grid_sizer_view_pane.Add(self.recent_count_btn, 0, 0, 0)
        grid_sizer_view_pane.Add(self.recent_int_ctrl, 0, wx.LEFT, 5)
        grid_sizer_view_pane.Add(self.recent_unlimit_rbtn, 0, 0, 0)
        sizer_view_pane.Add(grid_sizer_view_pane, 0, wx.LEFT, 5)
        self.pref_notebook_view_pane.SetSizer(sizer_view_pane)

        self.pref_notebook.AddPage(self.pref_notebook_network_pane, _("Network"))
        self.pref_notebook.AddPage(self.pref_notebook_notifier_pane, _("Updates"))
        self.pref_notebook.AddPage(self.pref_notebook_view_pane, _("View"))
        main_sizer.Add(self.pref_notebook, 7, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Layout()
        # end wxGlade
        bpanel, self.cancel_button, self.ok_button = \
                dialogs.make_std_dlg_btn_szr_panel(self, (
                    (wx.ID_CANCEL, _("&Cancel"), _("Cancel application of any unsaved changes and close this dialog box")),
                    (wx.ID_OK, _("&OK"), _("Apply any changes and close this dialog box")),
                    ))
        main_sizer.Add(bpanel, 0, wx.ALL|wx.ALIGN_RIGHT, 10)
        main_sizer.Fit(self)
        self.Layout()


    def OnPrefEvent(self, event):
        if event.GetId() == wx.ID_OK or event.GetId() == wx.ID_APPLY:
            # Validate the proxy settings.  If we find any missing information
            # we present a dialog informing the user.
            result = self.validate_proxy_settings()
            msg = _("The proxy settings are incomplete.\n\nA manual proxy configuration "\
                    "has been selected but some required information is missing. "\
                    "Please review the current settings.")
            if not result[0]:
                if len(result[1]) != 0:
                    msg = result[1]
                wx.MessageBox(msg, style=wx.OK|wx.ICON_INFORMATION|wx.CENTER,
                                 caption=_("Preferences: Proxy Settings"),
                                 parent=self)

                return

            self.update_notifier_op_state(self.image_path)
            self.store_prefs()
        else:
            pass
        event.Skip()


    def OnProxyRadioButtonEvent(self, dummy_event): # wxGlade: PreferencesDialog.<event_handler>
        #Turn on or off the proxy controls based on the radio box selection.
        self.proxy_controls(self.radiobutton_proxy_conn.GetValue())


    def OnRecentViewLimit(self, event): # wxGlade: PreferencesDialog.<event_handler>
        #Turn on or off the proxy controls based on the radio box selection.
        # self.proxy_controls(self.radiobutton_proxy_conn.GetValue())
        utils.logger.debug("OnRecentViewLimit")
        sel = event.GetEventObject()
        if sel == self.recent_unlimit_rbtn:
            utils.logger.debug("Unlimit")
            self.recent_int_ctrl.Enable(False)
        elif sel == self.recent_count_btn:
            utils.logger.debug("Limit")
            self.recent_int_ctrl.Enable(True)
        else:
            wx.MessageBox("This should not happen!", style=wx.OK|wx.ICON_INFORMATION|wx.CENTER, caption=_("Error"), parent=self)
        event.Skip()


    def proxy_controls(self, on=False):
        self.label_http_proxy_host.Enable(on)
        self.text_ctrl_http_proxy.Enable(on)
        self.label_http_proxy_port.Enable(on)
        self.int_ctrl_http_proxy_port.Enable(on)
        self.checkbox_http_proxy_for_all.Enable(on)
        self.label_ssl_proxy.Enable(on)
        self.text_ctrl_ssl_proxy_host.Enable(on)
        self.label_ssl_proxy_port.Enable(on)
        self.int_ctrl_ssl_proxy_port.Enable(on)
        self.label_no_proxy.Enable(on)
        self.text_ctrl_no_proxy.Enable(on)
        self.static_text_no_proxy.Enable(on)
        self.checkbox_proxies_need_auth.Enable(on)
        self._proxies_require_auth_helper(on and self.checkbox_proxies_need_auth.IsChecked())


    def set_prefs_action_handler(self, action_handler):

        # This order will cause the PreferencesDialog's handler to be
        # called before the GUI/Notifier's event handler.
        self.Bind(wx.EVT_BUTTON, action_handler, self.ok_button)

        self.Bind(wx.EVT_BUTTON, self.OnPrefEvent, self.ok_button)


    def set_config(self, config, image_path):
        self.config = config
        self.image_path = image_path

        #XXX: This code needs to be improved to handle the cases where the
        #     options or section don't exist in the prefs file.

        on = False
        if config.getboolean('network', 'proxy.required'):
            self.proxy_controls(True)
            self.radiobutton_proxy_conn.SetValue(True)
            on = True
        else:
            self.radiobutton_direct_conn.SetValue(True)
            on = False

        try:
            self.text_ctrl_http_proxy.SetValue(
                                        config.get('network', 'proxy.host'))
        except ConfigParser.NoOptionError, e:
            #It is not an error at this level if the host and/or port are
            #missing.
            pass

        try:
            port_str = config.get('network', 'proxy.port')
            if port_str.isdigit():
                self.int_ctrl_http_proxy_port.SetValue(int(port_str))
        except ConfigParser.NoOptionError, e:
            #It is not an error at this level if the host and/or port are
            #missing.
            pass

        try:
            self.text_ctrl_ssl_proxy_host.SetValue(
                                        config.get('network', 'proxy.https.host'))
        except ConfigParser.NoOptionError, e:
            #It is not an error at this level if the host and/or port are
            #missing.
            pass

        try:
            port_str = config.get('network', 'proxy.https.port')
            if port_str.isdigit():
                self.int_ctrl_ssl_proxy_port.SetValue(int(port_str))
        except ConfigParser.NoOptionError, e:
            #It is not an error at this level if the host and/or port are
            #missing.
            pass

        flag = config.getboolean('network', 'proxy.ssl_use_http')
        self.checkbox_http_proxy_for_all.SetValue(flag)
        if flag:
            self.label_ssl_proxy.Enable(False)
            self.text_ctrl_ssl_proxy_host.Enable(False)
            self.label_ssl_proxy_port.Enable(False)
            self.int_ctrl_ssl_proxy_port.Enable(False)
            self.text_ctrl_ssl_proxy_host.SetValue(self.text_ctrl_http_proxy.GetValue())
            self.int_ctrl_ssl_proxy_port.SetValue(self.int_ctrl_http_proxy_port.GetValue())

        flag = config.getboolean('network', 'proxy.auth')

        self.checkbox_proxies_need_auth.SetValue(flag)
        self._proxies_require_auth_helper(flag and on)

        try:
            self.text_ctrl_proxy_username.SetValue(
                                        config.get('network', 'proxy.username'))
        except ConfigParser.NoOptionError, e:
            #It is not an error at this level if the user and/or pass are
            #missing.
            pass

        try:
            self.text_ctrl_proxy_password.SetValue(
                    config.get('network', 'proxy.password'))
        except ConfigParser.NoOptionError, e:
            #It is not an error at this level if the user and/or pass are
            #missing.
            pass

        try:
            self.text_ctrl_no_proxy.SetValue(
                                config.get('network', 'proxy.no_proxy_list'))
        except ConfigParser.NoOptionError, e:
            #It is not an error at this level if the no proxy list is
            #missing.
            pass

        try:
            limit = config.get('main', 'maximum_recent_items')
            if limit.isdigit():
                limit = int(limit)
                if limit > preferences.MAX_RECENT_ITEMS:
                    limit = preferences.MAX_RECENT_ITEMS
                self.recent_int_ctrl.SetValue(limit)
                self.recent_int_ctrl.Enable(True)
                self.recent_count_btn.Enable(True)
                self.recent_count_btn.SetValue(True)
                self.recent_unlimit_rbtn.Enable(True)
                self.recent_unlimit_rbtn.SetValue(False)
            else:
                self.recent_int_ctrl.SetValue(int(preferences.get_default('main', 'maximum_recent_items', '3')))
                self.recent_int_ctrl.Enable(False)
                self.recent_count_btn.Enable(True)
                self.recent_count_btn.SetValue(False)
                self.recent_unlimit_rbtn.Enable(True)
                self.recent_unlimit_rbtn.SetValue(True)
        except ConfigParser.NoOptionError, e:
            utils.logger.error("Exception while getting maximum_recent_items from config")
            self.recent_int_ctrl.SetValue(int(preferences.get_default('main', 'maximum_recent_items', '3')))
            self.recent_int_ctrl.Enable(False)
            self.recent_count_btn.Enable(True)
            self.recent_count_btn.SetValue(False)
            self.recent_unlimit_rbtn.Enable(True)
            self.recent_unlimit_rbtn.SetValue(True)

        self.set_update_prefs()


    def set_update_prefs(self):

        try:
            freq = self.config.get('notifier', 'check_frequency')
        except ConfigParser.NoOptionError, e:
            # Default to weekly if the option is not set.
            freq = 'weekly'

        # If the property is valid use it
        if CHECK_FREQ_DICT.has_key(freq):
            if freq == 'never':
                self.radiobutton_update_daily.Enable(False)
                self.radiobutton_update_weekly.Enable(False)
                self.radiobutton_update_monthly.Enable(False)
                self.set_update_radio_selection(CHECK_FREQ_DICT['daily'])
                self.checkbox_auto_update_check.SetValue(False)
            else:
                self.radiobutton_update_daily.Enable(True)
                self.radiobutton_update_weekly.Enable(True)
                self.radiobutton_update_monthly.Enable(True)
                self.checkbox_auto_update_check.SetValue(True)
                self.set_update_radio_selection(CHECK_FREQ_DICT[freq])
        # If the property is not valid default to weekly
        else:
            self.radiobutton_update_daily.Enable(True)
            self.radiobutton_update_weekly.Enable(True)
            self.radiobutton_update_monthly.Enable(True)
            self.set_update_radio_selection(CHECK_FREQ_DICT['weekly'])
            self.checkbox_auto_update_check.SetValue(True)


    def set_update_radio_selection(self, freq=0):
        if freq == CHECK_FREQ_DICT['daily']:
            self.radiobutton_update_daily.SetValue(True)
        elif freq == CHECK_FREQ_DICT['weekly']:
            self.radiobutton_update_weekly.SetValue(True)
        elif freq == CHECK_FREQ_DICT['monthly']:
            self.radiobutton_update_monthly.SetValue(True)
        else :
            utils.logger.debug("set_update_radio_selection passed an invalid value: " + str(freq))
            return


    def get_radio_update_selection(self):
        if self.radiobutton_update_daily.GetValue():
            return CHECK_FREQ_DICT['daily']
        elif self.radiobutton_update_weekly.GetValue():
            return CHECK_FREQ_DICT['weekly']
        elif self.radiobutton_update_monthly.GetValue():
            return CHECK_FREQ_DICT['monthly']
        else:
            return CHECK_FREQ_DICT['never']


    def validate_proxy_settings(self):
        """
        Determine if any required proxy settings are valid or not.
        """

        msg = ""
        # pattern to check for valid IP address.
        pattern_ip = "^([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\." \
            "([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\." \
            "([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\." \
            "([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"

        # pattern to check for valid hostname.
        pattern_host = "^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*" \
            "([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$"

        # Determine if a proxy is required
        if self.radiobutton_proxy_conn.GetValue():
            # Check the proxy host
            if len(self.text_ctrl_http_proxy.GetValue().strip()) == 0:
                msg = _("Manual proxy configuration has been selected "\
                        "but HTTP Proxy information is missing.")
                return (False, msg)

            if len(self.text_ctrl_http_proxy.GetValue().strip()) != 0:
                host = self.text_ctrl_http_proxy.GetValue().strip()
                pattern_result = re.match(pattern_ip, host)
                pattern1_result = re.match(pattern_host, host)
                if pattern_result == None and pattern1_result == None:
                    return (False, "Please enter a valid value for HTTP Proxy.")

            if self.int_ctrl_http_proxy_port.GetValue() == 0:
                return (False, _("Please enter a valid value for HTTP Proxy port."))

            if len(self.text_ctrl_ssl_proxy_host.GetValue().strip()) != 0:
                host = self.text_ctrl_ssl_proxy_host.GetValue().strip()
                pattern_result = re.match(pattern_ip, host)
                pattern1_result = re.match(pattern_host, host)
                if pattern_result == None and pattern1_result == None:
                    return(False, "Please enter a valid value for SSL Proxy.")

            if ((len(self.text_ctrl_ssl_proxy_host.GetValue().strip()) != 0) and
                (self.int_ctrl_ssl_proxy_port.GetValue() == 0)):
                return (False, _("Please enter a valid value for SSL Proxy port."))

            if self.checkbox_proxies_need_auth.IsChecked():
                if len(self.text_ctrl_proxy_username.GetValue().strip()) == 0:
                    return(False, _("Proxy requires authentication is selected but the user name is missing."))

        return (True, msg)


    def store_prefs(self):
        #The user has pressed Apply or OK. We must now walk the Preferences'
        #controls and update the ConfigParser.  Then we can write the
        #user prefs.

        #Main Pane
        #No Prefs to store yet.

        #Network Pane
        if not self.config.has_section('network'):
            self.config.add_section('network')
        if self.radiobutton_proxy_conn.GetValue():
            self.config.set('network', 'proxy.required', 'True')
        else:
            self.config.set('network', 'proxy.required', 'False')

        if len(self.text_ctrl_http_proxy.GetValue()):
            self.config.set('network', 'proxy.host',
                                        self.text_ctrl_http_proxy.GetValue())
        else:
            self.config.remove_option('network', 'proxy.host')

        if self.int_ctrl_http_proxy_port.GetValue():
            self.config.set('network', 'proxy.port',
                                    str(self.int_ctrl_http_proxy_port.GetValue()))
        else:
            self.config.remove_option('network', 'proxy.port')

        if self.checkbox_http_proxy_for_all.IsChecked():
            self.config.set('network', 'proxy.ssl_use_http', 'True')
        else:
            self.config.set('network', 'proxy.ssl_use_http', 'False')

        if len(self.text_ctrl_ssl_proxy_host.GetValue()):
            self.config.set('network', 'proxy.https.host',
                                        self.text_ctrl_ssl_proxy_host.GetValue())
        else:
            self.config.remove_option('network', 'proxy.https.host')

        if self.int_ctrl_ssl_proxy_port.GetValue():
            self.config.set('network', 'proxy.https.port',
                                    str(self.int_ctrl_ssl_proxy_port.GetValue()))
        else:
            self.config.remove_option('network', 'proxy.https.port')

        if self.checkbox_proxies_need_auth.IsChecked():
            self.config.set('network', 'proxy.auth', 'True')
        else:
            self.config.set('network', 'proxy.auth', 'False')

        if len(self.text_ctrl_proxy_username.GetValue()):
            self.config.set('network', 'proxy.username',
                                        self.text_ctrl_proxy_username.GetValue())
        else:
            self.config.remove_option('network', 'proxy.username')

        if len(self.text_ctrl_proxy_password.GetValue()):
            self.config.set('network', 'proxy.password',
                                        self.text_ctrl_proxy_password.GetValue())
        else:
            self.config.remove_option('network', 'proxy.password')

        if len(self.text_ctrl_no_proxy.GetValue()):
            self.config.set('network', 'proxy.no_proxy_list',
                                        self.text_ctrl_no_proxy.GetValue())
        else:
            self.config.remove_option('network', 'proxy.no_proxy_list')

        # Updates Pane
        if not self.config.has_section('notifier'):
            self.config.add_section('notifier')
        if self.checkbox_auto_update_check.GetValue():
            self.config.set('notifier', 'check_frequency',
                 CHECK_FREQ_DICT[self.get_radio_update_selection()])
        else:
            self.config.set('notifier', 'check_frequency', 'never')

        # View Pane
        if not self.config.has_section('main'):
            self.config.add_section('main')
        if self.recent_unlimit_rbtn.GetValue():
            utils.logger.debug("Setting maximum_recent_items to None")
            self.config.set('main', 'maximum_recent_items', 'None')
        else:
            utils.logger.debug("Setting maximum_recent_items to " + str(self.recent_int_ctrl.GetValue()))
            self.config.set('main', 'maximum_recent_items', str(self.recent_int_ctrl.GetValue()))

        #Save the Preferences to disk
        self.config.save_config()

    # Update the notifier's registration status based on the checkbox
    # selection in the preferences.
    # If the notifier is unregistered then we also send it a shutdown message.
    # If the notifier is registered then we attempt to start it.
    # Attempt to start the notifier if the checkbox is selected.
    # Stop the notifier if the checkbox is not selected.
    def update_notifier_op_state(self, image_path):

        if self.config.get('notifier', 'check_frequency') == 'never' and \
            self.checkbox_auto_update_check.GetValue():
            error_code = nt_manage.register_notifier(image_path, register=True, force=False)
            if error_code and error_code != 1:
                wx.MessageBox(_("Unable to register the desktop notifier.  See the application log for the details."), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                              caption=_("Error"), parent=self)

            # Try to start the notifier.
            # This may silently fail if the notifier is already running.
	    if error_code != 1:
                # See issue 1917
                if error_code == 0:
                    args = '--check-and-exit'
                else:
                    args = ''

                nt_manage.start_notifier(image_path, args)

        elif self.config.get('notifier', 'check_frequency') != 'never' and \
            not self.checkbox_auto_update_check.GetValue():
            error_code = nt_manage.register_notifier(image_path, register=False, force=True)
            if error_code and error_code != 1:
                wx.MessageBox(_("Unable to unregister the desktop notifier.  See the appliation logs for the details."), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                              caption=_("Error"), parent=self)

            import common.ipcservice as ipcservice

            # Send a message to shutdown the notifier.  We do this regardless
            # of whether we could unregister it.
            ipcservice.send_command("nt_lock", "SHUTDOWN")


    def _proxies_require_auth_helper(self, flag):
        self.label_username.Enable(flag)
        self.label_password.Enable(flag)
        self.text_ctrl_proxy_username.Enable(flag)
        self.text_ctrl_proxy_password.Enable(flag)


    def OnUseHttpProxyForSSL(self, event):
        self._use_http_proxy_for_ssl_helper(event.IsChecked())


    def _use_http_proxy_for_ssl_helper(self, flag):
        if flag:
            self.text_ctrl_ssl_proxy_host.SetValue(self.text_ctrl_http_proxy.GetValue())
            self.int_ctrl_ssl_proxy_port.SetValue(self.int_ctrl_http_proxy_port.GetValue())
            self.label_ssl_proxy.Enable(False)
            self.text_ctrl_ssl_proxy_host.Enable(False)
            self.label_ssl_proxy_port.Enable(False)
            self.int_ctrl_ssl_proxy_port.Enable(False)
        else:
            self.text_ctrl_ssl_proxy_host.SetValue("")
            self.int_ctrl_ssl_proxy_port.Clear()
            self.label_ssl_proxy.Enable(True)
            self.text_ctrl_ssl_proxy_host.Enable(True)
            self.label_ssl_proxy_port.Enable(True)
            self.int_ctrl_ssl_proxy_port.Enable(True)


    def OnProxiesRequireAuth(self, event): # wxGlade: PreferencesDialog.<event_handler>
        self._proxies_require_auth_helper(event.IsChecked())


    def _auto_update_check_helper(self, flag):
        self.radiobutton_update_daily.Enable(flag)
        self.radiobutton_update_weekly.Enable(flag)
        self.radiobutton_update_monthly.Enable(flag)


    def OnAutoUpdateCheckEvent(self, event):
        self._auto_update_check_helper(event.IsChecked())


    def OnHttpProxyCharEvent(self, event):
        if self.checkbox_http_proxy_for_all.IsChecked():
            self.text_ctrl_ssl_proxy_host.SetValue(self.text_ctrl_http_proxy.GetValue())


    def OnHttpPortIntEvent(self, event):
        if self.checkbox_http_proxy_for_all.IsChecked():
            self.int_ctrl_ssl_proxy_port.SetValue(self.int_ctrl_http_proxy_port.GetValue())

# end of class PreferencesDialog


if __name__ == "__main__":
    import gettext
    gettext.install("preferencesdialog") # replace with the appropriate catalog name

    preferencesdialog = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    pref_dialog = PreferencesDialog(None, -1, "")
    preferencesdialog.SetTopWindow(pref_dialog)
    pref_dialog.Show()
    preferencesdialog.MainLoop()
