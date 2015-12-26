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

from common.fsutils import fsenc
from common import task
import common.info as INFO
from pkg.client.progress import NullProgressTracker
from pkg.client import image, api, api_errors
from common.exception import TaskInterruptedError, UpdateToolException
from common import utils
import socket
import sys
import urllib2
import urlparse
import errno
#from time import localtime, strftime
from common.mixins import KeywordArgsMixin

from common.ips import CLIENT_API_VERSION
APP_CMD_NAME = INFO.CMD_NAME

if False:          # Make Pylint happy
    import gettext
    _ = gettext.gettext

class AppTask(task.ThreadedTask, NullProgressTracker):

    # Issue 1337 - Without this our translations do not get picked up for dl_output etc.
    import wx
    _ = wx.GetTranslation

    def __init__(self):
        self.duration = 100 # dummy default
        self.iplan = None
        NullProgressTracker.__init__(self)

        self.act_started = False
        self.dl_started = False
        self.ind_started = False

        task.ThreadedTask.__init__(self)


    def cat_output_start(self):
        # "Fetching catalog '%s'..." % self.cat_cur_catalog
        pass


    def cat_output_done(self):
        # "Fetched catalog '%s'." % self.cat_cur_catalog
        pass


    def eval_output_start(self):
        # "Creating plan..."
        pass


    def eval_output_progress(self):
        # "Creating plan..."
        pass


    def eval_output_done(self):
        # "Install plan created."
        pass


    def ver_output(self):
        if self.ver_cur_fmri != None:
            #"Verifying %s" % self.ver_cur_fmri.get_pkg_stem()
            pass
        else:
            #Starting verification
            pass


    def ver_output_error(self, actname, errors):
        # "Verification error occured for %s" % actname
        pass


    def dl_output(self):
        if not self.dl_started:
            self.dl_started = True
            self.set_duration(self.dl_goal_nbytes)
            self.enable_cancel(True)
            self.task_progress(_("Starting download"), self.dl_cur_nbytes)

        self.check_for_interrupt()

        if self.dl_goal_npkgs == 1:
            strn = _("Downloaded %(current_bytes).2f of %(total_bytes).2f MB Overall\n\n" \
                    "Downloading:  %(pkg_name)s") % {
                        'current_bytes': (self.dl_cur_nbytes / 1024.0 / 1024.0),
                        'total_bytes': (self.dl_goal_nbytes / 1024.0 / 1024.0),
                        #"%d/%d" % (self.dl_cur_nfiles, self.dl_goal_nfiles),
                        'pkg_name': self.dl_cur_pkg}
        else:
            strn = _("Downloaded %(current_bytes).2f of %(total_bytes).2f MB Overall\n\n" \
                    "Downloading:  %(pkg_name)s  (%(current_pkg_count)s of %(total_pkg_count)s components)") % {
                        'current_bytes': (self.dl_cur_nbytes / 1024.0 / 1024.0),
                        'total_bytes': (self.dl_goal_nbytes / 1024.0 / 1024.0),
                        #"%d/%d" % (self.dl_cur_nfiles, self.dl_goal_nfiles),
                        'pkg_name': self.dl_cur_pkg,
                        'current_pkg_count': self.dl_cur_npkgs + 1,
                        'total_pkg_count':self.dl_goal_npkgs}

        self.task_progress(strn, self.dl_cur_nbytes)


    def dl_output_done(self):
        self.enable_cancel(False)
        self.check_for_interrupt()
        self.task_progress(_("Download done."), self.dl_goal_nbytes)


    def act_output(self, force=False):
        if self.act_phase == 'Install Phase':
            strn = _("Installing file %(file_number)d of %(total_files)d") % {
                    'file_number':self.act_cur_nactions, 'total_files':self.act_goal_nactions}
        elif self.act_phase == 'Removal Phase':
            strn = _("Removing file %(file_number)d of %(total_files)d") % {
                    'file_number':self.act_cur_nactions, 'total_files':self.act_goal_nactions}
        elif self.act_phase == 'Update Phase':
            strn = _("Updating %(file_number)d of %(total_files)d") % {
                    'file_number':self.act_cur_nactions, 'total_files':self.act_goal_nactions}
        else:
            strn = _("%(action)s %(done_count)d of %(total_count)d") % {
                    'action':self.act_phase, 'done_count':self.act_cur_nactions, 'total_count':self.act_goal_nactions}

        # The first time, emit header.
        if not self.act_started:
            self.act_started = True
            self.task_progress(strn, self.act_cur_nactions)
            self.set_duration(self.act_goal_nactions)

        self.task_progress(strn, self.act_cur_nactions)


    def act_output_done(self):
        self.task_progress(_("Action completed"), self.act_goal_nactions)


    def ind_output(self, force=False):
        if not self.ind_started:
            self.ind_started = True
            self.set_duration(self.ind_goal_nitems)
            self.enable_cancel(False)
            self.task_progress(_("Starting indexing"), self.ind_cur_nitems)

        strn = _("Indexing %(item_number)d of %(item_count)d") % {
                'item_number':self.ind_cur_nitems, 'item_count':self.ind_goal_nitems}

        self.task_progress(strn, self.ind_cur_nitems)


    def ind_output_done(self):
        self.task_progress(_("Indexing completed"), self.ind_goal_nitems)


    def set_image_plan(self, iplan):
        self.iplan = iplan



