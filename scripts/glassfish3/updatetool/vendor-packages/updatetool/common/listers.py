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

import common.info as INFO
from common.boot import safe_decode
from common import ips, utils
from common.mixins import KeywordArgsMixin
from common import lockmanager
from gui import views
import threading
import wx
from wx.lib.newevent import NewCommandEvent
import httplib
import sys
import pkg.client.image as pkgimage
from pkg.client.api_errors import CatalogRefreshException, InventoryException, \
    PlanCreationException, RetrievalError, TransportError

if False:
    import gettext
    _ = gettext.gettext


LISTING_INFORMATION = 0
LISTING_DATA = 1
LISTING_WARNING = 2
LISTING_ERROR = 3
LISTING_LONG_ERROR = 4
LISTING_SUCCESS = 5

ListingEvent, EVT_LISTING_COMPONENT = NewCommandEvent()

class _ListerThread(threading.Thread, KeywordArgsMixin):
    _ = wx.GetTranslation

    def __init__(self, *args, **kwargs):
        KeywordArgsMixin.__init__(self)
        self.kwset(kwargs, 'parent', None, required=True)
        self.kwset(kwargs, 'imagedir', None, required=True)
        self.kwset(kwargs, 'uid', None, required=True)
        self.kwset(kwargs, 'max_recent', 1)
        utils.logger.debug('max_recent: ' + repr(self._max_recent))
        self.kwset(kwargs, 'auto_mark', False)
        threading.Thread.__init__(self)


    def _post(self, etype, status):
        if self._parent:
            evt = ListingEvent(id=self._uid, value=(etype, status))
            wx.PostEvent(self._parent, evt)


    def set_status(self, status):
        self.info(status)


    def info(self, status):
        self._post(LISTING_INFORMATION, status)


    def warning(self, status):
        self._post(LISTING_WARNING, status)


    def error(self, status):
        self._post(LISTING_ERROR, status)
        self.stopped()


    def long_error(self, status):
        self._post(LISTING_LONG_ERROR, status)
        self.stopped()


    def data(self, status):
        self._post(LISTING_DATA, status)


    def success(self, status):
        self._post(LISTING_SUCCESS, status)
        self.stopped()


    def stopped(self):
        lockmanager.lock()
        lockmanager.done(self._imagedir, self._view)
        lockmanager.release()


    def abort_if_needed(self):
        if lockmanager.is_locked():
            return False

        lockmanager.lock()
        ret = False
        if lockmanager.is_aborting(self._imagedir, self._view):
            ret = True
            lockmanager.release()
            self.success(None)
        else:
            lockmanager.release()
        return ret



