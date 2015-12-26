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

if False:    # Keep Pylint happy
    import gettext
    _ = gettext.gettext

###############################################################################
####### T H E  O R D E R  O F  I M P O R T S  I S  I M P O R T A N T
###############################################################################
import socket
import time
import urllib2
import urlparse

from time import localtime, strftime

from common import utils
from common.ips import CLIENT_API_VERSION

import pkg.client.api as api
import pkg.client.api_errors as api_errors
import pkg.client.image as image
from pkg.client.progress import NullProgressTracker
from pkg.client.api_errors import RetrievalError
from pkg.client import global_settings
import common.task as task
import common.info as INFO
import common.basicfeed as BF
import common.ips as ips
from common.exception import TaskInterruptedError
import swupdate.consts as CONST
import swupdate.utils as swutils

from common.fsutils import fsenc
import swupdate.installdialog as prgdlg

DLG_UPDATE_START = -1
DLG_UPDATE_PROGRESS = -2
DLG_UPDATE_DONE = -3

APP_CMD_NAME = INFO.UPDATE_CLIENT_NAME

INCONSISTENT_INDEX_ERROR_MESSAGE = "The search index appears corrupted.  " + \
    "Please rebuild the index with 'pkg rebuild-index'."

PROBLEMATIC_PERMISSIONS_ERROR_MESSAGE = "\n(Failure of consistent use " + \
    "of pfexec when executing pkg commands is often a\nsource of this problem.)"

