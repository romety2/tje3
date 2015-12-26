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

"""Notification application"""

if False:    # Keep Pylint happy
    import gettext
    _ = gettext.gettext

###############################################################################
###### .oOo. T H E  O R D E R  O F  I M P O R T S  I S  I M P O R T A N T .oOo.
###############################################################################

import common.boot as boot
import common.info as INFO
import common.lockmanager as lockmanager
from common.fsutils import fsenc, fsdec
from common import fileutils
from common.basicfeed import BasicFeed
from common import ips, ipcservice, listers, preferences, utils
from common.ips import imgoptype

import sys
import os.path
import wx

import pkg.client.api_errors as api_errors
from pkg.client import global_settings

import subprocess
import ConfigParser
import socket
import httplib
import time, copy
import Queue
import swupdate.consts as CONST
import gui.views as views
import notifier.balloontip as BT
import notifier.manage as manage
from notifier.taskbar import NotifierTaskBarIcon
from dialogs.preferencesdialog import PreferencesDialog

APP_LONG_NAME     = INFO.APP_NAME + r' Notifier'
APP_CMD_NAME      = INFO.CMD_NAME
APP_CLIENT_NAME   = INFO.NOTIFIER_CLIENT_NAME
APP_APPLY_ACTION  = 1
APP_DETAIL_ACTION = 2
APP_START_WITH_CHECK = 3

ID_TIMER = wx.NewId()
ID_FRAME = wx.NewId()

UPDATE_CHECK_NORMAL      = 1
UPDATE_CHECK_SILENT      = 2

CHECK_FREQ = { 'testing': 300,         #               5*60
               'daily': 86400,         #           24*60*60
               'weekly': 604800,       #         7*24*60*60
               'monthly': 2592000,     #        30*24*60*60
               'never': 2147482647 }   #
TIMER_FREQUENCY = 60*60