class InstalledListerThread(_ListerThread):

    _ = wx.GetTranslation

    def __init__(self, *args, **kwargs):
        """
        Generates a listing of installed components in an image. The constructor auto-starts the thread run.

        @keyword parent: The GUI object that should receive the result
        @type parent: C{wx.EvtHandler}

        @keyword imagedir: The image directory to get the components detail for
        @type imagedir: unicode string literal

        @keyword uid: unique id of a component this listers events will be used with. This must
            be unique for all separate ListerThread instances.
        @type uid: int i.e. specifically, the type returned by C{type(wx.GetId(window))}

        @keyword auto_mark: Whether the C{LISTING_DATA} type returned data should have checkmark on or off.
            Default C{False}.
        @type auto_mark: boolean
        """
        _ListerThread.__init__(self, *args, **kwargs)
        self._view = views.INSTALLED
        self.start()


    def run(self):
        """thread run method"""

        try:
            (img, reason) = ips.load_image(self._imagedir, opname='list')
            if img is None:
                self.error(reason)
                return

            if self.abort_if_needed():
                return

            self.set_status(_("Loading components catalog..."))
            success, error_is_remote, remote, errors = ips.catalog_refresh(img, remote=False)
            #Issue 2161.
            #lazy=False will bring the full catalog from server. If lazy=true , the download will start
            #from , where it is left. remote=True will bring the catalog again from remote server.
            #This will happen only if the previous attempt to refresh the catalog fails, locally.
            if not success and not error_is_remote:
                success, error_is_remote, remote, errors = ips.catalog_refresh(img, remote=True, lazy=False)
            if not success:                
                emsg = u"\n".join(safe_decode(x) for x in errors)
                if emsg is None:
                    emsg = u""
                if error_is_remote:
                    if remote:
                        msg = _("Components list could not be refreshed successfully due to a network issue" \
                                " with the following publishers:\n\n%(publishers)s\n\nThe error was:" \
                                "\n\n%(errors)s\n\nThe available components list may not be accurate or complete.") % {
                                        'publishers':"\n".join(remote), 'errors':emsg}
                    else:
                        msg = _("Components list could not be refreshed successfully due to a network issue."\
                                "\n\n%s\n\nThe available components list may not be accurate or complete.") \
                                % emsg
                else:
                    msg = _("Components list could not be refreshed successfully."\
                            "\n\n%s\n\nThe available components list may not be accurate or complete.") \
                            % emsg
                self.warning(msg)

            if self.abort_if_needed():
                return

            self.set_status(_("Loading categories..."))

            categories = ips.load_categories(img)
            if self.abort_if_needed():
                return

            self.set_status(_("Loading categories...done."))

            preferred = img.get_preferred_publisher()

            self.set_status(_("Analyzing components..."))
            for ipkg, state in img.inventory(None, False):
                if self.abort_if_needed():
                    return
                assert state['state'] == pkgimage.PKG_STATE_INSTALLED
                itemCols = []
                itemCols.append(False) # 0 - This is the checkbox field

                if remote and (ipkg.has_publisher() and ipkg.get_publisher() in remote) or \
                    ((not ipkg.has_publisher() or ipkg.preferred_publisher()) and preferred in remote):
                    continue
                self.set_status(_("Getting manifest for %s...") % ipkg)
                try:
                    manifest = ips.get_manifest(img, ipkg, opname='list')[0]
                except:
                    utils.logger.error(utils.format_trace())
                    manifest = None
                if not manifest:
                    self.warning(_("Component manifest could not be obtained for '%s'.\n\n" \
                            "Further component listing won't be performed.") % ipkg)
                    break
                if self.abort_if_needed():
                    return
                self.set_status(_("Getting manifest for %s...done.") % ipkg)
                publisher, fmri_name, version = ips.get_fmri_info(manifest.fmri)
                self.set_status(_("Adding component %s to the list...") % fmri_name)

                display_name = manifest.get('pkg.summary', manifest.get('description', fmri_name))

                itemCols.append(display_name) # 1

                if publisher in categories and fmri_name in categories[publisher]:
                    cat = categories[publisher][fmri_name]
                else:
                    cat = manifest.get('info.classification', '')

                display_cat = cat.split(":")
                if len(display_cat) == 1:
                    itemCols.append(display_cat[0]) #2
                else:
                    itemCols.append(display_cat[1]) #2

                itemCols.append(utils.format_version(version))
                itemCols.append(manifest.get_size()) # 4
                itemCols.append(publisher) # 5

                self.data({'fmri':manifest.fmri, 'size':manifest.get_size(), 'items':itemCols})
                if self.abort_if_needed():
                    return
                self.set_status(_("Adding component %s to the list...done.") % fmri_name)
        except:
            ex = sys.exc_info()[1]
            utils.logger.error(utils.format_trace())
            self.error(str(ex))
            return
        self.success(None)
        return



