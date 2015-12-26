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

from common import utils
import os

def register_notifier(image_path, register=True, force=True):
    """This function will register the notifier using the provide image path."""

    import wx
    import subprocess

    if register:
        args = " --register"
        utils.logger.debug("Notifier registration triggered")
        reg_string  = "registration"
    else:
        args = " --unregister"
        utils.logger.debug("Notifier unregistration triggered")
        reg_string  = "unregistration"

    if force:
        args += " --force"

    # If an app image is not passed to us we can't find updatetoolconfig
    # to manage the reg/unreg.
    if  image_path == "":
        utils.logger.warning("Notifier %s: Unable to locate an application image in order to perform the %s.", reg_string, reg_string)
        return 2

    if wx.Platform == "__WXMSW__":
        exec_path = os.path.join(image_path, 'updatetool', 'bin',
                                 'updatetoolconfig.bat')
    else:
        exec_path = os.path.join(image_path, 'updatetool', 'bin',
                                             'updatetoolconfig')

    error_code = 0

    if os.path.exists(exec_path):
        # Fire off the register request.  This will quietly fail
        # if the notifier is already (un)registered or some other
        # issue exists.
        try:
            if "__WXMSW__" in wx.PlatformInfo:
                # close_fds is not supported on Windows.
                close_fds_on_popen = False
            else:
                close_fds_on_popen = True

            utils.logger.debug("Notifier %s: launching: %s %s",
                                   reg_string, exec_path, args)
            proc = subprocess.Popen('"' + exec_path + '"' + args,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True,
                                    close_fds=close_fds_on_popen)
            output, errors = proc.communicate()
            utils.logger.debug("Notifier %s: output: %s", reg_string, output)
            utils.logger.debug("Notifier %s: errors: %s", reg_string, errors)
            error_code = proc.wait()

            if error_code > 1:
                utils.logger.warning("Notifier %s failed: error code %d", reg_string, error_code)
	    elif error_code == 1:
                utils.logger.info("Notifier %s: return code %d", reg_string, error_code)
        except (OSError, Exception), e:
            utils.logger.warning("Notifier %s: failed: %s", reg_string, e)
            error_code = 2
    else:
        utils.logger.warning("Notifier %s: failed: path does not exist: %s", reg_string, exec_path)
        error_code = 2

    return error_code

def start_notifier(image_path, args, alt_path="run"):

    import subprocess
    import wx

    if image_path == "":
        exec_path = alt_path
        utils.logger.debug("start_notifier: Using alt path: %s", exec_path)
    elif wx.Platform == "__WXMSW__":
        exec_path = os.path.join(image_path, 'updatetool', 'bin',
                                 'updatetool.exe')
    else:
        exec_path = os.path.join(image_path, 'updatetool', 'bin',
                                             'updatetool')

    error_code = 0

    if os.path.exists(exec_path):
        args =  " -n --silentstart " + args

        # Launch the notifier.  This will quietly fail
        # if the notifier is already running or some other
        # issue exists.
        try:
            utils.logger.debug("Notifier: launching: %s %s",
                                   exec_path, args)

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
            #output, errors = proc.communicate()
            #logger.info("Notifier start up: output: %s", output)
            #logger.info("Notifier start up: errors: %s", errors)
        except OSError, e:
            utils.logger.warning("Notifier start up: failed: %s", e)
            error_code = 1
        except Exception, e:
            utils.logger.warning("Notifier start up: failed: %s", e)
            error_code = 1
    else:
        utils.logger.warning("Notifier start up: failed: path does not exist: %s", exec_path)
        error_code = 1

    return error_code


def update_and_register_notifier(image_path):
    import subprocess
    import wx

    utils.logger.debug("Notifier registration triggered")

    # We can not determine the image location.  The updatetool is likely
    # being run outside of an image.
    if image_path == "":
        return

    # Tracks whether we need to force registration of the notifier.
    force = False

    if wx.Platform == "__WXMSW__":
        exec_path = os.path.join(image_path, 'updatetool', 'bin',
                                 'updatetoolconfig.bat')
        uninstalled_ut_exec_path = os.path.join(image_path, 'updatetool',
                                              'lib', 'Update Tool Notifier.exe')
        home_dir = os.path.expanduser("~").strip()
        installed_ut_exec_path = os.path.join(home_dir, 'Start Menu',
                                              'Programs', 'Startup',
                                              'Update Tool Notifier.exe')

        utils.logger.debug("uninstalled_ut_exec_path: " + uninstalled_ut_exec_path)
        utils.logger.debug("installed_ut_exec_path: " + installed_ut_exec_path)

        # Check the installed wrapper version against the wrapper version
        # in the image.  If the image wrapper version is newer then we
        # update the wrapper from this image.
        if os.path.exists(uninstalled_ut_exec_path) and \
           os.path.exists(installed_ut_exec_path):

            try:
                # Determine the version of the wrapper in the image.
                utils.logger.debug(
                      "Notifier update: getting image wrapper version: %s",
                      uninstalled_ut_exec_path)

                check_args = " --wrapperversion"

                if "__WXMSW__" in wx.PlatformInfo: 
                    # close_fds is not supported on Windows. 
                    close_fds_on_popen = False 
                else:
                    close_fds_on_popen = True 

                proc = subprocess.Popen('"' + uninstalled_ut_exec_path +
                                        '"' + check_args,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True,
                                        close_fds=close_fds_on_popen)
                output, errors = proc.communicate()
                image_version = proc.wait()

                utils.logger.debug("Notifier update: output: %s", output)
                utils.logger.debug("Notifier update: errors: %s", errors)
                utils.logger.debug("Notifier update: version: %d",
                                   image_version)

                utils.logger.debug(
                   "Notifier update: getting installed wrapper version: %s",
                   installed_ut_exec_path)

                # Deterimine the version fo the installed wrapper.

                proc = subprocess.Popen('"' + installed_ut_exec_path +
                                        '"' + check_args,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=True,
                                        close_fds=close_fds_on_popen)
                output, errors = proc.communicate()
                installed_version = proc.wait()
                utils.logger.debug("Notifier update: output: %s", output)
                utils.logger.debug("Notifier update: errors: %s", errors)
                utils.logger.debug("Notifier update: version: %d",
                                   installed_version)

                # If the image version is newer then use the --force
                # option to register.  This will overwrite the current
                # wrapper exe.
                if image_version > installed_version:
                    force = True

            except OSError, e:
                utils.logger.warning("Notifier verson check: failed: %s", e)
            except Exception, e:
                utils.logger.warning("Notifier verson check: failed: %s", e)

    else:
        exec_path = os.path.join(image_path, 'updatetool', 'bin',
                                 'updatetoolconfig')

    if os.path.exists(exec_path):
        utils.logger.debug("Notifier registration: launching: %s",
                               exec_path)

        return register_notifier(image_path, register=True, force=force)

    else:
	return 2

