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

"""Update Center 2.0 UI and Notification application wrapper"""

if False:    # Keep Pylint happy
    import gettext
    _ = gettext.gettext

def main(argv):
    ###################################################################################
    ########## .oOo. T H E  O R D E R  O F  I M P O R T S  I S  I M P O R T A N T .oOo.
    ###################################################################################

    import common.info as INFO
    from common.boot import uc_error, init_app_locale, check_ips

    init_app_locale()
    check_ips()

    import os
    import platform
    import getopt

    def usage(msg=None, dev=False, app=None, exit_code=1):

        """Shows the command line usage help"""

        # Platform specific portion of usage message
        plt_specific_usage = ""
        if app in ['GUI', 'Notifier', 'SWUpdate'] and platform.system() != "Windows":
            plt_specific_usage = _("""

    --tty
         Send log output to terminal (as well as log file)""")

        ### NOTE : Try to keep the line length to 80 chars wide
        usage_msg = _("""
Usage:
    %s [options]

Options:
    --notifier (-n)
         Start the desktop notifier (instead of the GUI)

    --notifier --help
         List desktop notifier specific options

    --notifier --shutdown
         Shutdown a running notifier instance

    --swupdate (-u)
         Start the Software Update tool

    --version (-v)
         Show version and exit
""") % INFO.CMD_NAME

        if app == 'GUI':
            usage_msg += _("""
    -i/--image=directory
         Supply directory as an image to start with""")

            usage_msg += plt_specific_usage

        # This is not for end users. Do not localize.
        dev_msg = """Developer/Internal options:
    --new
         Start a new instance even if an instance is already
         running

    --ipcdebug
         Debug GUI/Notifier IPC

    --updates=< show | apply >
         Used by notifier to tell GUI what to do

    --dev=show_old_updates
         Show older versions of the component in Available
         updates view

    -e/--errors=< console | terminal | log | file | logfile | window >
         Send stderr messages to specified device. By default
         they are send to the logfile.

    --debug
         Set logging level to DEBUG

    --interval=n
         Do notifier update checks every n seconds (minimum 20)

Some options like --dev can be specified multiple times.
For other options like --errors, the last specified value
is used.
"""

        final_msg = []
        if msg is not None:
            final_msg.insert(0, msg)

        final_msg.append(usage_msg)

        if dev:
            final_msg.append(dev_msg)

        uc_error("\n".join(final_msg), exit_code)

    opts = {
        'check_and_exit' : False,
        'check_type' : "updates",
        'cwd' : os.getcwd(),
        'debug' : False,
        'debug_ipcservice' : False,
        'debug_timer': False,
        'enable_feature_feed': False,
        'errors' : 'logfile',
        'force_new_instance' : False,
        'initial_action' : None,
        'interval' : 0,
        'restarted' : False,
        'show_old_updates' : False,
        'shutdown' : False,
        'silent_start' : False,
        'tool_path' : "",
        'tty' : False,
    }
    cli_options = [
        # short,long,             app,                             internal, valid args
        ("-n",  "--notifier",     ["GUI", "Notifier", "SWUpdate"], False,    None),
        ("-u",  "--swupdate",     ["GUI", "Notifier", "SWUpdate"], False,    None),
        (None,  "--new",          ["GUI", "Notifier", "SWUpdate"], True,     None),
        ("-h",  "--help",         ["GUI", "Notifier", "SWUpdate"], False,    None),
        (None,  "--devhelp",      ["GUI", "Notifier", "SWUpdate"], True,     None),
        (None,  "--ipcdebug",     ["GUI", "Notifier", "SWUpdate"], True,     None),
        (None,  "--debug",        ["GUI", "Notifier", "SWUpdate"], True,     None),
        ("-v",   "--version",     ["GUI", "Notifier", "SWUpdate"], False,    None),

        ("-i:", "--image=",       ["GUI"],                         False,    []),
        ("-e:", "--errors=",      ["GUI", "Notifier", "SWUpdate"], True,     ['console', 'terminal', 'log', 'file', 'logfile', 'window']),
        ("-d:", "--dev=",         ["GUI"],                         True,     ['show_old_updates']),

        (None,  "--updates=",     ["GUI"],                         True,     ['show', 'apply']),
        (None,  "--tty",          ["GUI", "Notifier", "SWUpdate"], False,    None),
        (None,  "--installed",    ["Notifier"],                    True,     None),
        (None,  "--uninstalled",  ["Notifier"],                    True,     None),
        (None,  "--timerdebug",   ["Notifier"],                    True,     None),
        (None,  "--toolpath=",    ["GUI", "Notifier", "SWUpdate"], True,     []),
        (None,  "--silentstart",  ["GUI", "Notifier"],             True,     None),
        (None,  "--interval=",    ["Notifier"],                    True,     []),
        (None,  "--shutdown",     ["Notifier"],                    False,     []),
        (None,  "--check-and-exit", ["Notifier"],                  True,     []),
        (None,  "--restarted",    ["GUI", "Notifier", "SWUpdate"], True,     None),
        # --macapp is used by startup sh script on Mac, not by updatetool
        # we just ignore it
        (None,  "--macapp",       ["GUI", "Notifier", "SWUpdate"], False,    None),
    ]

    if '-n' in argv or '--notifier' in argv:
        launch_intent = 'Notifier'
        APP_LONG_NAME = INFO.NOTIFICATION_APP_NAME
    elif '-u' in argv or '--swupdate' in argv:
        launch_intent = 'SWUpdate'
        APP_LONG_NAME = INFO.UPDATE_APP_NAME
    else:
        launch_intent = 'GUI'
        APP_LONG_NAME = INFO.APP_NAME

    APP_VERSION = INFO.VERSION

    short_opts = [x[0][1:] for x in cli_options if x[0] is not None]
    long_opts  = [x[1][2:] for x in cli_options if x[1] is not None]
    # Create a prepopulated map of which option is valid in which mode
    opt_applies_to = {}
    for x in cli_options:
        if x[0]:
            o = x[0]
            opt_applies_to[o[0:2]] = x[2]
        if x[1]:
            o = x[1]
            if o[-1] == "=":
                o = o[:-1]
            opt_applies_to['' + o] = x[2]

    try:
        notifier_option = False
        swupdate_option = False

        cmd_opts, dummy_args = getopt.getopt(argv, "".join(short_opts), long_opts)
        for opt, arg in cmd_opts:
            # common options
            if launch_intent not in opt_applies_to[opt]:
                usage(_("%(command_name)s: illegal option for %(app_name)s -- %(option)s") % {
                    'command_name':INFO.CMD_NAME, 'app_name':APP_LONG_NAME, 'option':opt}, app=launch_intent)
            if opt in ["-v", "--version"]:
                uc_error("%s %s-%s.%s" % (APP_LONG_NAME, APP_VERSION, INFO.MILESTONE, INFO.REVISION), 0)
            if opt in ['-h', '--help']:
                usage(exit_code=0, app=launch_intent)
            if opt == "--ipcdebug":
                opts['debug_ipcservice'] = True
            if opt == "--debug":
                opts['debug'] = True
            if opt == "--tty":
                opts['tty'] = True
                opts['errors'] = "console"
            if opt in ['-e', "--errors"]:
                if arg in ("console", "terminal"):
                    opts['errors'] = "console"
                elif arg in ("log", "file", "logfile"):
                    opts['errors'] = 'logfile'
                elif arg == "window":
                    opts['errors'] = 'window'
                else:
                    opts['errors'] = 'logfile'
            if opt in ("-i", "--image"):
                opts['cli_image'] = arg
            if opt == "--macapp":
                pass
            if opt == "--new":
                opts['force_new_instance'] = True
            if opt in ["-n", "--notifier"]:
                notifier_option = True
            if opt == "--restarted":
                opts['restarted'] = True
            if opt in ["-u", "--swupdate"]:
                swupdate_option = True
            if opt == "--updates":
                # Capture the initial operation passed from the notifier.
                # This could be "apply" or "show" (updates)
                if arg == "show":
                    opts['initial_action'] = "SHOW_UPDATES"
                elif arg == "apply":
                    opts['initial_action'] = "APPLY_UPDATES"
                else:
                    usage(_("%(command_name)s: illegal '%(option_name)s' option argument '%(argument_string)s'. " \
                            "Should be one of 'show' or 'apply'.") % {
                                'command_name':INFO.CMD_NAME, 'option_name':opt, 'argument_string':arg},
                            dev=True, exit_code=1, app=launch_intent)
            if opt in ['-d', '--dev']:
                if arg == 'show_old_updates':
                    opts['show_old_updates'] = True
                else:
                    usage(_("%(command_name)s: illegal '%(option_name)s' option argument '%(argument_string)s'.") % {
                        'command_name':INFO.CMD_NAME, 'option_name':opt, 'argument_string':arg},
                        dev=True, exit_code=1, app=launch_intent)
            if opt == '--devhelp':
                usage(dev=True, exit_code=0, app=launch_intent)
            # notifier options
            if opt == "--check-and-exit":
                opts['check_and_exit'] = True
            if opt == "--installed":
                opts['check_type'] = "installed"
            if opt == "--uninstalled":
                opts['check_type'] = "uninstalled"
            if opt == "--timerdebug":
                opts['debug_timer'] = True
            if opt == "--toolpath":
                opts['tool_path'] = arg
            if opt == "--shutdown":
                opts['shutdown'] = True
            if opt == "--silentstart":
                opts['silent_start'] = True
            if opt == "--interval":
                if arg is None or not arg.isdigit():
                    usage(_("%s: update check interval must be specified as a positive integer") % INFO.CMD_NAME, dev=True, app=launch_intent)
                interval = int(arg)
                if interval < 20:
                    usage(_("%s: update check interval must be >= 20 seconds") % INFO.CMD_NAME, dev=True, app=launch_intent)
                opts['interval'] = int(arg)

    except getopt.GetoptError, e:
        if str(e).endswith("requires argument"):
            dev_short_opts = [x[0][1:] for x in cli_options if x[0] is not None and x[3]]
            dev_long_opts  = [x[1][2:] for x in cli_options if x[1] is not None and x[3]]
            check_short = e.opt + ":"
            check_long  = e.opt + "="
            if check_short in dev_short_opts or check_long in dev_long_opts:
                is_dev = True
            else:
                is_dev = False
            usage(_("%(command_name)s: %(error)s") % {'command_name':INFO.CMD_NAME, 'error':str(e)}, dev=is_dev, app=launch_intent)
        else:
            usage(_("%(command_name)s: illegal option -- %(option)s") % {'command_name':INFO.CMD_NAME, 'option':e.opt}, app=launch_intent)

    if swupdate_option and notifier_option:
        usage(_("%s: options -n/--notifier and -u/--swupdate can not be used at the same time.") % INFO.CMD_NAME)


    from common import ipcservice
    ipcservice._debug = opts['debug_ipcservice']
    service_thread = None

    if launch_intent == 'GUI':
        import common.utils as utils
        utils.enable_tty_logger = opts['tty']
        utils.use_debug_log_level = opts['debug']

        # Ctrl-C is just not needed in the GUIs
        #utils.disable_keyboard_interrupt()

        from gui.application import Application

        appl = Application(0, options=opts, clearSigInt=False)

        # If this is the main instance (e.g. the first updatetool started) create
        # a thread to listen for and process incoming requests.
        if not opts['force_new_instance'] and appl.options['start_gui']:
            service_thread = ipcservice.IPCServiceThread(appl.main_frame, "ut_lock")
            # True here means the thread started is considered not to be worth
            # waiting for when the main thread exits.   We will shut it down
            # after the MainLoop exits.
            service_thread.setDaemon(True)
            service_thread.start()

        if 'UC_WXPYTHON' in os.environ: # XXX : HACK
            import wx.lib.inspection
            wx.lib.inspection.InspectionTool().Show()
        appl.MainLoop()

        if service_thread:
            ipcservice.send_command("ut_lock", "EXIT_THREAD")

    elif launch_intent == 'Notifier':
        import common.utils as utils
        utils.enable_tty_logger = opts['tty']
        utils.use_debug_log_level = opts['debug']

        # Issue #961
        import wx
        if opts['shutdown'] and wx.Platform == "__WXMAC__":
            ipcservice.send_command("nt_lock", "SHUTDOWN")
            sys.exit(0)

        from notifier.application import NotifierApp
        appl = NotifierApp(0, options=opts)

        # If this is the main instance (e.g. the first notifier started create
        # a thread to listen for and process incoming requests.
        if not opts['force_new_instance'] and appl.start_notifier:
            service_thread = ipcservice.IPCServiceThread(appl, "nt_lock")
            # True here means the thread started is considered not to be worth
            # waiting for when the main thread exits.   We will shut it down
            # after the MainLoop exits.
            service_thread.setDaemon(True)
            service_thread.start()

        if 'UC_WXPYTHON' in os.environ: # XXX : HACK
            import wx.lib.inspection
            wx.lib.inspection.InspectionTool().Show()
        appl.MainLoop()

        if service_thread:
            ipcservice.send_command("nt_lock", "EXIT_THREAD")


    elif launch_intent == 'SWUpdate':
        from swupdate.application import SWUpdateApp
        import common.utils as utils

        utils.enable_tty_logger = opts['tty']
        utils.use_debug_log_level = opts['debug']

        appl = SWUpdateApp(0, options=opts)

        # If this is the main instance (e.g. the first notifier started create
        # a thread to listen for and process incoming requests.
        if not opts['force_new_instance'] and appl.options['start_swupdate']:
            service_thread = ipcservice.IPCServiceThread(appl.main_frame, "swu_lock")
            # True here means the thread started is considered not to be worth
            # waiting for when the main thread exits.   We will shut it down
            # after the MainLoop exits.
            service_thread.setDaemon(True)
            service_thread.start()

        if 'UC_WXPYTHON' in os.environ: # XXX : HACK
            import wx.lib.inspection
            wx.lib.inspection.InspectionTool().Show()
        appl.MainLoop()

        if service_thread:
            ipcservice.send_command("swu_lock", "EXIT_THREAD")

    else:
        # This should never happen
        sys.exit(1)

if __name__ == "__main__":
    import sys
    if not '-n' in sys.argv[1:] and not '--notifier' in sys.argv[1:]:
        # disable console Ctrl+C for GUI only
        import signal
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    main(sys.argv[1:])
