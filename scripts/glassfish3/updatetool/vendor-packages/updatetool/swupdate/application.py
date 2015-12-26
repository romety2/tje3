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

"""Software Update application"""

if False:    # Keep Pylint happy
    import gettext
    _ = gettext.gettext

###############################################################################
####### T H E  O R D E R  O F  I M P O R T S  I S  I M P O R T A N T
###############################################################################

import common.boot as boot
import common.info as INFO
from swupdate.mainframe import MainFrame
from common.fsutils import fsenc

APP_LONG_NAME = INFO.UPDATE_APP_NAME
APP_CMD_NAME = INFO.CMD_NAME
APP_CLIENT_NAME = INFO.UPDATE_CLIENT_NAME

LOG_FILE = "swupdate.log"

import os.path
import sys

import socket

from pkg.client import global_settings

from common import preferences, ipcservice, utils
import wx

class SWUpdateApp(wx.App):
    """The main wx.App"""

    _ = wx.GetTranslation

    def __init__(self, *args, **kwargs):

        self.options = kwargs['options']
        del kwargs['options']

        self.debug = self.options['debug']

        wx.App.__init__(self, *args, **kwargs)
        global_settings.client_name = APP_CLIENT_NAME


    def OnInit(self):

        show_frame = True
        self.options['start_swupdate'] = True

        # XXX: We use "updatetool" here so we can share the same preferences
        # XXX: We could change the Preferences impl to not depend on the
        # XXX: AppName set here.
        wx.GetApp().SetAppName(APP_CMD_NAME) # NOL10N

        # this env var has been set by init_app_locale in main
        localedir = boot.get_locale_dir()
        self.app_locale = wx.Locale(wx.LANGUAGE_DEFAULT, wx.LOCALE_LOAD_DEFAULT)
        self.app_locale.AddCatalogLookupPathPrefix(localedir)
        self.app_locale.AddCatalog(APP_CMD_NAME)

        # This whole block deals with getting a directory where we can log
        # stdout/stderr output from
        # the app. Currently it's the same dir as configuration directory.
        config_dir = utils.get_config_dir()
        if not os.path.exists(config_dir):
            #XXX: What exception could this throw?
            os.makedirs(config_dir)
        # We don't know what encoding the hostname is in.  We guess that 
        # it is latin-1 and if it is not we ignore those characters that 
        # we can't use. 
        hostname = unicode(socket.gethostname(), "latin-1", errors='ignore')
        if hostname == "":
            hostname = "logs"
        host_config_dir = fsenc(os.path.join(config_dir, hostname))
        if not os.path.exists(host_config_dir):
            os.makedirs(host_config_dir)
        utils.host_config_dir = host_config_dir
        if self.options['errors'] == 'logfile':
            log_file_path = os.path.join(config_dir, "error_log.txt")
            #Does the config directory exist?
            if os.path.exists(log_file_path):
                #It exists but it is not a file.  We can't use it.
                if not os.path.isfile(log_file_path):
                    raise Exception(_("Can not create log at '%s'") % log_file_path)
                utils.rotate_file(log_file_path)
            self.RedirectStdio(log_file_path)
            del log_file_path
        elif self.options['errors'] == 'console':
            # By default the output goes to console
            pass

        # Determine if an instance is already running.
        # If it is we can exit.
        if not self.options['force_new_instance'] and \
                                         ipcservice.process_running("swu_lock",
                                                                     show=True):
            # Found a running instance, remember to not start this instance.
            self.options['start_swupdate'] = False

            # If an instance is already running we don't complain to the user
            # when the silent_start option is true.
            if not self.options['silent_start']:
                self.RestoreStdio()
                boot.uc_error(_("%s: The tool is already running.") % APP_LONG_NAME, 1)

                # Set a flag so that we don't show the Frame.  For this type
                # of error message we don't want the user to see the Frame.
                show_frame = False

            else:
                sys.exit(1)

            # On non-Windows platforms we should not get here because uc_error
            # will call sys.exit.  On Windows we continue on.  Later in this
            # method there is a flag that triggers the error dialog and
            # sys.exit.  We have to delay until the frame is created.

        config_dir = utils.get_config_dir()

        # Load initial config
        self.config = preferences.Preferences(os.path.join(config_dir, "defaults.cfg"))

        # Create a place to store the tool's log
        if not os.path.exists(utils.host_config_dir):
            os.makedirs(utils.host_config_dir)
        log_path = os.path.join(utils.host_config_dir, LOG_FILE)

        utils.create_logger(self.config, log_path=log_path);
        utils.log_system_information()

        self.main_frame = MainFrame(None, -1, "", prefs=self.config,
                                              options=self.options,
                                              on_close_func = None,
                                              update_notifier_func = None,
                                              image_list = None,
                                              add_on_exists = True)
        self.SetTopWindow(self.main_frame)
        self.main_frame.Raise()

        if show_frame:
            self.main_frame.Show()

        if self.options['errors'] == 'window':
            self.RedirectStdio()
            self.SetOutputWindowAttributes(title=_('%(APP_FULL_ID)s Error Console') % INFO)


        if boot.uc_error_set:
            wx.CallAfter(self.error_and_exit, "")
            return True

        return True


    def error_and_exit(self, msg, code):
        # If the exit code is zero then there is not error.
        if code == 0:
            dlg = wx.MessageDialog(self.main_frame, msg,
                    _("%(APP_NAME)s") % {'APP_NAME':INFO.UPDATE_APP_NAME}, wx.OK|wx.ICON_INFORMATION)
        else:
            dlg = wx.MessageDialog(self.main_frame, msg,
                    _("%(APP_NAME)s: Error") % {'APP_NAME':INFO.UPDATE_APP_NAME}, wx.OK|wx.ICON_ERROR)

        dlg.ShowModal()
        dlg.Destroy()
        sys.exit(code)