class NotifierApp(wx.App):
    """The main wx.App"""

    _ = wx.GetTranslation

    def __init__(self, *args, **kwargs):

        self.options = kwargs['options']
        del kwargs['options']

        self.check_type = self.options['check_type']
        self.tool_path = self.options['tool_path']
        # The check interval if provided on the command line.
        self.cmdline_interval = self.options['interval']
        self.debug_timer = self.options['debug_timer']
        self.shutdown = self.options['shutdown']
        self.check_and_exit = self.options['check_and_exit']
        self.restarted = self.options['restarted']
        self.enable_feature_feed = self.options['enable_feature_feed']
        self.timer_interval = TIMER_FREQUENCY
        self.balloon = None
        self.start_notifier = True
        self.user_provided_timer = False
        self.update_time_initialized = False
        self.pending_image_count = 0
        self.swupdate_frame = None
        self.image_list_copy2 = None
        self.image_list_copy2_time = 0
        self.add_on_exists = False
        self.block_update_check = False
        self.update_check_queue = Queue.Queue()
        self.swupdate_frame_initializing = False
        self.logger_created = False
        self.prefs_dlg = None
        self.delayed_restart = False
        self.need_config_reload = False

        # If interval was provided on the command line it will override
        # the other intervals with the provided value.
        if self.cmdline_interval:
            self.user_provided_timer = True
            CHECK_FREQ['testing'] = self.cmdline_interval
            CHECK_FREQ['daily'] = self.cmdline_interval
            CHECK_FREQ['weekly'] = self.cmdline_interval
            CHECK_FREQ['monthly'] = self.cmdline_interval
            CHECK_FREQ['never'] = self.cmdline_interval
            if self.cmdline_interval > 60:
                self.timer_interval = 60
            else:
                self.timer_interval = 15

            print >> sys.stderr, "Debug: Daily, Weekly, Monthly intervals have been reset to %s seconds" % self.cmdline_interval
            print >> sys.stderr, "Debug: Wake up interval is set to %s seconds" % self.timer_interval

        # In debug_timer mode we redefine what daily, weekly and montly
        # mean.
        elif self.debug_timer:
            self.user_provided_timer = True
            CHECK_FREQ['testing'] = 300  # Every 5 seconds
            CHECK_FREQ['daily'] = 30     # Every 30 seconds
            CHECK_FREQ['weekly'] = 120   # Every 2 minutes
            CHECK_FREQ['monthly'] = 300  # Every 5 minutes
            self.timer_interval = 15

            print >> sys.stderr, "Debug: Timer debug mode is on"
            print >> sys.stderr, "Debug: Daily is redefined to 30 seconds"
            print >> sys.stderr, "Debug: Weekly is redefined to 120 seconds"
            print >> sys.stderr, "Debug: Monthly is redefined to 300 seconds"
            print >> sys.stderr, "Debug: Wake up interval is set to 15 seconds"

        wx.App.__init__(self, *args, **kwargs)
        global_settings.client_name = APP_CLIENT_NAME


    def OnInit(self):

        # XXX: We use "updatetool" here so we can share the same preferences
        # XXX: We could change the Preferences impl to not depend on the
        # XXX: AppName set here.
        wx.GetApp().SetAppName(APP_CMD_NAME) # NOL10N

        # this env var has been set by init_app_locale in main
        localedir = boot.get_locale_dir()
        self.app_locale = wx.Locale(wx.LANGUAGE_DEFAULT, wx.LOCALE_LOAD_DEFAULT)
        self.app_locale.AddCatalogLookupPathPrefix(localedir)
        self.app_locale.AddCatalog(APP_CMD_NAME)

        # The first thing we check is if the --shutdown option was passed.
        # This tells us to send a shutdown message to an existing
        # notifier.  Once we send the message we exit.
        if self.shutdown:
            ipcservice.send_command("nt_lock", "SHUTDOWN")
            sys.exit(0)

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
            log_file_path = os.path.join(host_config_dir, "notifier_error_log.txt")
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

        # Load initial config
        self.config = preferences.Preferences(os.path.join(config_dir, "defaults.cfg"))
        # Create a place to store the notifier log
        self.create_logger(config_dir)

        self.process_config(self.config)

        self.version = utils.get_version()

        # If this is the first time the tool is run then we check for updates
        # immediately.  If the notifier's check_at_start property is True
        # then we check immediately.
        try:
            check_at_start = \
                         self.config.getboolean('notifier', 'check_at_start')
        except ValueError:
            check_at_start = False

        # If the swu restart time is set and it is within 60 seconds then we
        # need to display the SW Update UI.  This means that the user applied
        # an update which required the notifier to restart.  The SWU was
        # instantiated at the time.  The notifier is starting back up and
        # uses this restart time property to determine if the SWU needs
        # to be instaniated.
        if _last_check_minutes(float(self.get_restart_time())) < 1:
            self.start_with_swu = True
            # We delay to avoid performing a check at the same time as the
            # Software Update UI
            update_check_delay = 60000 # 1 minute
            # Reset the restart time to 0.
            self.set_restart_time(reset=True)
            utils.logger.debug("Restarting with SWU open.")
        else:
            self.start_with_swu = False
            update_check_delay = 10000 # 10 seconds

        # See UC issue 2179.  One time only reset from daily -> weekly 
        self.reset_check_frequency()

        # We were asked to check and exit (from the scheduler).  If there
        # are no updates then we can just exit.
        if self.check_and_exit and \
           not self.start_with_swu and \
           not check_at_start and \
           not self.restarted and \
           not self.is_time_for_update_check():

            if self.config.get('notifier', 'check_frequency') == 'never' or \
               self.image_list_count == 0:
                sys.exit(99)
            else:
                sys.exit(0)

        # Determine if a notifier instance is already running.
        # If it is we can exit.
        if not self.options['force_new_instance'] and \
                                         ipcservice.process_running("nt_lock"):

            # Found a running notifier, remember to not start this instance.
            self.start_notifier = False

            # The notifier may be started as part of the bootstrapping process.
            # If a notifier is already running we don't complain to the user
            # when the instance the bootstrapper tried to start fails to
            # launch.  The silent_start option tells us to be quiet.
            if not self.options['silent_start']:
                self.RestoreStdio()
                boot.uc_error(_("%s: An instance is already running.  Use --shutdown to stop it.") % APP_LONG_NAME, 1)
            else:
                utils.logger.debug("Exiting - An instance is already running.  Use --shutdown to stop it.")
                sys.exit(1)

            # On non-Windows platforms we should not get here because uc_error
            # will call sys.exit.  On Windows we continue on.  Later in this
            # method there is a flag that triggers the error dialog and
            # sys.exit.  We have to delay until the frame is created.

        # Initialize the timer to check for updates.
        self.notify_timer = wx.Timer(self, ID_TIMER)
        if self.config.get('notifier', 'check_frequency') == 'testing':
            self.timer_interval = 60
        self.notify_timer.Start(self.timer_interval * 1000)
        wx.EVT_TIMER(self, ID_TIMER, self.OnTimerCheck)

        # This queue holds update data from the worker threads to be processed
        # by the main GUI thread.
        self.update_queue = None
        # This queue holds images to be checked for updates.
        self.image_queue = None

        try:
            # The existing notifier.sh already knows how to update itself.
            # Early versions of the Windows wrapper did not.  It relied on
            # updatetool to update the wrapper.  With the Software Update
            # UI now in use the use of updatetool may decrease so it is
            # best to have the notifier update its own wrapper.
            if wx.Platform == "__WXMSW__":
                if self.config.getboolean('main', 'optin.update.notification'):
                    wx.CallLater(4 * 60 * 1000, self.OnWrapperVersionCheck)
        except ValueError:
            pass

        utils.log_system_information()

        # Need to create a Frame so that the event loop will not exit.
        self.frame = wx.Frame(None, ID_FRAME, 'Notifier Control Frame')

        # On Mac when the user log's out we are not exiting properly.
        # This has something to do with the TaskBarIcon being instantiated.
        # To work around this problem we catch EVT_CLOSE (which gets
        # sent when the user log's off the system.  Upon EVT_CLOSE we
        # exit the notifier.
        wx.EVT_CLOSE(self.frame, self.OnClose)

        # We need a frame as a top level window so that the event loop
        # doesn't exit in the case where we don't need to display the
        # icon in the taskbar.
        self.frame_id_list = [ID_FRAME]

        if "__WXMSW__" in wx.PlatformInfo:
            app_icon_name = "application-update-tool-16x16.png"
            balloon_icon_name = "application-update-tool-24x24.png"
        elif "__WXMAC__" in wx.PlatformInfo:
            app_icon_name = "application-update-tool-48x48.png"
            balloon_icon_name = "application-update-tool-24x24.png"
        else:
            app_icon_name = "application-update-tool-24-23.png"
            balloon_icon_name = "application-update-tool-24x24.png"

        icon_path = os.path.join(os.path.dirname(__file__), "..", "images",
                                                                app_icon_name)

        # Create and place the taskbar icon
        self.taskbar = NotifierTaskBarIcon(APP_LONG_NAME, INFO.VERSION,
                                                   icon_path, self,
                                                   self.OnApply,
                                                   self.OnDetails,
                                                   self.OnPreferences)

        # This icon is used in the balloon frame
        self.icon_bitmap = utils.get_image(balloon_icon_name)
        if not self.icon_bitmap:
            utils.logger.error("Could not create the notifier icon.")
            sys.exit(1)

        if boot.uc_error_set:
            wx.CallAfter(self.error_and_exit, "")
            return True

        # If the user provided the interval (or debug timer is used) we
        # don't do any initial checks
        if self.user_provided_timer:
            #self.last_frequency_check_type == 'never':
            return True

        # The check_at_start defaults option was set so we will perform
        # the check ASAP.
        if (check_at_start or self.restarted) and \
            self.config.get('notifier', 'check_frequency') != 'never':
            # We delay displaying any updates when the notifier is first
            # started.  This is to avoid the race condition where the desktop
            # (e.g. dock, tasktray) is not fully initialized yet.

            if self.restarted:
                if not self.start_with_swu:
                    # Recheck quickly as this is a restart scenario
                    update_check_delay = 1000
                    wx.FutureCall(update_check_delay,  
                                  self.check_updates_without_notification)
                    utils.logger.debug("Restarted: Next update check will occur in %d milliseconds.",
                               update_check_delay)
                else:
                    # If we are going to instantiate the SWU it will perform
                    # the update check and callback the notifier with the
                    # results.
                    utils.logger.debug("Restarted: instantiating SWU with APP_START_WITH_CHECK")
            else:
                wx.FutureCall(update_check_delay,  self.check_updates_now)
                utils.logger.debug("Next update check will occur in %d milliseconds.",
                               update_check_delay)
        elif self.is_time_for_update_check():
            wx.FutureCall(update_check_delay,  self.check_updates_now)
            utils.logger.debug("Next update check will occur in %d milliseconds.",
                               update_check_delay)

        # Start the GUI if this was a restart and the GUI had been
        # instantiated at the time of the restart.
        if self.start_with_swu:
            self.launch_gui_updater(APP_START_WITH_CHECK)

        # We were asked to check and exit (from the scheduler).  If the
        # check frequency is never then we exit with 99.
        if self.check_and_exit and \
           check_at_start and \
           self.config.get('notifier', 'check_frequency') == 'never':
            sys.exit(99)

        return True


    # Timer Callback - Wake up and display the balloon notice
    def OnTBIconDisplay(self):

        # In case the balloon is already displayed undisplay it first.
        if self.balloon and self.balloon.IsDisplayed():
            self.balloon.UnDisplayBalloon()

        # Issue 1903 - no balloon notification if updatetool or the 
        #              SW Update dialog is open.
        if ipcservice.process_running("ut_lock") or \
           self.swupdate_frame != None:
            utils.logger.debug("Notification balloon withheld - due to UT/SWU")
            return

        title, msg = build_balloon_msg(self.new_updates)

        self.display_balloon(icon_bitmap=self.icon_bitmap,
                            title=title,
                            msg=msg,
                            display_time=self.display_usecs,
                            clickfunc=self.OnApply)


    # Windows only: If the notifier.cfg points to a valid image this will
    # kick off a wrapper check to ensure the Update Tool Notifier.exe which
    # is installed in the Startup folder is current.
    def OnWrapperVersionCheck(self):
        utils.logger.debug("OnWrapperVerisonCheck timer triggered")

        # First get the image path from the newer notifier path.  If we find
        # that it is likely the notifier wrapper already knows how to update
        # itself.
        # If notifier-1.cfg is missing then it is possible that the image
        # has been updated but the registered wrapper has not.
        image_path = get_notifier_image("notifier-1.cfg")
        if image_path == None:
            image_path = get_notifier_image("notifier.cfg")

        if image_path == None:
            utils.logger.debug("OnWrapperVerisonCheck: Unable to get image from notifier-1.cfg or notifier.cfg.")
            return

        manage.update_and_register_notifier(image_path)


    # Timer Callback - Wake up, check and see if an update check should
    # be performed.  This timer goes off every hour.
    def OnTimerCheck(self, dummy_event):

        if self.is_time_for_update_check():
            if self.debug_timer:
                print >> sys.stderr, "Debug: checking for new updates..."
                print >> sys.stderr, "Debug: pending image count: " + str(self.pending_image_count)

            # Reload the config just befor checking - there my be new images
            try:
                self.config.load_config()
            except:
                utils.logger.error("Unable to load defaults.cfg")

            # This regenerates the image_list (based on the updated props)
            self.process_config(self.config)

            if self.image_list_count == 0:
                self.set_last_check_time()
                utils.logger.debug("The image_list is empty - aborting check.")

                # No updates available so don't show the icon
                self.taskbar.remove_icon()

                # Remove balloon if there are no images to check
                if self.balloon and self.balloon.IsDisplayed():
                    self.balloon.UnDisplayBalloon()

                # If there are no images to check then we exit if
                # SW Update UI or the props dialog is not displayed.
                self.check_and_exit = True
                self.exit_if_needed(99, "No images to check.")
                self.check_and_exit = False
                return

            if not self.update_check_queue.empty():
                # An update check is already in progress so we indicate that
                # a follow on check should be performed when current check
                # completes.
                _update_queue(self.update_check_queue, UPDATE_CHECK_NORMAL)
                return
            else:
                _update_queue(self.update_check_queue, UPDATE_CHECK_NORMAL)

            self._check_for_updates()


    def OnApply(self, dummy_event):
        # If the GUI is already running send it an IPC message to apply
        # the updates.  Otherwise we have to launch the GUI ourself.
        if not ipcservice.process_running("swu_lock", show=True):
            self.launch_gui_updater(APP_APPLY_ACTION)

        if self.balloon and self.balloon.IsDisplayed():
            self.balloon.UnDisplayBalloon()


    def OnDetails(self, dummy_event):
        # If the GUI is already running send it an IPC message to show
        # the updates.  Otherwise we have to launch the GUI ourself.
        if not ipcservice.process_running("ut_lock", show=True):
            self.launch_gui_updater(APP_DETAIL_ACTION)

        if self.balloon and self.balloon.IsDisplayed():
            self.balloon.UnDisplayBalloon()


    def OnPreferences(self, dummy_event):
        self.prefs_dlg = PreferencesDialog(self.frame, -1,
                                        _("%s: Preferences") % APP_LONG_NAME,
                                        style=wx.DEFAULT_DIALOG_STYLE)

        self.prefs_dlg.set_prefs_action_handler(self.OnPrefAction)

        image_path = get_notifier_image("notifier.cfg")
        if image_path == None:
            # Try to find the image location relative the main.py
            # XXX: If we ever move the location of main.py this will break.
            image_path = os.path.join(os.path.dirname(__file__),
                                      '..', '..', '..', '..')

        # Reload the config before displaying the dialog. (issue 1053)
        self.config.load_config()

        #Update the Preferences GUI with the current config
        self.prefs_dlg.set_config(self.config, image_path)

        dummy = self.prefs_dlg.ShowModal()
        self.prefs_dlg.Destroy()
        self.prefs_dlg = None

        # We may have received a restart event while the dialog was displayed.
        # If we did and the SW Update UI is not displayed we can safely
        # restart now.
        if self.swupdate_frame == None and self.delayed_restart == True:
            # A return code of 88 indicates a restart is needed.
            os._exit(88)



    def OnPrefAction(self, event):

        # The user may have changed the check frequency.  So it now may be
        # time to perform a check.
        self.process_config(self.config)
        if self.is_time_for_update_check():
            wx.FutureCall(5000,  self.check_updates_now)

        # When the user applies the prefs inform the GUI (if it is running)
        # to reload its config.  We don't care if it was successful as the
        # GUI may not be running.
        ipcservice.send_command("ut_lock", "LOAD_CONFIG")
        ipcservice.send_command("nt_lock", "LOAD_CONFIG")

        event.Skip()


    def load_pending_image_queue(self):

        # This queue holds images to be checked for updates.
        self.image_queue = Queue.Queue()

        # Reload our list of images from the config file.
        self.image_list = self.load_images_list()
        self.pending_image_count = self.image_list_count

        for img_details in self.image_list.itervalues():
            if img_details['type'] != imgoptype.T_NORMAL:
                continue

            self.image_queue.put(img_details)


    # Returns True if the thread was started.
    def start_update_check_thread(self, img_details):

        security_attr, security_keywords = ips.get_security_defs(self.config)

        utils.logger.debug("%d: Checking for updates in %s" % \
                            (img_details['id'], fsenc(img_details['imgroot'])))

        try:
            lockmanager.lock()
            lockmanager.flag_running(img_details['imgroot'], views.UPDATES)
            lockmanager.release()
        except Exception, err_msg:
            lockmanager.release()
            utils.logger.info("Unable to check for updates in: %s" % (img_details['imgroot']))
            exctype = sys.exc_info()[0]
            utils.logger.error("    Exception: '%s' (%s)" % (str(exctype), str(err_msg)))
            utils.logger.error(utils.format_trace())
            return False

        # The results on the UpdatesListerThread's work is placed on the
        # update_queue.
        self.worker = listers.UpdatesListerThread(parent=self,
                                            uid=img_details['id'],
                                            imagedir=img_details['imgroot'],
                                            max_recent=1,
                                            security_attr=security_attr,
                                            security_keywords=security_keywords)
        return True


    def abort_threads(self):

        # This tells OnUpdateEvent() not to process any results from the
        # running threads.  They are being aborted.
        self.ignore_results = True

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
        self.ignore_results = False


    def abort_if_needed(self, imagedir):
        if lockmanager.is_locked():
            return False

        lockmanager.lock()
        ret = False
        if lockmanager.is_aborting(imagedir, views.UPDATES):
            ret = True
            lockmanager.release()
            #self.success(None)
        else:
            lockmanager.release()
        return ret


    def _check_for_updates(self):

        global_settings.client_name = APP_CLIENT_NAME
        utils.logger.debug("Entering _check_for_updates()")

        # Don't perform the check if the SW Update UI is currently
        # performing the check.
        if self.block_update_check:
            # Since we are skipping this check we need to remove the check
            # type from the update_check_queue.
            if not self.update_check_queue.empty():
                self.update_check_queue.get()

            if self.need_config_reload:
                self.reload_config()

            utils.logger.debug("Skipping update check: SW Update conflict")
            return

        # If the pending_image_count is greater than 0 then the last check
        # has not completed yet.  If we are in debug mode we don't
        # interrupt that check.   If we are in normal mode we kill those
        # remaining threads and try again.
        if self.debug_timer == True and self.pending_image_count > 0:
            utils.logger.debug("Method check_for_updates() invoked with pending_image_count = " + str(self.pending_image_count))
            utils.logger.debug("Skipping update check.")
            return

        # Not in debug mode so just log that the prior check was aborted.
        if self.pending_image_count > 0:
            utils.logger.info("Prior update check aborted.  Failed to complete prior to end of current check interval: " + str(self.pending_image_count))

        # This queue holds update data from the worker threads to be processed
        # by the main GUI thread.  OnUpdateEvent() fills it.
        self.update_queue = Queue.Queue()

        self.abort_threads()

        self.load_pending_image_queue()
        self.set_last_check_time()

        # If the queue is empty then there are no images to check for updates.
        if self.image_queue.empty():

            # No updates available so don't show the icon
            self.taskbar.remove_icon()

            # Remove balloon if there are no images to check
            if self.balloon and self.balloon.IsDisplayed():
                self.balloon.UnDisplayBalloon()

            utils.logger.debug("No application images available to check for updates")
            self.pending_image_count = 0

            # No images to check.  Check to see if we should exit.
            self.exit_if_needed(0, "No images to check.")

            return

        if self.swupdate_frame != None:
            # Inform the SW Update UI that the notifier is performing an
            # update check.
            self.swupdate_frame.update_check_in_progress(True)

        self.Bind(listers.EVT_LISTING_COMPONENT, self.OnUpdateEvent)

        # We only check for updates in at most 2 images in parallel to
        # avoid slowing down the system.  See process_update_queue() where
        # new threads are spawned when these finish their work.
        thread_count = 2
        while not self.image_queue.empty():
            if self.start_update_check_thread(self.image_queue.get()):
                thread_count -= 1
            else:
                # If we could not start the thread lower the image count
                self.pending_image_count -= 1

            if thread_count == 0:
                return

        # Failed to check any images.  In this mode we just exit if SW Update
        # UI is not up.
        if thread_count == 2:
            # Failed to check any images.  Check to see if we should exit.
            self.exit_if_needed(1,
                        "Could not start any update check threads.")


    # Called by one of the threads checking for updates on an image.
    def OnUpdateEvent(self, event):

        a, b = event.value
        id = event.GetId()

        if self.ignore_results or \
           self.abort_if_needed(self.image_list[id]['imgroot']) :
            utils.logger.debug("OnUpdateEvent: ignoring results on aborted thread: " + str(id))
            return

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
        # Issue 1694
        wx.YieldIfNeeded()


    def process_update_queue(self):

        # The UpdatesListerThreads put the results of their work in the
        # update_queue.  This method drains from the queue.
        while not self.update_queue.empty():
            wx.YieldIfNeeded()
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
                self.pending_image_count -= 1

                # Only update the list if there are pkgs with pending updates.
                if self.image_list[id]['pkgs'] != []:
                    self.update_list_has_item = True
                    utils.logger.debug("%d: -------> Listing Success for: %s" %
\
                                        (id,
                                         fsenc(self.image_list[id]['imgroot'])))
            elif type == listers.LISTING_WARNING:
                image_details = self.image_list[id]
                title = ips.get_image_title(fsenc(image_details['imgroot']),
                                            opname='list')
                utils.logger.warning("%d: Problem checking for updates in ``%s'':\n%s",
                                     id, title, item)

            elif type == listers.LISTING_ERROR or \
                 type == listers.LISTING_LONG_ERROR:
                self.pending_image_count -= 1
                image_details = self.image_list[id]
                title = ips.get_image_title(fsenc(image_details['imgroot']),
                                            opname='list')
                utils.logger.warning("%d: Unable to check for updates in ``%s'':\n%s",
                                     id, title, item)
                if self.image_has_publisher(image_details['imgroot']): 
                    utils.logger.warning("This image has been upgraded to a format no longer supported by this version of the notifier.")
                    utils.logger.warning("To check for updates in this image run the pkg or updatetool commands located in %s", image_details['imgroot'])

            else:
                image_details = self.image_list[id]
                title = ips.get_image_title(fsenc(image_details['imgroot']),
                                            opname='list')
                utils.logger.error("Unknown type returned from Update Lister: %s for image %s.",
                                     str(type), title)

            # As the prior threads finish their work we start new threads
            # to check the remaining images.
            if type != listers.LISTING_DATA and \
               type != listers.LISTING_WARNING:
                try:
                    self.start_update_check_thread(
                                              self.image_queue.get(block=False))
                except Queue.Empty:
                    pass

        # When the count reaches zero all images have been processed.  We
        # can now deal with the pending updates.
        if self.pending_image_count == 0:
            self.image_list_copy1 = copy.copy(self.image_list)
            self.image_list_copy1_time = time.time()
            self.new_updates = self.generate_update_list(self.image_list_copy1)
            utils.logger.debug("CHECK IS DONE: %d update(s) found" % len(self.new_updates))

            # Once all the update check threads have finished it is safe
            # to perform the featured SW add-on check
            self._perform_addon_check()

            self.process_updates(self.new_updates,
                                 self.update_check_queue.get())

            self.exit_if_needed(0, "No pending updates found.",
                                update_count=len(self.new_updates))

            if not self.update_check_queue.empty():
                # Check for new add-ons
                utils.logger.debug("PERFORMING SECONDARY CHECK... qsize: %d" % self.update_check_queue.qsize())
                self._check_for_updates()

            # An IPC config reload request may have arrived while we were 
            # performing the update.  It is now safe to perform the reload.
            if self.need_config_reload:
                self.reload_config()


    def generate_update_list(self, image_list):

        new_updates = []

        for img_details in image_list.itervalues():
            if img_details['pkgs'] != []:
                security_pkgs = \
                        [pkg for pkg in img_details['pkgs'] if pkg['security']]
                new_updates.append((img_details['imgroot'],
                                   img_details['pkgs'],
                                   len(security_pkgs)))

        return new_updates


    def process_updates(self, new_updates, check_type):

        if check_type == UPDATE_CHECK_NORMAL:
            # If we have updates then we notify straight away.
            if len(self.new_updates):
                # Show the icon and set the tooltip.
                self.update_taskbar_tip(self.new_updates)

                # Delay showing the balloon help until the taskbar icon is
                # displayed.
                # We can't catch any resize or create window events on the
                # taskbar icon so we have to resort to delaying to allow the
                # icon to be displayed.  Not ideal.
                wx.CallLater(3000, self.OnTBIconDisplay)

            else:
                # No updates available so don't show the icon
                self.taskbar.remove_icon()
        else:
            # check_type == UPDATE_CHECK_SILENT

            # Update the tooltip
            self.update_taskbar_tip(self.new_updates)

            if len(self.new_updates) == 0:

                # No updates available so don't show the icon
                self.taskbar.remove_icon()

                # Remove balloon if necessary
                if self.balloon and self.balloon.IsDisplayed():
                    self.balloon.UnDisplayBalloon()

            elif self.balloon and self.balloon.IsDisplayed():
                # The GUI has informed us that updates have been applied.  Since
                # updates remain and the balloon is currently displayed we
                # need to update the message
                self.balloon.UnDisplayBalloon()

                title, msg = build_balloon_msg(self.new_updates)

                self.display_balloon(icon_bitmap=self.icon_bitmap,
                            title=title,
                            msg=msg,
                            display_time=self.display_usecs,
                            clickfunc=self.OnApply)

        if self.swupdate_frame != None:
            # Inform the SW Update UI that the notifier is performing an
            # update check.
            self.swupdate_frame.update_check_in_progress(False)


    def load_images_list(self):

        self.image_list_count = 0

        img_list_dict = {}

        if not self.config.has_option('main', 'image_list'):
            return img_list_dict

        # Use a set to remove duplicate paths
        for path in set(utils.to_unicode(self.config.get('main', 'image_list')).splitlines()):
            directory = path.strip()

            if os.path.exists(fsenc(directory)):
                imgroot = ips.get_user_image_rootdir(fsenc(directory))
                if not imgroot:
                    utils.logger.warning("Not a valid image: %s", directory)
                    if self.image_has_publisher(directory):
                        utils.logger.warning("This image has been upgraded to a format no longer supported by this version of the notifier.")
                        utils.logger.warning("To check for updates in this image run the pkg or updatetool commands located in %s", directory)
                    continue
                imgroot = fileutils.canonical_path(imgroot)
                img_list_dict[self.image_list_count] = \
                        self._initialize_img_details(
                                           self.image_list_count,
                                           imgoptype.T_NORMAL,
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
        img_details['add_on_image_list'] = []

        return img_details


    def set_last_check_time(self):

        last_check_time = str(time.time())

        # Before we save anything to the config file we must first load the
        # current config to avoid overwriting any recent changes
        self.config.load_config()

        self.config.set('notifier', '_last_update_check_time', last_check_time)
        self.config.set('notifier', '_last_update_check_type',
                                 self.config.get('notifier', 'check_frequency'))

        self.config.save_config()


    def check_updates_now(self):

        if not self.update_check_queue.empty():
            # An update check is already in progress so we indicate that
            # a follow on check should be performed when current check
            # completes.
            _update_queue(self.update_check_queue, UPDATE_CHECK_NORMAL)
            return
        else:
            _update_queue(self.update_check_queue, UPDATE_CHECK_NORMAL)

        self._check_for_updates()


    def is_time_for_update_check(self):


        # We don't perform a check if the check frequency is set to never
        if self.config.get('notifier', 'check_frequency') == 'never':
            if self.debug_timer == True:
                print >> sys.stderr, "Debug: check_frequency is never - not checking for updates."
            return False

        last_check_time = float(
                         self.config.get('notifier', '_last_update_check_time'))

        # If the recorded last_check_time is later than the current time then
        # the system clock time has been moved forward then backwards.  To
        # recover we reset the last_check_time to the current time.
        if last_check_time > time.time():
            if self.debug_timer:
                print >> sys.stderr, "Debug: Resetting last_check_time: current time < last check time"
            last_check_time = time.time()
            self.set_last_check_time()

        # We need to compute the next time the update check should
        # be performed.
        next_check_time = last_check_time - 5 + CHECK_FREQ.get(
                       self.config.get('notifier', 'check_frequency'), 24*60*60)
        utils.logger.debug("Next update check will occur at %s (%s seconds from now)." % (str(time.ctime(next_check_time)), str(next_check_time- time.time())))

        if self.debug_timer:
            print >> sys.stderr, "Debug: current time: %s" % str(time.ctime())
            print >> sys.stderr, "Debug: next check  : %s" % str(time.ctime(next_check_time))
            print >> sys.stderr, "Debug: delta       : %s" % str(next_check_time- time.time())

        if time.time() >= next_check_time:
            return True

        return False


    # Process the config file.
    def process_config(self, config):

        if not config:
            return

        self.image_list = self.load_images_list()

        # Is monitoring enabled?  Should we check for updates?
        # self.monitoring_enabled = config.get('notifier', 'monitoring_enabled')

        # How long to display the balloon notification
        # -1 : until user dismisses it
        #  0 : never - just display the icon
        # NN : Number of seconds
        value_str = config.get('notifier', 'display_seconds')
        if value_str.isdigit():
            value = int(value_str)
        else:
            # XXX: Should log a bad value error.
            value = -1

        if value not in [0, -1]:
            self.display_usecs = value * 1000
        else:
            self.display_usecs = value

        # Process proxy info
        utils.set_net_proxy(config)

        #return perform_update_check_now


    # Check for available add-ons.
    def _perform_addon_check(self):

        if not self.enable_feature_feed:
            return

        global_settings.client_name = APP_CLIENT_NAME
        self.add_on_exists = False

        # Don't perform the check if the SW Update UI is currently
        # performing the check.
        if self.block_update_check:
            utils.logger.debug("Skipping add-on check: SW Update conflict")
            return

        # Atom feed for New Software and Add-ons list
        featured_feed_url = self.config.get('main', 'featured.feed.url')
        if featured_feed_url is not None and len(featured_feed_url) > 0:
            basicfeed = BasicFeed(url=featured_feed_url)
            #basicfeed.set_debug_delay(2)
            basicfeed.parse(self.featured_feed_callback)


    def featured_feed_callback(self, basicfeed):
        '''
        After the featured software Atom feed is loaded we are called
        with the feed
        '''

        try:
            from swupdate.mainframe import split_feed
            feeddata = basicfeed.get_feed()
            # Split feed into lists of apps and addons
            (apps, addons) = split_feed(feeddata)

        except Exception, e:
            utils.logger.info("Unable to get featured software feed %s: %s",
                              basicfeed.get_url(), e)
            return

        try:
            # Load feed into the list
            self.frame.Bind(listers.EVT_LISTING_COMPONENT, self.OnNewSWListingEvent)

            img_list = [img_details['imgroot'] for img_details in self.image_list.itervalues() if img_details['type'] == imgoptype.T_NORMAL]

            if img_list:
                lockmanager.lock()
                lockmanager.flag_running("Featured Feed Lock", views.UPDATES)
                lockmanager.release()

                # The results on the UpdatesListerThread's work is placed on the                # XXX_queue.
                self.not_used = listers.NewSWListerThread(parent=self.frame,
                                            uid=12356,
                                            imagedir="Featured Feed Lock",
                                            max_recent=1,
                                            image_list=img_list,
                                            feed_addon_entries=addons,
                                            feed_newsw_entries=apps)
        except Exception, e:
            utils.logger.warning("Unable to load feed %s into UI: %s",
                              basicfeed.get_url(), e)
            utils.logger.debug(utils.format_trace())
            return


    def OnNewSWListingEvent(self, event):

        a, b = event.value

        id = event.GetId()

        if a == listers.LISTING_DATA:
            self.add_on_exists = True
        elif a == listers.LISTING_INFORMATION:
            pass
        elif a in [listers.LISTING_WARNING,
                   listers.LISTING_ERROR,
                   listers.LISTING_LONG_ERROR,
                   listers.LISTING_SUCCESS]:
            pass
        else:
            utils.logger.error("Unknown type sent as Add-on ListingEvent: %s.",
                                                                        str(a))
        wx.YieldIfNeeded()


    def display_balloon(self, icon_bitmap=None, title=None,
                            msg=None, display_time=-1, clickfunc=None):

        # We don't display the balloon if display_time is 0
        if display_time == 0:
            return

        self.balloon = BT.BalloonTip(topicon=icon_bitmap, toptitle=title,
                                message=msg, shape=BT.BT_ROUNDED,
                                tipstyle=BT.BT_BUTTON, clickfunc=clickfunc)

        # Set The BalloonTip Background Colour
        #self.balloon.SetBalloonColour(wx.LIGHT_GREY)
        # Set The Font For The Balloon Title
        self.balloon.SetTitleFont(
                        wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        # Set The Colour For The Balloon Title
        self.balloon.SetTitleColour(wx.WHITE)
        # Leave The Message Font As Default
        self.balloon.SetMessageFont(
                        wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False))
        # Set The Message (Tip) Foreground Colour
        self.balloon.SetMessageColour(wx.WHITE)
        # Set The Time After Which The BalloonTip Is Destroyed
        if display_time != -1:  # User dismisses
            self.balloon.SetEndDelay(display_time)

        # Windows
        if wx.Platform == "__WXMSW__":
            # We can't find this window on Windows without native code
            tb_icon_window = None
        else:
            tb_icon_window = get_tb_icon_window(self.frame_id_list)

        self.balloon.DisplayBalloon(tb_icon_window)


    def update_taskbar_tip(self, ulist):
        n = count_updates(ulist)

        if n == 0:
            self.taskbar.set_tooltip(_("No updates available"))
        elif n == 1:
            self.taskbar.set_tooltip(_("1 update available"))
        else:
            self.taskbar.set_tooltip(_("%d updates available") % n)


    def launch_gui_updater(self, action):

        if action == APP_APPLY_ACTION:
            # Start the SW Update UI
            from swupdate.mainframe import MainFrame

            # If the SW Update UI is already up but it is also busy performing
            # a task we don't interrupt it with a new image list.
            if self.swupdate_frame != None and (self.swupdate_frame.busy or \
                                            self.block_update_check):
                self.swupdate_frame.Raise()
                self.swupdate_frame.Show()
                return

            # We preserve the image list used by SW Update if the copy
            # used by the notifier is not newer.  This deals with the
            # case where the SW Update may have applied an update but
            # the notifier has not had a chance to update its image_list.
            if self.image_list_copy2 == None or \
               self.image_list_copy1_time >= self.image_list_copy2_time:
                self.image_list_copy2 = copy.copy(self.image_list_copy1)
                self.image_list_copy2_time = self.image_list_copy1_time

            if self.swupdate_frame == None:
                if self.swupdate_frame_initializing:
                    return;

                self.swupdate_frame_initializing = True
                self.swupdate_frame = MainFrame(None, -1, "",
                               prefs=self.config,
                               options=self.options,
                               image_list=self.image_list_copy2,
                               on_close_func=self.OnSWUpdateClose,
                               update_notifier_func=self.OnSWUpdateCheck,
                               add_on_exists = self.add_on_exists)
                self.swupdate_frame_initializing = False
            else:
                # The SW Update UI is already up
                self.swupdate_frame.update_lists(self.image_list_copy2,
                                             self.add_on_exists)

            self.SetTopWindow(self.swupdate_frame)
            self.swupdate_frame.Raise()
            self.swupdate_frame.Show()
        elif action == APP_START_WITH_CHECK:
            # Start the SW Update UI
            from swupdate.mainframe import MainFrame

            if self.swupdate_frame == None:
                if self.swupdate_frame_initializing:
                    return;

                self.swupdate_frame_initializing = True
                self.swupdate_frame = MainFrame(None, -1, "",
                               prefs=self.config,
                               options=self.options,
                               image_list=None,
                               on_close_func=self.OnSWUpdateClose,
                               update_notifier_func=self.OnSWUpdateCheck,
                               add_on_exists = False)
                self.swupdate_frame_initializing = False
            else:
                utils.logger.debug("Notifier: APP_START_WITH_CHECK: non-null main_frame")
            self.SetTopWindow(self.swupdate_frame)
            self.swupdate_frame.Raise()
            self.swupdate_frame.Show()
        else:
            close_fds_on_popen = True

            # Start the main GUI
            args = ""

            if "__WXMSW__" in wx.PlatformInfo:
                # close_fds is not supported on Windows.
                close_fds_on_popen = False

            subprocess.Popen('"' + self.tool_path + '"' + args, shell=True,
                                                   close_fds=close_fds_on_popen)


    # The SW Update UI has been closed.
    def OnSWUpdateClose(self, restart_check=False):
        self.block_update_check = False
        self.swupdate_frame = None

        # Software update is indicating that updates have been applied.
        # Determine if it is safe to exit.
        self.exit_if_needed(0, "All images are up to date.",
                            update_count=len(self.new_updates))

        if restart_check:
            self.restart_if_needed()


    # This is called back when the SW Update UI starts an update check and
    # the update check completes or successfully installs some
    # updates.  This tells the notifier to:
    #   Not perform an update check if SW Update is doing a check.
    #   Update its notion of pending updates.
    def OnSWUpdateCheck(self, image_list, check_in_progress):
        if check_in_progress:
            # SW Update started an update check so this flag prevents the
            # notifier from performing a check at the same time.
            self.block_update_check = True
        else:
            self.block_update_check = False
            if image_list == None:
                self.exit_if_needed(0, "All images are up to date.")
                return
            self.image_list_copy1 = copy.copy(image_list)
            self.image_list_copy1_time = time.time()
            self.new_updates = self.generate_update_list(self.image_list_copy1)
            self.process_updates(self.new_updates, UPDATE_CHECK_SILENT)

            # Software update is indicating that updates have been applied.
            # Determine if it is safe to exit.
            self.exit_if_needed(0, "All images are up to date.",
                                update_count=len(self.new_updates))


    # Handle shutdown messages sent to the notifier from the GUI.
    def ipc_shutdown(self):
        utils.logger.info("Notifier: Shutdown message received.  Shutting down.")
        # We delay exiting to allow the IPC thread to return.  Not doing
        # so causes an exception in the IPC thread when sys.exit() is
        # invoked.
        wx.CallLater(1000, self.ExitNotifier)


    def restart_if_needed(self):
        """
        This method is triggered when the notifier needs to check if the
        files it depends on have been updated (e.g. RESTART_CHECK).

        We should restart if the version loaded at start up no longer
        matches the version on disk.

        The restart can happen immediately if the SW Update UI or Property
        windows are not open.

        The restart will be postponed until the Property Dialog is closed.

        If SW Update UI is open prompt the user to restart.

        If SW Update UI is open and the Property Dialog is open prompt the
        user to restart.
        """

        current_version = utils.get_version()

        if utils.get_version() == self.version:
            utils.logger.debug("restart_if_needed: restart not require")
            return


        if self.swupdate_frame == None and self.prefs_dlg == None:
            utils.logger.debug("restart_if_needed: notifier restarting now.")
            # A return code of 88 indicates a restart is needed.
            os._exit(88)

        if self.swupdate_frame == None and self.prefs_dlg != None:
            self.delayed_restart = True
            utils.logger.debug("restart_if_needed: delayed restart")
            return

        # SW Update UI is open - prompt for restart

        msg = _("Updates have been applied to the %(APP_NAME)s tool. " \
                "The tool should be restarted immediately to " \
                "ensure proper operation.\n\nWould you like to restart the " \
                "%(APP_NAME)s tool?") % {'APP_NAME':INFO.UPDATE_APP_NAME}

        if wx.YES == wx.MessageBox(msg,
                caption=_("Restart %(APP_NAME)s") % \
                                        {'APP_NAME':INFO.UPDATE_APP_NAME},
                style=wx.YES|wx.NO|wx.ICON_WARNING|wx.CENTER,
                parent=self.swupdate_frame):
            utils.logger.debug("restart_if_needed: user confirmed restart")


            # The SWU UI is visible so we need to remember to open this UI
            # when the tool restarts.
            self.set_restart_time()

            # A return code of 88 indicates a restart is needed.
            os._exit(88)


    def ExitNotifier(self):
        sys.exit(99)


    def OnClose(self, dummy_event):
        sys.exit(0)


    # This method will exit the notifier if required.
    #
    # The notifier will exit if the following are True:
    #   check_and_exit flag is set.
    #   SW Update is not instantiated.
    #   Notifier property window is not displayed.
    #   No pending updates.
    #
    def exit_if_needed(self, exit_code, status, update_count=0):

        if self.check_and_exit and \
           self.swupdate_frame == None and \
           self.prefs_dlg == None and \
           update_count == 0:
            utils.logger.debug("Exiting: %s", status)
            utils.logger.debug("Exit code: %d", exit_code)
            sys.exit(exit_code)


    # If the pref's are updated via the GUI prefs dialog the notifier is
    # sent a LOAD_CONFIG IPC message.  This method is called to respond
    # to the reload request.
    def reload_config(self):

        if not self.update_check_queue.empty():
            # We can't reload the config now because an update check is
            # in progress.  Reloading the config would reset the image
            # list as well as the last_check_time. 
            self.need_config_reload = True
            return

        if self.config:
            self.config.load_config()
            self.process_config(self.config)
            self.need_config_reload = False
            # We use to check if it was time to perform an update check
            # here to handle the case where the user increased the check
            # frequency.  But given a running notifier wakes up hourly
            # to perform the time check the check here is no longer needed.


    # If the Updatetool is updated the user is asked to restart the tool.
    # If the user chooses to restart the tool the GUI pings the notifier
    # to restart as well.  This method is called when the RESTART message
    # is received.
    def restart(self):
        sys.exit(88)


    # If the Updatetool GUI applys any updates it pings the notifier via
    # IPC.  This should trigger the notifier to recheck the number of
    # pending updates and update the tooltip/icon status if necessary.
    # It should not cause the balloon notification to reappear.
    def check_updates_without_notification(self):

        # Return without checking if the check interval is never.
        if self.config.get('notifier', 'check_frequency') == 'never':
            return

        if not self.update_check_queue.empty():
            # An update check is already in progress so we indicate that
            # a follow on check should be performed when current check
            # completes.
            _update_queue(self.update_check_queue, UPDATE_CHECK_SILENT)
            return
        else:
            _update_queue(self.update_check_queue, UPDATE_CHECK_SILENT)

        # Issues 623: There is a concurrency issue where both the notifier
        # and GUI may attempt to update/access the image's IPS catalog at the
        # same time.  This can cause the notifier's update check to fail.
        # A safe workaround at this point is to delay the update check
        # a couple of seconds so that it is less likely the two tools
        # will collide.
        time.sleep(5)

        # Check for updates
        self._check_for_updates()


    def error_and_exit(self, dummy_msg):
        if boot.uc_error_code == 0:
            dlg = wx.MessageDialog(self.frame, boot.uc_error_msg,
                            _("Update Tool Notifier"),
                            wx.OK|wx.ICON_INFORMATION)
        else:
            dlg = wx.MessageDialog(self.frame, boot.uc_error_msg,
                            _("Update Tool Notifier: Error"),
                            wx.OK|wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        sys.exit(boot.uc_error_code)


    def image_has_publisher(self, path):

        # We check for the publisher directory.  If it exists then this
        # image has been upgraded to the new meta data format.

        if os.path.isdir(os.path.join(fsenc(path), ".org.opensolaris,pkg",
                                                   "publisher")):
            return True

        return False


    def create_logger(self, config_dir):

        if self.logger_created:
            return

        # Create a place to store the notifier log
        if not os.path.exists(utils.host_config_dir):
            os.makedirs(utils.host_config_dir)
        log_path = os.path.join(utils.host_config_dir, "notifier.log")

        utils.create_logger(self.config, log_path=log_path)
        self.logger_created = True


    def set_restart_time(self, reset=False):

        if not reset:
            restart_time = str(time.time())
        else:
            restart_time = '0'

        # Before we save anything to the config file we must first load the
        # current config to avoid overwriting any recent changes
        self.config.load_config()

        self.config.set('notifier', '_swu_restart_time', restart_time)
        self.config.save_config()


    def get_restart_time(self):

        try:
            restart_time = \
                         self.config.get('notifier', '_swu_restart_time')
        except ValueError:
            restart_time = 0

        return restart_time

    def reset_check_frequency(self):

        if not self.config.has_section('notifier'):
            return;

        # One time reset of daily frequency to weekly.
        if not self.config.has_option('notifier', '_check_frequency_reset'):
            if self.config.get('notifier', 'check_frequency') == 'daily':
                self.config.set('notifier', 'check_frequency', 'weekly')

            self.config.set('notifier', '_check_frequency_reset', 'True')
            self.config.save_config()


def build_balloon_msg(ulist):

    one_update = False
    title = ""
    msg = ""

    if len(ulist) == 0:
        # This method should not be called with an empty list but just in case
        title = _(" No new updates available\n")
    elif len(ulist) == 1:
        if len(ulist[0][1]) == 0:
            # This should never happen...
            title = _(" No updates are available")
        elif len(ulist[0][1]) == 1:
            title = _(" New Update Available")
            one_update = True
        else:
            title = _(" New Updates Available")
    else:
        title = _(" New Updates Available")

    image_counter = len(ulist)

    for image in ulist:
        update_count = len(image[1]) - image[2]
        security_count = image[2]

        update_msg = generate_update_message(security_count, update_count)

        msg = "".join([msg, _("   %(image_name)s:\n%(message)s") % {'image_name':ips.get_image_title(fsenc(image[0]), opname='list'), 'message':update_msg}])

        if image_counter > 1:
            msg = "".join([msg, "\n"])

        image_counter -= 1

    if one_update:
        msg = "".join([msg, _("\nClick on this window to apply the update.")])
    else:
        msg = "".join([msg, _("\nClick on this window to apply some or all of these updates.")])

    return title, msg


def generate_update_message(security_count, update_count):

    if security_count > 1:
        security_text = _("updates")
    else:
        security_text = _("update")

    if update_count > 1:
        if security_count == 0:
            update_text = _("updates")
        else:
            update_text = _("other updates")
    else:
        if security_count == 0:
            update_text = _("update")
        else:
            update_text = _("other update")

    msg = ""

    if security_count > 0:
        msg = "".join([msg, _("         %(count)d security %(message)s available\n") % {'count':security_count, 'message':security_text}])

    if update_count > 0:
        msg = "".join([msg, _("         %(count)d %(message)s available\n") % {'count':update_count, 'message':update_text}])

    return msg

# Determine the total number of components needing to be updated.
def count_updates(ulist):

    n = 0

    if len(ulist) == 0:
        return 0
    else:
        for image in ulist:
            n += len(image[1])
        return n

def _update_queue(update_check_queue, type):

    # If the queue is empty we add the item.
    # If the queue just has one item then we add the item
    # If the queue has two items then we override the last item according
    # to this rule:
    # NORMAL overrides SILENT.
    # SILENT overrides nothing.

    if update_check_queue.qsize() < 2:
        update_check_queue.put(type)
        return

    # Return the first item to the queue
    update_check_queue.put(update_check_queue.get())

    last_item = update_check_queue.get()

    if type == UPDATE_CHECK_NORMAL:
        update_check_queue.put(UPDATE_CHECK_NORMAL)
        return

    if type == UPDATE_CHECK_SILENT:
        if last_item == UPDATE_CHECK_NORMAL:
            # Leave Normal on the queue as it overrides SILENT
            update_check_queue.put(UPDATE_CHECK_NORMAL)
        else:
            update_check_queue.put(UPDATE_CHECK_SILENT)
        return


def get_tb_icon_window(frame_id_list):

    for w in wx.GetTopLevelWindows():

        # The assumption here is that the taskbar window we are looking
        # for was not directly created by us.   We walk the list of
        # top level windows looking for one that has an ID that we
        # don't recognize.  If we find one that is likely the taskbar.
        # This is going to bite us at some point.
        if w.GetId() not in frame_id_list:
            return w

    return None


def get_notifier_image(file_name):

    try:
        config_dir = utils.get_config_dir()

        notifier_cfg = os.path.join(config_dir, file_name)

        if not os.path.exists(notifier_cfg):
            return None

        notifier_file = open(notifier_cfg)
        image_path = notifier_file.readline()
        notifier_file.close()

        if image_path == "":
            return None

        image_path = image_path.strip()
        if os.path.exists(fsenc(image_path)):
            return image_path

    except IOError, e:
        utils.logger.error("IOError opening %s. Errno: %s", notifier_cfg, str(e[0]))

    return None


# Returns the number of hours since the time provide as a parameter.
def _last_check_hours(last_time):
    return ((time.time() - last_time)/3600)


# Returns the number of minutes since the time provide as a parameter.
def _last_check_minutes(last_time):
    return ((time.time() - last_time)/60)


dump_windows = BT.DumpWindows

def dump_window(w):
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


def print_updates(lst):

    for image in lst:
        print image[0] + " has " + str(len(image[1])) + " item(s)."