class ImagePlanTask(AppTask):

    # Issue 1337 - Without this our translations do not get picked up for dl_output etc.
    import wx
    _ = wx.GetTranslation

    def __init__(self, *args, **kwargs):
        AppTask.__init__(self, *args, **kwargs)


    def Run(self):
        self.task_started(self.duration)

        try:
            self.iplan.preexecute()
            self.iplan.execute()
            self.check_for_interrupt()
        except api_errors.WrapSuccessfulIndexingException, e:
            # This is harmless and happens for old style indexed images
            utils.logger.debug("Harmless WrapSuccessfulIndexingException happened for an old image at ImagePlanTask.Run()")
        except TaskInterruptedError:
            self.task_cancelled((task.TASK_END_USER_ABORT, None))
            return
        except:
            self.task_cancelled((task.TASK_END_EXCEPTION, sys.exc_info()))
            return

        self.task_finished()



class ImageUpdateTask(AppTask, KeywordArgsMixin):

    # Issue 1337 - Without this our translations do not get picked up for dl_output etc.
    import wx
    _ = wx.GetTranslation

    def __init__(self, *args, **kwargs):
        """
        @param imageroot: image root directory
        @type imageroot: C{common.fsutils.fsenc} encoded path of the image root directory

        @param op_type: 'install' or 'image-update'. If 'install' is specified, pkg_list must be specified.
        @type op_type: C{str}

        @param pkg_list: list of packages to install/update
        @type op_type: list
        """
        KeywordArgsMixin.__init__(self)
        self.kwset(kwargs, 'imageroot', required=True)
        self.kwset(kwargs, 'op_type', required=True)
        self.kwset(kwargs, 'pkg_list', default=[])
        self.imageplan = None
        AppTask.__init__(self, *args, **kwargs)


    def Run(self):
        self.task_started(self.duration)

        try:
            self._install(self._imageroot, self._op_type)
            self.check_for_interrupt()
        except TaskInterruptedError:
            self.task_cancelled((task.TASK_END_USER_ABORT, None))
            return
        except:
            self.task_cancelled((task.TASK_END_EXCEPTION, sys.exc_info()))
            return

        self.task_finished()


    def _install(self, imgroot, op_type):

        self.enable_cancel(True)
        self.task_progress(_("Starting %s" % op_type), 0)
        self.task_log(_("Starting %s") % op_type) # strftime("%d-%b-%Y %H:%M:%S", localtime()).decode('utf-8'))
        if op_type == 'install':
            self.task_log(_("Add-On to be installed into: %s" % imgroot))

        try:
            tmp_img = image.Image()

            tmp_img.history.client_name = APP_CMD_NAME
            tmp_img.history.operation_name = op_type
            try:
                tmp_img.find_root(fsenc(imgroot))
                if tmp_img.type != image.IMG_USER:
                    msg = _("Not a valid user image: '%s'") % imgroot
                    self.task_log(msg)
                    self.task_progress(msg)
                    raise UpdateToolException(msg)
            except (AssertionError, api_errors.ImageNotFoundException):
                msg = _("Application image not found:\n  '%s'") % imgroot
                self.task_log(msg)
                self.task_progress(msg)
                raise UpdateToolException(msg)

            self.check_for_interrupt()

            self.task_log(_("Loading image configuration"))
            tmp_img.load_config()

            self.dl_started = False
            self.act_started = False
            self.reset() # Reset the progress tracker

            api_inst = api.ImageInterface(fsenc(imgroot),
                                          CLIENT_API_VERSION,
                                          self,  # Progress Tracker
                                          cancel_state_callable=None,
                                          pkg_client_name=APP_CMD_NAME)

            self.check_for_interrupt()
        except api_errors.WrapSuccessfulIndexingException, e:
            # This is harmless and happens for old style indexed images
            utils.logger.debug("Harmless WrapSuccessfulIndexingException happened for an old image at ImageUpdateTask.__install()")
        except api_errors.ImageNotFoundException, e:
            msg = _("Application image not found:\n  '%s'") % e.user_dir
            self.task_log(msg)
            self.task_progress(msg)
            raise UpdateToolException(msg)
        except TaskInterruptedError:
            raise

        try:
            noexecute = False
            if self._plan_install(api_inst, op_type, noexecute) == 0:
                if not noexecute:
                    self.enable_cancel(False)
                    if self._plan_execute(api_inst) == 0:
                        self.task_log(_("Installation successful"))
                        return
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

        except api_errors.WrapSuccessfulIndexingException, e:
            # This is harmless and happens for old style indexed images
            utils.logger.debug("WrapSuccessfulIndexingException happened for an old image at ImageUpdateTask._install")
            self.task_log(_("Old index removed and rebuilt."))
            self.task_log(_("Installation successful"))
            return
        except (UpdateToolException, TaskInterruptedError), e:
            raise
        except Exception, e:
            msg = _("Exception caught: '%s'") % e
            self.task_log(msg)
            self.task_progress(msg)
            utils.logger.error(utils.format_trace())
            utils.logger.error("Exception caught: '%s'" % e)
            return

        self.task_progress("")


    def _plan_install(self, api_inst, op_type, noexecute=False):

        refresh_catalogs = True
        force = False # Don't skip safety checks
        verbose = False
        update_index = False # HACK : Don't update the search indices after the op completes
                            # since doing so removes the pkg_plans from the imageplan which
                            # we need to run configurators
        be_name = None # Rename the newly created boot environment

        try:
            self.task_log(_("Creating install plan"))

            if op_type == 'image-update':
                # cre is either None or a catalog refresh exception which was
                # caught while planning.
                stuff_to_do, dummy_image = \
                    api_inst.plan_update_all(APP_CMD_NAME, refresh_catalogs=refresh_catalogs,
                                     noexecute=noexecute, force=force, verbose=verbose,
                                     update_index=update_index, be_name=be_name)
            elif op_type == 'install':
                stuff_to_do = api_inst.plan_install(
                        self._pkg_list,
                        [],
                        refresh_catalogs=refresh_catalogs,
                        noexecute=noexecute, verbose=verbose,
                        update_index=update_index)

            if not stuff_to_do:
                self.task_log(_("No pending components for this application image"))
                self.task_progress("")
                return
        except api_errors.InventoryException, e:
            msg = _("Inventory exception:\n%s") % e
            self.task_log(msg)
            self.task_progress(_("Inventory exception"))
            raise UpdateToolException(msg)
        except api_errors.CatalogRefreshException, e:
            if self.log_catalog_failures(e) == 0:
                if not noexecute:
                    return
            else:
                msg = self.task_log(_("Catalog refresh failed"))
                self.task_log(msg)
                self.task_progress(msg)
                raise UpdateToolException(msg)
        except api_errors.BEException, e:
            # This is a Boot Environement (BE) Exception which we should never
            # see.
            msg = _("Boot Environement Exception (BEException):\n%s") % e
            self.task_log(msg)
            self.task_progress(_("Boot Environement Exception (BEException)"))
            raise UpdateToolException(msg)
        except api_errors.PlanCreationException, e:
            msg = _("Error creating install plan:\n%s") % e
            self.task_log(_("Error creating install plan:\n%s") % e)
            self.task_progress(_("Error creating install plan"))
            raise UpdateToolException(msg)
        except api_errors.PermissionsException, e:
            self.task_log(_("Error: Insufficient permissions:\n%s") % e)
            self.task_progress(_("Error: Insufficient permissions"))
            raise UpdateToolException(msg)
        except api_errors.IpkgOutOfDateException:
            msg = _("Error: pkg(5) appears to be out of date")
            self.task_log(msg)
            self.task_progress(msg)
            raise UpdateToolException(msg)
        except api_errors.ImageNotFoundException, e:
            msg = _("Application image not found:\n   '%s'") % e.user_dir
            self.task_log(msg)
            self.task_progress(msg)
            raise UpdateToolException(msg)
        except TaskInterruptedError:
            raise
        except Exception, e:
            raise

        if noexecute:
            return

        # Exceptions which happen here are printed in the above level, with
        # or without some extra decoration done here.
        # XXX would be nice to kick the progress tracker.
        try:
            self.task_log(_("Preparing install plan"))
            self.task_progress(_("Preparing install plan"))
            api_inst.prepare()
        except api_errors.TransportError, e:
            msg = _("Error: Transport Error:\n   '%s'") % e
            self.task_log(msg)
            self.task_progress(msg)
            raise UpdateToolException(msg)
        except KeyboardInterrupt:
            msg = _("Error: Keyboard Interrupt")
            self.task_log(msg)
            self.task_progress(msg)
            raise UpdateToolException(msg)
        except api_errors.PermissionsException, e:
            msg = _("Error: Insufficient permissions:\n%s") % e
            self.task_log(_("Error: Insufficient permissions:\n%s") % e)
            self.task_progress(_("Error: Insufficient permissions"))
            raise UpdateToolException(msg)
        except api_errors.ActionExecutionError, e:
            msg = _("Error: Action Execution:\n%s") % e
            self.task_log(msg)
            self.task_progress(msg)
            raise UpdateToolException(msg)
        except TaskInterruptedError:
            raise
        except Exception, e:
            raise

        return 0


    def _plan_execute(self, api_inst):
        try:
            self.task_log(_("Executing install plan"))
            api_inst.execute_plan()
            # HACK
            self.image = api_inst.img
            self.imageplan = api_inst.img.imageplan
            return
        except RuntimeError, e:
            self.task_log(_("Runtime Error:\n%s") % e)
            self.task_progress(_("Runtime Error"))
            utils.logger.error(utils.format_trace())
            utils.logger.error("Runtime Error:\n%s" % e)
            raise
        except api_errors.ImageUpdateOnLiveImageException:
            msg = _("Error: Update cannot be done on a live image")
            self.task_log(msg + " (ImageUpdateOnLiveImageException)")
            self.task_progress(msg)
            raise UpdateToolException(msg)
        except api_errors.CorruptedIndexException, e:
            msg = _("Error: The search index appears to be corrupted")
            self.task_log(msg + _(". Please rebuild the index with 'pkg rebuild-index'."))
            self.task_progress(msg)
            raise UpdateToolException(msg)
        except api_errors.ProblematicPermissionsIndexException, e:
            msg = _("Error: ProblematicPermissionsIndexException:\n%s") % e
            self.task_log(msg)
            self.task_progress(_("Error: Permissions issue"))
            raise UpdateToolException(msg)
        except api_errors.PermissionsException, e:
            msg = _("Error: Insufficient permissions:\n%s") % e
            self.task_log(msg)
            self.task_progress(_("Error: Insufficient permissions"))
            raise UpdateToolException(msg)
        except api_errors.ActionExecutionError, e:
            msg = _("Error: Action Execution:\n%s") % e
            self.task_log(msg)
            self.task_progress(msg)
            raise UpdateToolException(msg)
        except api_errors.BEException, e:
            # This is a Boot Environement (BE) Exception which we should never
            # see.
            msg = _("Boot Environement Exception (BEException):\n%s") % e
            self.task_log(msg)
            self.task_progress(_("Boot Environement Exception (BEException)"))
            raise UpdateToolException(msg)
        except KeyboardInterrupt:
            msg = _("Error: Keyboard Interrupt")
            self.task_log(msg)
            self.task_progress(msg)
            raise UpdateToolException(msg)
        except Exception, e:
            raise


    def log_catalog_failures(self, cre):
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
            elif isinstance(err, api_errors.RetrievalError) and \
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