class UpdatesListerThread(_ListerThread):

    _ = wx.GetTranslation


    def __init__(self, *args, **kwargs):
        """
        Generates a listing of updateable components in an image. The constructor auto-starts the thread run.

        @keyword parent: The GUI object that should receive the result
        @type parent: C{wx.EvtHandler}

        @keyword imagedir: The image directory to get the components detail for
        @type imagedir: unicode string literal

        @keyword uid: unique id of a component this listers events will be used with. This must
            be unique for all separate ListerThread instances.
        @type uid: int i.e. specifically, the type returned by C{type(wx.GetId(window))}

        @keyword max_recent: < 1 for unlimited. Default C{1}.
        @type max_recent: int

        @keyword auto_mark: Whether the C{LISTING_DATA} type returned data should have checkmark on or off.
            Default C{False}.
        @type auto_mark: boolean

        @keyword show_old_updates: Whether the older components, which will
            really be downgrades rather than updates, should be listed or not. Default C{False}.
        @type show_old_updates: boolean

        @keyword security_attr: C{pkg(5)} security attribute name to look for security keywords in
        @type security_attr: string

        @keyword security_keywords: list of security keywords to look for in the security attribute for C{pkg(5)} pkgs.
        @type security_attr: string list
        """
        _ListerThread.__init__(self, *args, **kwargs)
        self.kwset(kwargs, 'show_old_updates', default=False)
        self.kwset(kwargs, 'security_attr', required=True)
        self.kwset(kwargs, 'security_keywords', required=True)
        self._view = views.UPDATES
        self.start()


    def run(self):
        """thread run method"""

        try:
            (img, reason) = ips.load_image(self._imagedir, opname='list')
            if img is None:
                self.error(reason)
                return

            if self.abort_if_needed():
                return

            self.set_status(_("Retrieving components catalog..."))
            success, error_is_remote, remote, errors = ips.catalog_refresh(img, remote=True, lazy=False)
            if not success:
                # Issue 1818 - Messages coming for pkg/python are out of our control so safe_decode them
                # assuming they are partially localized
                emsg = u"\n".join(safe_decode(x) for x in errors)
                if emsg is None:
                    emsg = u""
                if error_is_remote:
                    if remote:
                        msg = _("Components list could not be refreshed successfully due to a network issue" \
                                " with the following publishers:\n\n%(publishers)s\n\nThe error was:" \
                                "\n\n%(errors)s\n\nThe available components list may not be accurate or complete.") % {
                                        'publishers':u"\n".join(remote), 'errors':emsg}
                    else:
                        msg = _("Components list could not be refreshed successfully due to a network issue." \
                                "\n\n%s\n\nThe available components list may not be accurate or complete.") \
                                % emsg
                else:
                    msg = _("Components list could not be refreshed successfully." \
                            "\n\n%s\n\nThe available components list may not be accurate or complete.") \
                            % emsg
                self.warning(msg)
            else:
                self.set_status(_("Retrieving components catalog...done."))

            if self.abort_if_needed():
                return

            updates_to_from = []

            if self._max_recent != 1: # view more than one case
                self.set_status(_("Generating installed inventory..."))
                upgradable_fmris = [ipkg for ipkg, state in img.inventory(None, False) if  state['upgradable']]
                self.set_status(_("Generating installed inventory...done."))
                if self.abort_if_needed():
                    return

                if upgradable_fmris:
                    # Cache the inventory once rather than regenerating it for each upgradable_fmris
                    # to compare with
                    inventory = list(img.inventory(None, True))
                    if self.abort_if_needed():
                        return

                    for installed in upgradable_fmris:
                        self.set_status(_("Inspecting %s...") % installed)
                        if self.abort_if_needed():
                            return

                        for ipkg, state in inventory:
                            if self.abort_if_needed():
                                return

                            if ipkg.is_same_pkg(installed) and \
                                    state['state'] == pkgimage.PKG_STATE_KNOWN and \
                                    (ipkg.is_successor(installed) or
                                            # debug option
                                            (self._show_old_updates and installed.is_successor(ipkg))):
                                updates_to_from.append((ipkg, installed))
                        self.set_status(_("Inspecting %s...done.") % installed)
                    del inventory

                ips.keep_n_newest_fmris(updates_to_from, self._max_recent)

            else: # only the latest update
                if self.abort_if_needed():
                    return
                try:
                    self.set_status(_("Calculating updates..."))
                    pkg_plans = ips.get_list_of_updates(img, opname='list')
                    self.set_status(_("Calculating updates...done."))
                except PlanCreationException, err:
                    val = sys.exc_info()[1]
                    utils.logger.error(utils.format_trace())
                    if val.constraint_violations:
                        self.error(_("Conflicting updates possibilities were detected.\n\nFor example, this can happen "\
                                "when updating a complex component dependency will try to downgrade something else " \
                                "that is already installed.\n\nThe detailed error was:\n\n%(error)s\n\n"
                                "Please select '%(show_all_versions_menu_label)s' from the '%(view_menu_label)s' "\
                                "menu to select the ones you want to install") % {
                                    'error':str(err),
                                    'show_all_versions_menu_label':_("Show All Versions"),
                                    'view_menu_label':_("View")})
                    else:
                        self.error(_("Could not plan the updates.\n\n" \
                                "The detailed error was:\n\n%(error)s\n\nYou can try to\n" \
                                "\n" \
                                "1) Select '%(show_all_versions_menu_label)s' from the '%(view_menu_label)s' menu\n" \
                                "or\n" \
                                "2) Perform a refresh") % {
                                    'error':str(err),
                                    'show_all_versions_menu_label':_("Show All Versions"),
                                    'view_menu_label':_("View")})
                    return
                except (httplib.HTTPException, InventoryException,
                        TransportError, RetrievalError,
                        CatalogRefreshException), err:
                    utils.logger.error(utils.format_trace())
                    self.error(_("Could not plan the updates.\n\nThere was a problem retrieving information " \
                            "from the remote server.\n\nThe detailed error was:\n\n%(error)s") % {'error':str(err)})
                    return
                except:
                    utils.logger.error(utils.format_trace())
                    self.long_error((
                        _("An unexpected error occured.\nPlease report the following" \
                            " error to %(email)s.") % {'email':INFO.REPORT_TO},
                        utils.format_trace()))
                    return

                if not pkg_plans:
                    self.success(None)
                    return

                for pp in pkg_plans:
                    if self.abort_if_needed():
                        return
                    # Don't show components which got pulled in due to
                    # dependencies but aren't actually installed
                    if pp.origin_fmri is not None:
                        updates_to_from.append((pp.destination_fmri, pp.origin_fmri))

            preferred = img.get_preferred_publisher()
            if self.abort_if_needed():
                return

            inv_all = list(img.inventory(None, True))
            if self.abort_if_needed():
                return

            for new_fmri, old_fmri in updates_to_from:
                if self.abort_if_needed():
                    return
                if old_fmri is None: # Be extra safe for "View all" case
                    continue
                itemCols = []
                itemCols.append(self._auto_mark) # 0 - This is the checkbox field

                if remote and (new_fmri.has_publisher() and new_fmri.get_publisher() in remote) or \
                    ((not new_fmri.has_publisher() or new_fmri.preferred_publisher()) and preferred in remote):
                    continue
                if remote and (old_fmri.has_publisher() and old_fmri.get_publisher() in remote) or \
                    ((not old_fmri.has_publisher() or old_fmri.preferred_publisher()) and preferred in remote):
                    continue
                if self.abort_if_needed():
                    return

                security = False
                if self._max_recent == 1:
                    self.set_status(_("Checking security status of the updates for %s...") % old_fmri)
                    # HACK : This might be made more efficient by
                    # 1) Checking for new_fmri first
                    # 2) Checking only for this component's fmris if possible rather than the whole inventory
                    for ipkg, state in inv_all:
                        if self.abort_if_needed():
                            return
                        if ipkg.is_same_pkg(old_fmri) and \
                            state['state'] == pkgimage.PKG_STATE_KNOWN and \
                                                             ipkg.is_successor(old_fmri):
                            try:
                                manifest = ips.get_manifest(img, ipkg)[0]
                            except:
                                continue
                            if not manifest: # manifest could not be retrieved for some reason
                                continue
                            value = manifest.get(self._security_attr, None)

                            if value and value in self._security_keywords:
                                security = True
                                break
                else:
                    # We will calculate the security flag later to avoid some
                    # duplicate code
                    pass

                self.set_status(_("Getting manifest for %s...") % new_fmri)
                try:
                    new_manifest = img.get_manifest(new_fmri)
                except:
                    utils.logger.error(utils.format_trace())
                    new_manifest = None
                if not new_manifest:
                    self.warning(_("Component manifest could not be obtained for '%s'.\n\n"
                        "Further component listing won't be performed.") % new_fmri)
                    break
                self.set_status(_("Getting manifest for %s...") % old_fmri)
                try:
                    old_manifest = img.get_manifest(old_fmri)
                except:
                    utils.logger.error(utils.format_trace())
                    old_manifest = None
                if not old_manifest:
                    self.warning(_("Component manifest could not be obtained for '%s'.\n\n"
                        "Further component listing won't be performed.") % old_fmri)
                    break
                self.set_status(_("Getting manifest for %s...done.") % old_fmri)

                publisher, fmri_name, version = ips.get_fmri_info(new_manifest.fmri)

                self.set_status(_("Adding component %s to the list...") % fmri_name)

                display_name = new_manifest.get('pkg.summary', new_manifest.get('description', fmri_name))

                # Check if there is a detailed URL list. At the time of this
                # writing it is not clear if the attribute will use an underscore
                # or a dash -- so we accept both
                url_str = new_manifest.get('pkg.detailed_url', new_manifest.get('pkg.detailed-url', None))

                itemCols.append(display_name) # 1

                if self._max_recent != 1:
                    # We didn't calculate this earlier due to the need to get
                    # the new manifest for info anyway
                    if self._security_attr and self._security_keywords:
                        value = new_manifest.get(self._security_attr, None)
                        if value and value in self._security_keywords:
                            security = True

                itemCols.append(security) #2
                itemCols.append(version.get_timestamp()) # 3
                itemCols.append(utils.format_version(version)) # 4
                itemCols.append(utils.format_version(ips.get_fmri_info(old_fmri)[2])) # 5
                psize = ips.get_download_size_delta(old_manifest, new_manifest)
                itemCols.append(psize) # 6
                itemCols.append(publisher) # 7

                self.data({'fmri':new_manifest.fmri, 'size':psize, 'items':itemCols, 'imageplan':img.imageplan, 'detailed-url':url_str})
                if self.abort_if_needed():
                    return
                self.set_status(_("Adding component %s to the list...done.") % fmri_name)
            del inv_all
        except:
            ex = sys.exc_info()[1]
            utils.logger.error(utils.format_trace())
            self.error(str(ex))
            return
        self.success(None)
        return



