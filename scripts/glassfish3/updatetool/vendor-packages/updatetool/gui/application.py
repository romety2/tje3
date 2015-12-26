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

import os
import sys
import wx
import common.boot as boot
import common.info as INFO
from common.fsutils import fsenc, fsdec
import socket
import common.utils as utils
import common.ips as ips
import common.ipcservice as ipcservice
from gui.mainframe import MainFrame
import notifier.manage as nt_manage

import gettext
if False:    # Keep Pylint happy
    _ = gettext.gettext



class Application(wx.App):

    _ = wx.GetTranslation

    def __init__(self, *args, **kwargs):
        self.options = kwargs['options']
        del kwargs['options']
        self.options['start_gui'] = True

        wx.App.__init__(self, *args, **kwargs)


    def OnInit(self):

        show_main_frame = True

        self.SetAppName(INFO.CMD_NAME) # NOL10N

        # Have wx load appropriate localizations
        localedir = boot.get_locale_dir()
        self.app_locale = wx.Locale(wx.LANGUAGE_DEFAULT, wx.LOCALE_LOAD_DEFAULT)
        self.app_locale.AddCatalogLookupPathPrefix(localedir)
        self.app_locale.AddCatalog(INFO.CMD_NAME)

        ### This whole block deals with getting a directory where we can log stdout/stderr output from
        ### the app. Currently it's the same dir as configuration directory.
        config_dir = utils.get_config_dir()
        if not os.path.exists(config_dir):
            #XXX: What exception could this throw?
            os.makedirs(config_dir)
        config_file_path = os.path.join(config_dir, "defaults.cfg")
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
        # Determine if an updatetool instance is already running.
        # If it is, based on the passed parameters (show and action) send
        # it a message to Open/Raise, show or apply updates.
        if not self.options['force_new_instance'] and \
                         ipcservice.process_running("ut_lock",
                                                    show=True,
                                                    action=self.options['initial_action']):
            # Found a running GUI, remember to not start this instance.
            self.options['start_gui'] = False

            if self.options['silent_start']:
                return 1

            # If the notifier sent us an action to execute we don't
            # complain about the GUI already running.
            if self.options['initial_action'] is None:
                self.RestoreStdio()


                boot.uc_error(_("%s: The tool is already running.") % INFO.CMD_NAME, 1)
                # For this type of error we don't want the mainframe to be
                # displayed.
                show_main_frame = False
            else:
                return 1

        wx.InitAllImageHandlers()

        self.main_frame = MainFrame(None, -1, "", config=config_file_path,
                show_old_updates=self.options['show_old_updates'],
                enable_feature_feed=self.options['enable_feature_feed'])
        self.SetTopWindow(self.main_frame)
        self.main_frame.Raise()

        if show_main_frame:
            self.main_frame.Show()

        if self.options['errors'] == 'window':
            self.RedirectStdio()
            self.SetOutputWindowAttributes(title=_('%(application name)s Error Console') % {'application name':INFO.APP_FULL_ID})

        del config_dir
        del config_file_path
        # Notifier life cycle management
        # Set a timer to check to see if the notifier needs to be registered
        # as a login startup task.  We do this check only once, 30 seconds
        # after the tool is launched if the user is not a root user.  See
        # issue 729 for details.
        if wx.Platform == "__WXMSW__" or os.geteuid() != 0:
            wx.CallLater(30 * 1000, self.notifier_ops_timer_event)
        else:
            utils.logger.debug("Notifier registration not triggered: root user")

        wx.YieldIfNeeded()
        wx.CallAfter(self._initial_tasks)
        if boot.uc_error_set:
            wx.CallAfter(self.error_and_exit, boot.uc_error_msg, boot.uc_error_code)

        return 1


    def _initial_tasks(self):

        conf = self.main_frame.config
        last_image = ""
        if conf.has_option("main", "_last_active_image"):
            last_image = utils.to_unicode(conf.get('main', '_last_active_image'))
        utils.logger.debug("Loading images list")
        self.main_frame.load_images_list()
        if last_image and last_image != "":
            self.main_frame.add_image(last_image, quiet=True, add_any=True)
        has_cli_image = False
        if 'cli_image' in self.options:
            utils.logger.debug("Adding CLI image '%s'" % self.options['cli_image'])
            has_cli_image = self.main_frame.add_image(self.options['cli_image'], add_any=True, quiet=True)
            utils.logger.debug("Final CLI image %s" % repr(has_cli_image))
        utils.logger.debug("Adding CWD image '%s'" % self.options['cwd'])
        has_cwd_image, success = self.main_frame.add_image(self.options['cwd'], add_any=False, quiet=True)
        utils.logger.debug("Final CWD image %s" % repr(has_cwd_image))

        found = False
        notifier_initiated_view = False

        for image in [has_cli_image, has_cwd_image, sys.executable, last_image]:
            if image and image != "":
                imagedir = ips.get_user_image_rootdir(fsenc(image), opname='list')
                if imagedir is None:
                    utils.logger.debug("Could not get image rootdir for '%s'." % image)
                    continue
                u_imagedir, success = self.main_frame.add_image(fsdec(imagedir), add_any=False, quiet=True)
                if not success:
                    utils.logger.debug("Could not add image '%s'." % imagedir)
                    continue
                node_id = self.main_frame.imgs_tree.get_image_node(u_imagedir)[0]
                if node_id:
                    utils.logger.debug("Selecting image '%s'." % imagedir)
                    self.main_frame.imgs_tree.select_image_node(u_imagedir)
                    utils.logger.debug("Selected image '%s'." % imagedir)
                    found = True
                    break
                else:
                    utils.logger.debug("Added but could not select image '%s'." % imagedir)
                    utils.logger.debug("*** THAT SHOULD NOT HAVE HAPPENED ***" % imagedir)

        self.main_frame.save_images_list()

        if self.options['initial_action'] == 'APPLY_UPDATES':
            utils.logger.debug("GUI triggered via notifier (APPLY_UPDATES).")
            # Confirm and apply known updates
            self.main_frame.notifier_apply_updates()
            notifier_initiated_view = True
        elif self.options['initial_action'] == 'SHOW_UPDATES':
            utils.logger.debug("GUI triggered via notifier (SHOW_UPDATES).")
            self.main_frame.notifier_show_updates()
            notifier_initiated_view = True

        if not found and not notifier_initiated_view:
            utils.logger.debug("Selecting first image.")
            if not self.main_frame.imgs_tree.select_image_node(-1):
                # HACK
                self.main_frame.set_list_msg(_("Please create or open a new image"))
                self.main_frame.pkg_details_panel.describe_view(None, None)

        if boot.uc_error_set:
            wx.CallAfter(self.error_and_exit, boot.uc_error_msg, boot.uc_error_code)


    def error_and_exit(self, msg, code):
        # If the exit code is zero then there is not error.
        if code == 0:
            dlg = wx.MessageDialog(self.main_frame, msg,
                    _("%(APP_NAME)s") % {'APP_NAME':INFO.APP_NAME}, wx.OK|wx.ICON_INFORMATION)
        else:
            dlg = wx.MessageDialog(self.main_frame, msg,
                    _("%(APP_NAME)s: Error") % {'APP_NAME':INFO.APP_NAME}, wx.OK|wx.ICON_ERROR)

        dlg.ShowModal()
        dlg.Destroy()
        sys.exit(code)


    def notifier_ops_timer_event(self):
        """
        This method will register the notifier as a login startup task and
        start the notifier if the check_frequency is set to daily, weekly or
        monthly and the notifier is not already registered.
        """

        # Check the check_frequency.  If it is never then we are done.
        config = self.main_frame.config
        if config.has_option('notifier', 'check_frequency'):
            if config.get('notifier', 'check_frequency') == 'never':
                utils.logger.debug("Auto notifier reg/startup aborted: Automatic update checks not selected.")
                return

        image_path = ips.get_python_image_path()
        utils.logger.debug("Current image path: " + image_path)

        status = nt_manage.update_and_register_notifier(image_path)

        # If the image_path is empty then we are running from the workspace
        # so we will use the tool-path option.
        alternate_path = None
        if image_path == "":
            alternate_path = self.options["tool_path"]

        # A status of 1 indicates the notifier is already registered.  If
        # that is the case we do not need to start it here.
        if status != 1:
            # See issue 1917
            if status == 0:
                args = '--check-and-exit'
            else:
                args = ''

            nt_manage.start_notifier(image_path, args, alt_path=alternate_path)

# end of class Application