class MultiImageTask(task.ThreadedTask, NullProgressTracker):
    def __init__(self):
        #self.duration = 100 # dummy default
        self.selected_image_list = None
        NullProgressTracker.__init__(self)

        self.act_started = False
        self.dl_started = False

        task.ThreadedTask.__init__(self)

        self.spinner = 0
        self.spinner_chars = "/-\|"
        self.last_print_time = 0
        self.last_phase = ""


    def Run(self):

        self.task_started(0)

        # XXX: Assert selected_image_list is not empty

        for img_details in self.selected_image_list:
            try:
                self._process_image(img_details, img_details['type'])
            except TaskInterruptedError:
                # The user cancelled the task.  We are finsished.
                self.task_log(_("Installation cancelled by user"))
                self.task_cancelled((task.TASK_END_USER_ABORT, None))
                self.enable_cancel(True)
                utils.logger.info("Installation cancelled by user.")
                return

        self.enable_cancel(True)
        self.task_finished()


    def _process_image(self, img_details, type):

        if type == CONST.T_NORMAL:
            type_str = _("update")
            opname = 'image-update'
            imgroot = img_details['imgroot']
        elif type == CONST.T_ADD_ON:
            type_str = _("install")
            opname = 'install'
            item = img_details['add_on_image_list'][0]
            # The target image for the addon install
            imgroot = self.image_list[item['id']]['imgroot']
        elif type == CONST.T_NEW_IMAGE:
            type_str = _("install")
            opname = 'install'
            imgroot = img_details['imgroot']
        else:
            assert False, "Unknown img_details type"

        self.enable_cancel(True)
        self.task_progress(_("Starting %s" % type_str), 0,
                               id=img_details['id'],
                               sequence=prgdlg.DLG_UPDATE_START)
        self.task_log(_("Starting %s at " % type_str) +
                    strftime("%d-%b-%Y %H:%M:%S", localtime()).decode('utf-8'))
        if type == CONST.T_ADD_ON:
            self.task_log(_("Add-On to be installed in: %s" % imgroot))
        elif type == CONST.T_NEW_IMAGE:
            self.task_log(_("New application to be installed in: %s" % imgroot))

        try:
            tmp_img = image.Image()

            global_settings.client_name = tmp_img.history.client_name = APP_CMD_NAME
            tmp_img.history.operation_name = opname
            try:
                tmp_img.find_root(fsenc(imgroot), exact_match=True)
                if tmp_img.type != image.IMG_USER:
                    msg = _("Not a valid user image: '%s'") % imgroot
                    self.task_log(msg)
                    self.task_progress(msg, 0, id=img_details['id'],
                                               sequence=prgdlg.DLG_UPDATE_ERROR)
                    return
            except (AssertionError, api_errors.ImageNotFoundException):
                if type == CONST.T_NEW_IMAGE:
                    # The image has not been created yet.  Create it now
                    status = swutils.create_image(imgroot,
                                                  img_details['title'],
                                                  img_details['description'],
                                                  img_details['publishers'])

                    if status:
                        msg = _("Unable to create image:\n  '%s'") % imgroot
                        self.task_log(msg)
                        self.task_log(_("The following error occurred:\n"))
                        self.task_log(status)
                        self.task_progress(msg, 0, id=img_details['id'],
                                           sequence=prgdlg.DLG_UPDATE_ERROR)
                        return
                    else:
                        (tmp_img, reason) = ips.load_image(imgroot, opname=opname)
                        if tmp_img is None:
                            msg = _("Unable to load image:\n  '%s'") % imgroot
                            self.task_log(_("The following error occurred:\n"))
                            self.task_log(reason)
                            self.task_progress(msg, 0, id=img_details['id'],
                                           sequence=prgdlg.DLG_UPDATE_ERROR)
                            return

                else:
                    msg = _("Application image not found:\n  '%s'") % imgroot
                    self.task_log(msg)
                    self.task_progress(msg, 0, id=img_details['id'],
                                           sequence=prgdlg.DLG_UPDATE_ERROR)
                    return

            self.check_for_interrupt()

            self.task_log(_("Loading image configuration"))
            tmp_img.load_config()

            self.last_phase = ""
            self.dl_started = False
            self.act_started = False
            self.cat_started = False
            self.reset() # Reset the progress tracker

            api_inst = api.ImageInterface(fsenc(imgroot),
                                          CLIENT_API_VERSION,
                                          self,  # Progress Tracker
                                          cancel_state_callable=None,
                                          pkg_client_name=APP_CMD_NAME)

            self.check_for_interrupt()
        except api_errors.ImageNotFoundException, e:
            msg = _("Application image not found:\n  '%s'") % e.user_dir
            self.task_log(msg)
            self.task_progress(msg, 0, id=img_details['id'],
                                           sequence=prgdlg.DLG_UPDATE_ERROR)
            utils.logger.debug(utils.format_trace())
            return
        except TaskInterruptedError:
            raise

        try:
            noexecute = False
            if self._plan_install(api_inst, img_details, noexecute) == 0:
                if not noexecute:
                    self.enable_cancel(False)
                    if self._plan_execute(api_inst, img_details['id']) == 0:
                        self.task_log(_("Installation successful"))
                    else:
                        # An error occurred creating the plan.  Continue to the
                        # next image.
                        self.enable_cancel(True)
                        return
                    self.enable_cancel(True)
            else:
                # An error occurred creating the plan.  Continue to the
                # next image.
                return

        except TaskInterruptedError:
            raise
        except Exception, e:
            msg = _("Exception caught: '%s'") % e
            self.task_log(msg)
            self.task_progress(msg, 0, id=img_details['id'],
                                           sequence=prgdlg.DLG_UPDATE_ERROR)
            utils.logger.error(utils.format_trace())
            utils.logger.error("Exception caught: '%s'" % e)
            return

        self.task_progress("", 0, id=img_details['id'],
                               sequence=prgdlg.DLG_UPDATE_DONE)


    def set_image_list(self, selected_list, all_dict):
        self.selected_image_list = selected_list
        self.image_list = all_dict


    def _plan_install(self, api_inst, img_details, noexecute=False):

        refresh_catalogs = True
        force = False # Don't skip safety checks
        verbose = False
        update_index = True # update the search indices after the op completes
        be_name = None # Rename the newly created boot environment
        img_id = img_details['id']

        try:
            self.task_log(_("Creating install plan"))

            if img_details['type'] == CONST.T_NORMAL:
                # cre is either None or a catalog refresh exception which was
                # caught while planning.
                stuff_to_do, opensolaris_image = \
                    api_inst.plan_update_all(INFO.CMD_NAME,
                                     refresh_catalogs=refresh_catalogs,
                                     noexecute=noexecute, force=force,
                                     verbose=verbose,
                                     update_index=update_index, be_name=be_name)
            elif img_details['type'] == CONST.T_ADD_ON or \
                 img_details['type'] == CONST.T_NEW_IMAGE:
                stuff_to_do = \
                    api_inst.plan_install(
                                     img_details['feed_entry'][BF.PACKAGES],
                                     [],
                                     refresh_catalogs=refresh_catalogs,
                                     noexecute=noexecute, verbose=verbose,
                                     update_index=update_index)

            if not stuff_to_do:
                self.task_log(
                          _("No pending components for this application image"))
                self.task_progress("", 0, id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_DONE)
                return 1
        except api_errors.InventoryException, e:
            self.task_log(
                        _("Inventory exception:\n%s") % e)
            self.task_progress(_("Inventory exception"), 0,
                                   id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except api_errors.CatalogRefreshException, e:
            if self.display_catalog_failures(e) == 0:
                if not noexecute:
                    return 1
            else:
                self.task_log(_("Catalog refresh failed"))
                self.task_progress(_("Catalog refresh failed"), 0,
                                   id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
                return 1
        except api_errors.BEException, e:
            # This is a Boot Environement (BE) Exception which we should never
            # see.
            self.task_log(
                        _("Boot Environement Exception (BEException):\n%s") % e)
            self.task_progress(_("Boot Environement Exception (BEException)"),
                                   0,
                                   id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except api_errors.PlanCreationException, e:
            self.task_log(_("Error creating install plan:\n%s") % e)
            self.task_progress(_("Error creating install plan"), 0,
                                   id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except api_errors.PermissionsException, e:
            self.task_log(_("Error: Insufficient permissions:\n%s") % e)
            self.task_progress(_("Error: Insufficient permissions"), 0,
                                   id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except api_errors.IpkgOutOfDateException:
            self.task_log(_("Error: pkg(5) appears to be out of date"))
            self.task_progress(_("Error: pkg(5) appears to be out of date"), 0,
                                   id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except api_errors.ImageNotFoundException, e:
            msg = _("Application image not found:\n   '%s'") % e.user_dir
            self.task_log(msg)
            self.task_progress(msg, 0, id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except TaskInterruptedError:
            raise
        except Exception, e:
            raise

        if noexecute:
            return 0

        # Exceptions which happen here are printed in the above level, with
        # or without some extra decoration done here.
        # XXX would be nice to kick the progress tracker.
        try:
            self.task_log(_("Preparing install plan"))
            api_inst.prepare()
        except api_errors.TransportError, e:
            msg = _("Error: Transport Error:\n   '%s'") % e
            self.task_log(msg)
            self.task_progress(msg, 0, id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except KeyboardInterrupt:
            msg = _("Error: Keyboard Interrupt")
            self.task_log(msg)
            self.task_progress(msg, 0, id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except api_errors.PermissionsException, e:
            self.task_log(_("Error: Insufficient permissions:\n%s") % e)
            self.task_progress(_("Error: Insufficient permissions"), 0,
                                   id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except api_errors.ActionExecutionError, e:
            self.task_log(_("Error: Action Execution:\n%s") % e)
            self.task_progress(_("Error: Action Execution"), 0,
                                   id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except TaskInterruptedError:
            raise
        except Exception, e:
            raise

        return 0


    def _plan_execute(self, api_inst, img_id):
        try:
            self.task_log(_("Executing install plan"))
            api_inst.execute_plan()
            return 0
        except api_errors.WrapSuccessfulIndexingException, e:
            # This is harmless and happens for old style indexed images
            utils.logger.debug("WrapSuccessfulIndexingException happened for an old image at MultiImageTask._plan_execute()")
            return 0
        except RuntimeError, e:
            self.task_log(_("Runtime Error:\n%s") % e)
            self.task_progress(_("Runtime Error"), 0,
                                   id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            utils.logger.error(utils.format_trace())
            utils.logger.error("Runtime Error:\n%s" % e)
            return 1
        except api_errors.ImageUpdateOnLiveImageException:
            msg = _("Error: Update cannot be done on a live image")
            self.task_log(msg + " (ImageUpdateOnLiveImageException)")
            self.task_progress(msg, 0, id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except api_errors.CorruptedIndexException, e:
            msg = _("Error: The search index appears to be corrupted")
            self.task_log(msg + _(". Please rebuild the index with 'pkg rebuild-index'."))
            self.task_progress(msg, 0, id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except api_errors.ProblematicPermissionsIndexException, e:
            self.task_log(_("Error: ProblematicPermissionsIndexException:\n%s") % e)
            self.task_progress(_("Error: Permissions issue"), 0,
                                   id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except api_errors.PermissionsException, e:
            self.task_log(_("Error: Insufficient permissions:\n%s") % e)
            self.task_progress(_("Error: Insufficient permissions"), 0,
                                   id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except api_errors.ActionExecutionError, e:
            self.task_log(_("Error: Action Execution:\n%s") % e)
            self.task_progress(_("Error: Action Execution"), 0,
                                   id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except api_errors.BEException, e:
            # This is a Boot Environement (BE) Exception which we should never
            # see.
            self.task_log(
                        _("Boot Environement Exception (BEException):\n%s") % e)
            self.task_progress(_("Boot Environement Exception (BEException)"),
                                   0,
                                   id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except KeyboardInterrupt:
            msg = _("Error: Keyboard Interrupt")
            self.task_log(msg)
            self.task_progress(msg, 0, id=img_id,
                                   sequence=prgdlg.DLG_UPDATE_ERROR)
            return 1
        except Exception, e:
            raise


    def cat_output_start(self):
        # Fetching catalog

        if not self.cat_started:
            self.task_log(_("Fetching catalog(s): "))
            self.cat_started = True

        if self.last_phase != self.cat_cur_catalog:
            self.last_phase = self.cat_cur_catalog
            self.task_log("     " + self.cat_cur_catalog)

        self.task_progress(
                     _("Fetching catalog '%s'..." % (self.cat_cur_catalog)), 0)


    def cat_output_done(self):
        # "Fetched catalog '%s'." % self.cat_cur_catalog
        self.task_progress(
                     _("Fetching catalog '%s'...Done" % \
                     (self.cat_cur_catalog)), 0)
        pass


    def eval_output_start(self):
        # "Creating plan..."
        self.task_progress(_("Creating Plan"), 0)
        pass


    def eval_output_progress(self):
        # "Creating plan..."
        if (time.time() - self.last_print_time) >= 0.10:
            self.last_print_time = time.time()
        else:
            return
        self.spinner += 1
        if self.spinner >= len(self.spinner_chars):
            self.spinner = 0

        self.task_progress(
                      _("Creating Plan %c" % self.spinner_chars[self.spinner]),
                      0)


    def eval_output_done(self):
        # "Install plan created."
        pass


    def ver_output(self):

        if self.ver_cur_fmri != None:
            if (time.time() - self.last_print_time) >= 0.10:
                self.last_print_time = time.time()
            else:
                return
            self.spinner += 1
            if self.spinner >= len(self.spinner_chars):
                self.spinner = 0
                self.task_progress(_("%-50s..... %c%c") % \
                                    (self.ver_cur_fmri.get_pkg_stem(),
                                     self.spinner_chars[self.spinner],
                                     self.spinner_chars[self.spinner]))


    def ver_output_error(self, actname, errors):
        # "Verification error occured for %s" % actname
        pass


    def dl_output(self):
        if not self.dl_started:
            self.dl_started = True
            #self.set_duration(self.dl_goal_nbytes)
            #self.enable_cancel(True)
            self.task_progress(_("Starting download"), self.dl_cur_nbytes)
            self.task_log(_("Starting package download"))
            if self.dl_goal_npkgs == 1:
                self.task_log(_(
                   "1 package to download (%(nf)s file(s)) (%(size).2f MB)") % {
                                'nf':self.dl_goal_nfiles,
                                'size':(self.dl_goal_nbytes / 1024.0 / 1024.0)})
            else:
                self.task_log(_(
                   "%(npkgs)s packages to download (%(nf)s file(s)) (%(size).2f MB)") % {
                                'npkgs':self.dl_goal_npkgs,
                                'nf':self.dl_goal_nfiles,
                                'size':(self.dl_goal_nbytes / 1024.0 / 1024.0)})

        self.check_for_interrupt()

        if self.last_phase != self.dl_cur_pkg:
            self.last_phase = self.dl_cur_pkg
            self.task_log(_("     Downloading: %(pkg_name)s" % {
                                  'pkg_name': self.dl_cur_pkg}))

        if self.dl_goal_npkgs == 1:
            strn = _("Downloaded %(current_bytes).2f of %(total_bytes).2f MB Overall\n" \
                    "   Downloading:  %(pkg_name)s") % {
                        'current_bytes': (self.dl_cur_nbytes / 1024.0 / 1024.0),
                        'total_bytes': (self.dl_goal_nbytes / 1024.0 / 1024.0),
                        #"%d/%d" % (self.dl_cur_nfiles, self.dl_goal_nfiles),
                        'pkg_name': self.dl_cur_pkg}
        else:
            strn = _("Downloaded %(current_bytes).2f of %(total_bytes).2f MB Overall\n" \
                    "   Downloading:  %(pkg_name)s  (%(current_pkg_count)s of %(total_pkg_count)s components)") % {
                        'current_bytes': (self.dl_cur_nbytes / 1024.0 / 1024.0),
                        'total_bytes': (self.dl_goal_nbytes / 1024.0 / 1024.0),
                        #"%d/%d" % (self.dl_cur_nfiles, self.dl_goal_nfiles),
                        'pkg_name': self.dl_cur_pkg,
                        'current_pkg_count': self.dl_cur_npkgs + 1,
                        'total_pkg_count':self.dl_goal_npkgs}

        self.task_progress(strn, self.dl_cur_nbytes)


    def dl_output_done(self):
        #self.enable_cancel(False)
        self.check_for_interrupt()
        self.dl_started = False
        self.task_progress(_("Download completed"), self.dl_goal_nbytes)
        self.task_log(_("Download completed"))


    def act_output(self):

        # XXX - This code has internal knowledge of IPS.
        if self.act_phase == 'Install Phase':
            strn = _("Install Phase:\n   Installing file %(file_number)d of %(total_files)d") % {
                    'file_number':self.act_cur_nactions, 'total_files':self.act_goal_nactions}
        elif self.act_phase == 'Removal Phase':
            strn = _("Removal Phase:\n   Removing file %(file_number)d of %(total_files)d") % {
                    'file_number':self.act_cur_nactions, 'total_files':self.act_goal_nactions}
        elif self.act_phase == 'Update Phase':
            strn = _("Update Phase:\n   Updating %(file_number)d of %(total_files)d") % {
                    'file_number':self.act_cur_nactions, 'total_files':self.act_goal_nactions}
        else:
            strn = _("%(action)s %(done_count)d of %(total_count)d") % {
                    'action':self.act_phase, 'done_count':self.act_cur_nactions, 'total_count':self.act_goal_nactions}

        # The first time, emit header.
        if not self.act_started:
            self.act_started = True
            self.task_progress(strn, self.act_cur_nactions)
            self.task_log(_("Executing actions:"))
            #self.set_duration(self.act_goal_nactions)
        else:
            if self.act_phase != self.last_phase:
                self.last_phase = self.act_phase
                self.task_log(_("     %(phase)s: %(nactions)s action(s)" % {
                               'phase':self.act_phase,
                               'nactions':self.act_goal_nactions}))

            self.task_progress(strn, self.act_cur_nactions)


    def act_output_done(self):
        self.task_progress(_("Action completed"), self.act_goal_nactions)


    def ind_output(self):

        strn = _("Indexing:\n   %-40s %11s" % \
                   (
                       self.ind_phase,
                       "%d/%d" % (self.ind_cur_nitems,
                           self.ind_goal_nitems)
                   ))

        if self.last_phase != self.ind_phase:
            self.last_phase = self.ind_phase
            self.task_log(_("%s: %d item(s)" %
                                  (self.ind_phase, self.ind_goal_nitems)))

        self.task_progress(strn, self.ind_cur_nitems)


    def ind_output_done(self):
        self.task_progress(_("Indexing completed"), self.ind_goal_nitems)


    #def set_image_list(self, list):
    #    self.selected_image_list = list


    def display_catalog_failures(self, cre):
        #total = cre.total
        succeeded = cre.succeeded
        #msg(_("pkg: %s/%s catalogs successfully updated:") % (succeeded, total))
        for pub, err in cre.failed:
            if isinstance(err, urllib2.HTTPError):
                       self.task_log("   %s: %s - %s" %
                                            (err.filename, err.code, err.msg))
            elif isinstance(err, urllib2.URLError):
                if err.args[0][0] == 8:
                    self.task_log("    %s: %s" % \
                         (urlparse.urlsplit(
                             pub["origin"])[1].split(":")[0],
                         err.args[0][1]))
                else:
                    if isinstance(err.args[0], socket.timeout):
                        self.task_log("    %s: %s" %
                                            (pub["origin"], "timeout"))
                    else:
                        self.task_log("    %s: %s" %
                                            (pub["origin"], err.args[0][1]))
            elif isinstance(err, RetrievalError) and \
                     isinstance(err.exc, EnvironmentError) and \
                     err.exc.errno == errno.EACCES:
                if err.pub:
                    self.task_log("   ", _("Could not update catalog "
                                  "for '%s' due to insufficient "
                                  "permissions.") % err.pub)
                else:
                    self.task_log("   ", _("Could not update a catalog "
                                  "due to insufficient permissions."))

            else:
                self.task_log("   ", err)

        if cre.message:
            self.task_log(cre.message)

        return succeeded