class AvailableListerThread(_ListerThread):

    _ = wx.GetTranslation

    def __init__(self, *args, **kwargs):
        """
        Generates a listing of available components which can be installed in an image. The constructor auto-starts the thread run.

        @keyword parent: The GUI object that should receive the result
        @type parent: C{wx.EvtHandler}

        @keyword imagedir: The image directory to get the components detail for
        @type imagedir: unicode string literal

        @keyword uid: unique id of a component this listers events will be used with. This must
            be unique for all separate ListerThread instances.
        @type uid: int i.e. specifically, the type returned by C{type(wx.GetId(window))}

        @keyword max_recent: < 1 for unlimited. Default C{1}.
        @type max_recent: int

        @keyword auto_mark: Whether the C{LISTING_DATA} type returned data should have checkmark on or off.
            Default C{False}.
        @type auto_mark: boolean

        @keyword pre_mark: Whether a specific component should be checkmarked or not. The C{auto_mark} and this list option are C{or}ed.
            Default C{[]}.
        @type auto_mark: list of fmris
        """
        _ListerThread.__init__(self, *args, **kwargs)
        self.kwset(kwargs, 'pre_mark', [], required=False)
        self._view = views.AVAILABLE
        self.start()


    def run(self):
        """thread run method"""

        try:
            (img, reason) = ips.load_image(self._imagedir, opname='list')
            if img is None:
                self.error(reason)
                return

            if self.abort_if_needed():
                return

            self.set_status(_("Retrieving components catalog..."))
            success, error_is_remote, remote, errors = ips.catalog_refresh(img, remote=True)
            #Issue 2161. HACK:
            #lazy=False will bring the full catalog from server. If lazy=true , the download will start
            #from , where it is left. remote=True will bring the catalog again from remote server.
            #This will happen only if the previous attempt to refresh the catalog fails.
            if not success and not error_is_remote:
                success, error_is_remote, remote, errors = ips.catalog_refresh(img, remote=True, lazy=False)
            if self.abort_if_needed():
                return
            if not success:
                # Issue 1818 - Messages coming for pkg/python are out of our control so safe_decode them
                # assuming they are partially localized
                emsg = u"\n".join(safe_decode(x) for x in errors)
                if emsg is None:
                    emsg = u""
                if error_is_remote:
                    if remote:
                        msg = _("Components list could not be refreshed successfully due to a network issue" \
                                " with the following publishers:\n\n%(publishers)s\n\nThe error was:" \
                                "\n\n%(errors)s\n\nThe available components list may not be accurate or complete.") % {
                                        'publishers':u"\n".join(remote), 'errors':emsg}
                    else:
                        msg = _("Components list could not be refreshed successfully due to a network issue." \
                                "\n\n%s\n\nThe available components list may not be accurate or complete.") \
                                % emsg
                else:
                    msg = _("Components list could not be refreshed successfully."\
                            "\n\n%s\n\nThe available components list may not be accurate or complete.") \
                            % emsg
                self.warning(msg)
            else:
                self.set_status(_("Retrieving components catalog...done."))

            if self.abort_if_needed():
                return

            self.set_status(_("Loading categories..."))
            categories = ips.load_categories(img)
            self.set_status(_("Loading categories...done."))

            if self.abort_if_needed():
                return

            self.set_status(_("Generating installed inventory..."))
            installed_fmris = [ipkg for ipkg, dummy in img.inventory(None, False)]

            if self.abort_if_needed():
                return

            self.set_status(_("Generating all inventory..."))
            not_installed_fmris = []
            all_inventory = [ipkg for ipkg, dummy in img.inventory(None, True)]

            if self.abort_if_needed():
                return

            self.set_status(_("Analyzing components..."))
            for ipkg in all_inventory:
                if self.abort_if_needed():
                    return

                have = False
                for installed in installed_fmris:
                    if self.abort_if_needed():
                        return
                    if ipkg.is_same_pkg(installed):
                        have = True
                        break

                if not have:
                    not_installed_fmris.append(ipkg)

            if self._max_recent == 1:
                ips.keep_preferred_or_newest_fmris(not_installed_fmris)
            elif self._max_recent > 1:
                ips.keep_n_newest_fmris(not_installed_fmris, self._max_recent)
            else:
                # keep them all
                pass

            self.set_status(_("Analyzing components...done."))

            preferred = img.get_preferred_publisher()

            for fmri in not_installed_fmris:
                if self.abort_if_needed():
                    return
                # ips.dump_fmri(fmri, image=img, img.get_pkg_state_by_fmri(fmri), preferred_publisher)
                itemCols = []
                itemCols.append(False) # 0 - This is the checkbox field

                if remote and (fmri.has_publisher() and fmri.get_publisher() in remote) or \
                    ((not fmri.has_publisher() or fmri.preferred_publisher()) and preferred in remote):
                    continue
                self.set_status(_("Getting manifest for %s...") % fmri)
                try:
                    manifest = img.get_manifest(fmri)
                except:
                    utils.logger.error(utils.format_trace())
                    manifest = None
                if not manifest:
                    self.warning(_("Component manifest could not be obtained for '%s'.\n\n"
                        "Further component listing won't be performed.") % fmri)
                    break
                self.set_status(_("Getting manifest for %s...done.") % fmri)
                publisher, fmri_name, version = ips.get_fmri_info(fmri)
                self.set_status(_("Adding component %s to the list...") % fmri_name)

                display_name = manifest.get('pkg.summary', manifest.get('description', fmri_name))

                itemCols.append(display_name) # 1

                if publisher in categories and fmri_name in categories[publisher]:
                    cat = categories[publisher][fmri_name]
                else:
                    cat = manifest.get('info.classification', '')

                display_cat = cat.split(":")
                if len(display_cat) == 1:
                    itemCols.append(display_cat[0]) #2
                else:
                    itemCols.append(display_cat[1]) #2

                itemCols.append(version.get_timestamp()) # 3
                itemCols.append(utils.format_version(version)) # 4
                itemCols.append(manifest.get_size())  # 5
                itemCols.append(publisher)  # 6

                check = self._auto_mark
                if not check and self._pre_mark:
                    for x in self._pre_mark:
                        if fmri.is_same_pkg(x):
                            itemCols[0]=True
                            break

                self.data({'fmri':fmri, 'size':manifest.get_size(), 'items':itemCols, 'check':check})
                if self.abort_if_needed():
                    return
                self.set_status(_("Adding component %s to the list...done.") % fmri_name)
        except:
            ex = sys.exc_info()[1]
            utils.logger.error(utils.format_trace())
            self.error(str(ex))
            return
        self.success(None)
        return


class NewSWListerThread(_ListerThread):

    _ = wx.GetTranslation


    def __init__(self, *args, **kwargs):
        """
        Generates a dict that associates installed images with BasicFeed
        entries for Add-on software.  Generates a list representing pkg(5)
        based software that is not installed.  The constructor auto-starts the
        thread run.

        @keyword parent: The GUI object that should receive the result
        @type parent: C{wx.EvtHandler}

        @keyword imagedir: The image directory to get the components detail for
        @type imagedir: unicode string literal

        @keyword uid: unique id of a component this listers events will be used with. This must
            be unique for all separate ListerThread instances.
        @type uid: int i.e. specifically, the type returned by C{type(wx.GetId(window))}

        """

        _ListerThread.__init__(self, *args, **kwargs)
        self.kwset(kwargs, 'feed_addon_entries', required=True)
        self.kwset(kwargs, 'feed_newsw_entries', required=True)
        self.kwset(kwargs, 'image_list', required=True)
        self._view = views.UPDATES
        self.start()


    def run(self):
        """thread run method"""

        # We build an entry_image dict.  It is indexed by the basic feed
        # entry's ID which is unique.  Each entry_image has two sub-items:
        #      'feed_entry'   The feed entry to which the ID is associated with
        #      'image_list'   A list of images the entry applys to

        import common.basicfeed as BF

        entry_image_dict = {}

        for img_path in self._image_list:
            if self.abort_if_needed():
                return
            filtered_entries = ips.filter_addon_entries([img_path],
                                                       self._feed_addon_entries)

            # assert that each filtered_entry is associated with at least
            # one installed image.

            for fe in filtered_entries:
                if fe[BF.ID] not in entry_image_dict:
                    entry_image_dict[fe[BF.ID]] = {}
                    entry_image_dict[fe[BF.ID]]['feed_entry'] = fe
                    entry_image_dict[fe[BF.ID]]['image_list'] = []

                entry_image_dict[fe[BF.ID]]['image_list'].append(img_path)

        # We build a list of basic feed entries that have not be installed
        # on the target system.
        filtered_entries = ips.filter_application_entries(self._image_list,
                                                       self._feed_newsw_entries)

        # SW Update does not support "other" newsw - so we filter those out
        # here.
        newsw_entries = []
        for fe in filtered_entries:
            if fe[BF.APP_TYPE] != 'other':
                newsw_entries.append(fe)

        if entry_image_dict or newsw_entries != []:
            self.data({'addon_dict':entry_image_dict,
                       'newsw_list':newsw_entries})

        self.success(None)
