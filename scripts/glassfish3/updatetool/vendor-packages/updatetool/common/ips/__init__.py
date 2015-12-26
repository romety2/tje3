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

"""Interface to IPS, the Image Packing System"""
from common.fsutils import fsenc, fsdec
import common.info as INFO
from common.fileutils import canonical_path
from common import messages
import os.path
import sys
from StringIO import StringIO
import urllib2
import urlparse
import socket
import httplib
import shutil

import pkg.misc as pkgmisc
import pkg.client.image as pkgimage
from pkg.client.progress import QuietProgressTracker, NullProgressTracker
from pkg.client.api_errors import ImageNotFoundException, CatalogRefreshException, \
    PublisherError, InvalidDepotResponseException, PermissionsException, \
    InconsistentIndexException, IncorrectIndexFileHash, ProblematicSearchServers, \
    SlowSearchUsed, BooleanQueryException, RetrievalError, TransportError
from pkg.client import global_settings
from pkg.updatelog import UpdateLogException
import pkg.fmri
from pkg.fmri import PkgFmri
import itertools
from pkg.client.api import ImageInterface, PackageInfo, Query
from pkg.client.publisher import Publisher, Repository

import gettext
_ = gettext.gettext

import common.utils as utils
import common.basicfeed as BF

# Package attributes we look for. The final value for these is still TBD
INFO_URL_ATTR           = "com.sun.service.info_url"
SECURITY_UPDATE_ATTR    = "com.sun.service.keywords"

# Keyword used to indicate a package has a security fix
SECURITY_UPDATE_KEYWORD = "security"

# version of the pkg(5) client API that we are using
CLIENT_API_VERSION = 21

def dump_fmri(fmri, state=None, image=None, preferred_publisher=None):
    utils.logger.debug("fmri                                                = [%s]" % fmri)
    utils.logger.debug("fmri.publisher                                      = [%s]" % fmri.publisher)
    utils.logger.debug("preferred_publisher                                 = [%s]" % repr(fmri.preferred_publisher()))
    utils.logger.debug("get_publisher                                       = [%s]" % fmri.get_publisher())
    utils.logger.debug("get_short_fmri                                      = [%s]" % fmri.get_short_fmri())
    utils.logger.debug("get_fmri()                                          = [%s]" % fmri.get_fmri())

    st = None
    if state is not None:
        st = state
    elif image is not None:
        st = image.get_pkg_state_by_fmri(fmri)

    if st is not None:
        utils.logger.debug("state = %s" % st)

    if image is not None:
        utils.logger.debug("<image>.get_pkg_pub_by_fmri()                      = [%s]" % image.get_pkg_pub_by_fmri(fmri))

    pa = None
    if preferred_publisher is not None:
        pa = preferred_publisher
    elif image is not None:
        pa = image.get_preferred_publisher()

    if pa is not None:
        utils.logger.debug("get_short_fmri(default publisher=specified)         = [%s] (publisher = %s)" % (fmri.get_short_fmri(default_publisher=pa), pa))
        utils.logger.debug("get_fmri(default_publisher=specified)               = [%s] (publisher = %s)" % (fmri.get_fmri(default_publisher=pa), pa))
        utils.logger.debug("get_fmri(default publisher=specified, anarchy=True) = [%s] (publisher = %s)" % (fmri.get_fmri(default_publisher=pa, anarchy=True), pa))
        utils.logger.debug("pkg.fmri.is_same_publisher(default %s) = %s" % (pa, pkg.fmri.is_same_publisher(pa, fmri.get_publisher())))


def get_python_image_path(opname=None):
    img = get_user_image_rootdir(sys.executable, opname=opname)
    if img is None:
        return ""
    return img


def keep_preferred_or_newest_fmris(fmri_list):
    """
    Keeps the preferred newest version if available, which may be older than non-preferred versions,
    otherwise keeps one of the newest randomly from other publishers

    NOTE: Operates IN-PLACE
    """
    length = len(fmri_list) - 1
    i = 0
    while i < length:
        j = i + 1
        while j <= length:
            ii = fmri_list[i]
            cii = fmri_list[j]
            if ii.is_same_pkg(cii):
                if ii.is_successor(cii) and (ii.preferred_publisher() or not cii.preferred_publisher()):
                    fmri_list.pop(j)
                    length -= 1
                else:
                    fmri_list[i], fmri_list[j] = fmri_list[j], fmri_list[i]
                    fmri_list.pop(j)
                    length -= 1
            else:
                j += 1
        i += 1
    return fmri_list


def keep_newest_fmris(fmri_list):
    keep_n_newest_fmris(fmri_list, 1)


def keep_n_newest_fmris(fmri_list, n=-1):
    """
    Keeps at most n newest versions of a package in fmri_list. Operates in place. Element order is
    not maintained.
    """
    if n == 0:
        fmri_list = []
        return
    if n == -1:
        return
    length = len(fmri_list)
    if length == 0:
        return
    fmri_list.sort(reverse=True)
    i = 0
    this_cnt = 0
    is_tuple = (type(fmri_list[0]) == type(()))
    while i < length:
        #utils.logger.debug(fmri_list[i])
        if i == 0:
            #utils.logger.debug("Keeping" + str(fmri_list[i]))
            this_cnt = 1
            i += 1
        elif ((is_tuple and not fmri_list[i][0].is_same_pkg(fmri_list[i-1][0]))
                or (not is_tuple and not fmri_list[i].is_same_pkg(fmri_list[i-1]))):
            #utils.logger.debug("Keeping" + str(fmri_list[i]))
            this_cnt = 1
            i += 1
        elif this_cnt < n:
            #utils.logger.debug("Keeping" + str(fmri_list[i]))
            this_cnt += 1
            i += 1
        else:
            #utils.logger.debug("Removing" + str(fmri_list[i]))
            fmri_list.pop(i)
            length -= 1


def create_image(image_dir, image_title, pub_name, pub_url, ssl_key=None, ssl_cert=None, opname=None):
    """Throws exception on failure. Returns nothing on success."""
    assert isinstance(pub_url, str)
    img = pkgimage.Image()
    img.history.client_name = INFO.CMD_NAME
    if opname:
        img.history.operation_name = opname
    else:
        img.history.operation_name = "image-create"
    is_zone = False

    img.set_attrs(pkgimage.IMG_USER, image_dir, is_zone, pub_name, pub_url,
                  ssl_key, ssl_cert)

    img.set_property('title', image_title)
    return img


def destroy_image(image_dir):
    """Throws exception on failure. Returns nothing on success."""
    # Make sure image_dir is a USER image
    img = pkgimage.Image()
    if img.image_type(image_dir) == pkgimage.IMG_USER:
        shutil.rmtree(image_dir)
    else:
        raise AssertionError("Not a user image: %s" % image_dir)


def get_user_image_object(imagedir, opname=None):
    """Returns the IPS image object for imagedir (user images only) or None if there is None"""
    img = pkgimage.Image()
    img.history.client_name = INFO.CMD_NAME
    if opname:
        img.history.operation_name = opname
    try:
        img.find_root(imagedir)
        if img.type == pkgimage.IMG_USER:
            return img
        else:
            return None
    except ImageNotFoundException:
        utils.logger.debug("Image not found at %s" % fsdec(imagedir))
        return None


def get_user_image_rootdir(imagedir, opname=None):
    """Returns the IPS image root directory for imagedir if there is None"""
    img = get_user_image_object(imagedir, opname=opname)
    if img:
        return img.get_root()
    return None


def get_image_title(imgrootdir, opname=None):
    """returns the slightly decorated directory itself on error"""
    val = get_image_property(imgrootdir, "title", opname=opname)
    if val is None:
        return fsdec(imgrootdir)
    return val


def set_image_title(imgrootdir, u_title, opname=None):
    set_image_property(imgrootdir, "title", u_title, opname=opname)


def set_image_description(image, u_desc, opname=None):
    set_image_property(image, "description", u_desc, opname=opname)


def get_image_description(imgrootdir, opname=None):
    """
    Returns unicode description if one is available, empty string otherwise
    """
    val = get_image_property(imgrootdir, "description", opname=opname)
    if val is None:
        return u""
    return val


def _get_image_object_property(image, prop, opname=None):
    try:
        if opname:
            image.history.operation_name = opname
        image.load_config()
    except (RuntimeError, ValueError, httplib.HTTPException):
        utils.logger.error("Could not fetch image property '%s'\n%s", (prop, utils.format_trace()))
        return None
    try:
        return image.get_property(prop)
    except KeyError:
        return None


def _get_image_dir_property(imgrootdir, prop, opname=None):
    """returns None on error"""
    assert imgrootdir is not None, "invalid parameter to get_image_property"
    img = pkgimage.Image()
    img.history.client_name = INFO.CMD_NAME
    if opname:
        img.history.operation_name = opname
    try:
        img.find_root(imgrootdir)
        if img.type != pkgimage.IMG_USER:
            return None
    except ImageNotFoundException:
        utils.logger.debug("Could not fetch image property '%s' as image could not be found", prop)
        return None
    return get_image_property(img, prop, opname=opname)


def get_image_property(image, prop, opname=None):
    if isinstance(image, basestring):
        return _get_image_dir_property(image, prop, opname=opname)
    elif isinstance(image, pkgimage.Image):
        return _get_image_object_property(image, prop, opname=opname)
    else:
        raise TypeError, _("Invalid argument type")


def set_image_property(image, name, value, opname=None):
    if isinstance(image, basestring):
        _set_image_dir_property(image, name, value, opname=opname)
    elif isinstance(image, pkgimage.Image):
        _set_image_object_property(image, name, value, opname=opname)
    else:
        raise TypeError, _("Invalid argument type")


def _set_image_dir_property(imgrootdir, name, value, opname=None):
    assert imgrootdir is not None, "invalid parameter to get_image_property"
    img = pkgimage.Image()
    img.history.client_name = INFO.CMD_NAME
    if opname:
        img.history.operation_name = opname
    try:
        img.find_root(imgrootdir)
        if img.type != pkgimage.IMG_USER:
            return
        img.load_config()
    except ImageNotFoundException:
        utils.logger.debug("Could not set image property '%s' to '%s' as image could not be found.", (name, value))
        return
    _set_image_object_property(img, name, value, opname=opname)


def _set_image_object_property(img, name, value, opname=None):
    if opname:
        img.history.operation_name = opname
    img.set_property(name, value)


def has_installed_pkgs(imagedir, landmark_pkgs):
    '''
    Check if a list of packages are installed in an image.
    landmark_pkgs is a list of package names. If imagedir has the
    packages described by landmark_pkgs installed in it then return True,
    else return False
    '''
    if landmark_pkgs is None or len(landmark_pkgs) < 1:
        return False

    img = ImageInterface(imagedir, pkg.client.api.CURRENT_API_VERSION,
                         NullProgressTracker(), None, None)
    # Get infor for the landmark pkgs
    info = img.info(fmri_strings=list(landmark_pkgs), local=True,
                    info_needed=set([PackageInfo.IDENTITY, PackageInfo.STATE]))

    # Get list of landmark packgaes that are installed
    installed_landmarks = info[ImageInterface.INFO_FOUND]
    # If the number of landmark_pkgs installed equals the number of
    # landmark packages we checked for, then the landmarks are installed
    if len(landmark_pkgs) == len(installed_landmarks):
        return True
    else:
        return False


def has_origins(imagedir, origin_urls=None):
    '''
    Check if the specified imagedir contains publishers that have
    publishers with origins that match the passed origin_urls
    '''
    if origin_urls is None:
        return True

    match = False
    # Load publishers for image
    publishers = get_publishers(imagedir, include_disabled=False)

    if publishers is None:
        return False

    # Make sure all origin URLs match some publisher in imagedir
    for url in origin_urls:
        match = False
        for a in publishers:
            if _matching_origins(url, a[1]):
                match = True
                break
        if not match:
            # One of the passed origin URLs is not contained in any publisher
            return False

    return match


def _matching_origins(url1, url2):
    '''
    Two origins are considered matching if the initial parts of the
    two urls match.
    '''
    if len(url1) == len(url2):
        return url1 == url2
    elif len(url1) > len(url2):
        return url1.startswith(url2)
    else:
        return url2.startswith(url1)


def get_publishers(imagedir, opname=None, include_disabled=True):
    """
    Returns a lists of
    (pubname, puburl, preferred, ssl_key, ssl_cert, disabled) tuples
    for an existing image

    Can raise a ValueError if the imagedir is not a valid image
    """
    pubs = []
    img = pkgimage.Image()
    img.history.client_name = INFO.CMD_NAME
    if opname:
        img.history.operation_name = opname
    try:
        img.find_root(imagedir) # can raise ValueError: if it is not an install image
        if img.type != pkgimage.IMG_USER:
            return
    except ImageNotFoundException:
        utils.logger.debug("Could not get publishers as image could not be found")
        return
    img.load_config()
    preferred_publisher = img.get_preferred_publisher()
    for a in img.gen_publishers(inc_disabled = include_disabled):
        pubs.append((a["prefix"], a["origin"], a["prefix"] == preferred_publisher,
            a["ssl_key"], a["ssl_cert"], a["disabled"] ))

    # if not pubs:
    #    utils.logger.err("An exisiting image had no publishers defined.")
    del img, preferred_publisher
    return pubs


def set_publishers(imagedir, new_pubs, opname=None):
    """
    Takes an existing image with some set of pubs to a target set of pubs. The algorithm
    works based on pkg set-publisher behavior

    new_pubs is a list of tuples containing (pubname, origin, preferred flag, ssl key, ssl cert, disabled flag)
    """
    if not new_pubs:
        return (False, _("No publishers to set"))
    n_p_pubs = [a for a in new_pubs if a[2]]
    if len(n_p_pubs) != 1:
        return (False, _("Unexpected number of preferred publishers encountered."))
    old_pubs = get_publishers(imagedir, opname=opname)
    old_names = [a[0] for a in old_pubs]
    new_names = [a[0] for a in new_pubs]
    modify = []
    try:
        img = ImageInterface(imagedir, CLIENT_API_VERSION,
                    QuietProgressTracker(), None, INFO.CMD_NAME)
    except ImageNotFoundException, e:
        return (False, _("'%s' is not an install image") % e.user_dir)

    # NOTE: this uses a private field (img).  The ImageInterface class doesn't
    # provide a way to get the type of the image.
    if img.img.type != pkgimage.IMG_USER:
        return (False, _("'%s' is not a supported install image") % imagedir)

    # add new pub and save the rest for possible modification
    for new_pub, new_url, preferred, new_ssl_key, new_ssl_cert, disabled in new_pubs:
        if not new_pub in old_names:
            try:
                repo = Repository()
                pub = Publisher(new_pub, repositories=[repo])
                pub.disabled = disabled
                repo.add_origin(new_url, ssl_key=new_ssl_key, ssl_cert=new_ssl_cert)
                img.add_publisher(pub, refresh_allowed=not disabled)
                if preferred:
                    img.set_preferred_publisher(prefix=pub.prefix)
            except PublisherError, e:
                return (False, str(e))
            except CatalogRefreshException, e:
                return (False, _("Could not refresh the catalog for %s") % pub)
            except InvalidDepotResponseException, e:
                text = _("The origin URIs for '%(pubname)s' do not appear to point to a "
                    "valid pkg server.\nPlease check the server's address and "
                    "client's network configuration."
                    "\nAdditional details:\n\n%(details)s") % {'pubname': pub.prefix, 'details': e}
                return (False, text)
            except PermissionsException, e:
                return (False, str(e))
        else:
            modify.append((new_pub, new_url, preferred, new_ssl_key, new_ssl_cert, disabled))

    # if the old preferred publisher is being disabled and a different
    # publisher is being made preferred, we have to set the new preferred
    # publisher before we disable the old one, because we cannot disable the
    # preferred publisher.  To do this, we sort the modify list so that enabled
    # publishers are first.
    modify.sort(lambda x, y: cmp(x[5], y[5]))

    # modify the remaining as needed
    for old_name, new_url, preferred, new_ssl_key, new_ssl_cert, disabled in modify:
        try:
            pub = img.get_publisher(prefix=old_name, alias=old_name, duplicate=True)
            pub.disabled = disabled
            origin = pub.selected_repository.origins[0]
            origin.uri = new_url
            origin.ssl_cert = new_ssl_cert
            origin.ssl_key = new_ssl_key
            img.update_publisher(pub, refresh_allowed=not disabled)
            if preferred:
                img.set_preferred_publisher(prefix=old_name)
        except CatalogRefreshException, e:
            return (False, _("Could not refresh the catalog for %s") % pub)
        except InvalidDepotResponseException, e:
            text = _("The origin URIs for '%(pubname)s' do not appear to point to a "
                "valid pkg server.\nPlease check the server's address and "
                "client's network configuration."
                "\nAdditional details:\n\n%(details)s") % {'pubname': pub.prefix, 'details': e}
            return (False, text)
        except PermissionsException, e:
            return (False, str(e))

    # remove pubs no longer there
    for old_name in old_names:
        if not old_name in new_names:
            try:
                img.remove_publisher(prefix=old_name, alias=old_name)
            except (PermissionsException, PublisherError), e:
                return (False, _("Unable to remove publisher %(pubname)s: %(details)s") %
                    {'pubname': old_name, 'details': str(e)})

    return (True, None)


def get_security_defs(config=None):
    """
    Returns a tuple containing security attribute name and a list of security
    keywords in that attribute for C{pkgs(5)} pkgs.

    @param config: The config instance to check for getting the definitions
    @type config: X{common.preferences.Preferences}
    @return: a two elements tuple containing security attribute name and a
        list of security keywords in that attribute for C{pkgs(5)} pkgs.
    """
    security_attr = keywords = None
    security_keywords = []

    if config and config.has_section('main'):
        if config.has_option('main', '_security_update_attr'):
            security_attr = config.get('main', '_security_update_attr')
        else:
            security_attr = SECURITY_UPDATE_ATTR

        if config.has_option('main', '_security_update_attr'):
            keywords = config.get('main', '_security_update_keywords')
        else:
            keywords = SECURITY_UPDATE_KEYWORD
    if keywords:
        security_keywords = [x.strip() for x in keywords.split(',')]
    return (security_attr, security_keywords)


def enumerate_pkgs(imagedir, check_type="updates", security_attr="info.keywords", security_keywords=None, client=INFO.CLIENT_NAME, opname=None):
    assert client in [INFO.CLIENT_NAME, INFO.NOTIFIER_CLIENT_NAME]
    if security_keywords is None:
        security_keywords = ["security"]

    img = pkgimage.Image()
    global_settings.client_name = img.history.client_name = client
    if opname:
        img.history.operation_name = opname

    img.find_root(imagedir)
    if img.type != pkgimage.IMG_USER:
        return
    img.load_config()

    img.load_catalogs(QuietProgressTracker())
    img.refresh_publishers(full_refresh=True)

    if check_type == "updates":
        component_list = get_list_of_updates(img, opname=opname)

        security_update_count = 0
        if security_attr and component_list:
            security_update_count = get_list_of_security_updates(img,
                                                              security_attr,
                                                              security_keywords)

        return component_list, security_update_count
    elif check_type == "installed":
        return get_list_of_installed(img), 0
    elif check_type == "uninstalled":
        return get_list_of_uninstalled(img), 0


def get_manifest(img, fmri, opname=None):
    """
    Returns a tuple containing (msft, None) or (None, exception).
    All (almost) errors are network errors or some sort
    """
    try:
        if opname:
            img.history.operation_name = opname
        return (img.get_manifest(fmri), None)
    except (TransportError, RetrievalError, CatalogRefreshException, RuntimeError), err:
        utils.logger.warning("Manifest retrieval error for %s" % fmri)
        utils.logger.warning(utils.format_trace())
        return (None, str(err))


def get_list_of_updates(img, opname=None):
    """
    Throws RuntimeError, httplib.HTTPException, PlanCreationException, InventoryException,
    RetrievalError, CatalogRefreshException on error
    """
    if opname:
        img.history.operation_name = opname
    pkg_list = [ ipkg.get_pkg_stem() for ipkg in img.gen_installed_pkgs() ]

    img.make_install_plan(pkg_list, QuietProgressTracker(), lambda: False, False,
                          verbose = False)

    # Don't include components which got pulled in due to
    # dependencies but aren't actually installed.
    return [pp for pp in img.imageplan.pkg_plans if pp.origin_fmri is not None]


def get_list_of_security_updates(img, security_attr=None, security_keywords=None, opname=None):
    """
    Determine if any of the updates between the current pkg version installed
    and the version targeted to be installed has one of the security keywords set
    in the pkg's meta-data.  This indicates that the update contains
    security changes.
    """
    if not security_attr or not security_keywords:
        return 0

    if security_keywords is None:
        security_keywords = []

    if opname:
        img.history.operation_name = opname

    count = 0

    inv_all = list(img.inventory(None, True))

    for installed, state in img.inventory(None, False):
        if not state['upgradable']:
            continue

        found_security_update = False

        for ipkg, state in inv_all:
            # We only need to find one security update per package update
            # group.
            if found_security_update:
                break
            if ipkg.is_same_pkg(installed) and \
                state['state'] == pkgimage.PKG_STATE_KNOWN and \
                                                 ipkg.is_successor(installed):
                (manifest, dummy_reason) = get_manifest(img, ipkg)
                if not manifest: # manifest could not be retrieved for some reason
                    continue
                value = manifest.get(security_attr, None)

                if value and value in security_keywords:
                    count += 1
                    found_security_update = True
                    break

                del value
                del manifest

    return count


def get_list_of_installed(img, opname=None):
    if opname:
        img.history.operation_name = opname
    else:
        img.history.operation_name = 'list'

    return [ipkg for ipkg, dummy_state in img.inventory(None, False)]


def get_list_of_uninstalled(img, opname=None):
    """Only the newest fmris of not installed packages are returned"""
    if opname:
        img.history.operation_name = opname
    else:
        img.history.operation_name = 'list'
    installed_fmris = get_list_of_installed(img, opname=opname)

    not_installed_fmris = []
    inventory = img.inventory(None, True)
    for ipkg, dummy_state in inventory:
        have = False
        for installed in installed_fmris:
            if ipkg.is_same_pkg(installed):
                have = True
                break

        if not have:
            not_installed_fmris.append(ipkg)

    keep_newest_fmris(not_installed_fmris)

    return not_installed_fmris


def get_license(image, act, fmri, opname=None):
    try:
        if opname:
            image.history.operation_name = opname
        # get license content
        lic_name = act.attrs["license"]
        sio = StringIO()
        pkgmisc.gunzip_from_stream(act.get_remote_opener(image, fmri)(), sio)
        lic_text = sio.getvalue()
        sio.close()
        return (lic_text, lic_name, None)
    except:
        val = sys.exc_info()[1]
        utils.logger.debug(utils.format_trace())
        return (None, None, val)


def fetch_licenses(image_plan, opname=None):
    """
    Get liceneses from the passed imageplan
    Returns ("", None) if no license were found
    Returns (licensetext, None) if license(s) exists and were not empty
    Returns (None, errmsg) if an error occured while fetching licenses

    Since many packages may share identical
    licenses we collapse the licenses based on the hash of the license
    file.
    """

    try:
        if opname:
            image_plan.image.history.operation_name = opname

        # license_dict is a dictionary of:
        # { lic_text : [ lic_name, [ pkgname1, pkgname2, ...] ] }
        # NOTE: for now, lic_name is hardcoded is 'unknown', and is not used
        # because the new pkg(5) API doesn't make the name available.  When the
        # name becomes available, it can be set and used.
        license_dict = { }
        licenses = ""
        lic_name = "Unknown"

        pkgs = [pp.destination_fmri for pp in image_plan.pkg_plans]

        api_inst = ImageInterface(image_plan.image.get_root(), CLIENT_API_VERSION,
            QuietProgressTracker(), None, INFO.CMD_NAME)
        ret = api_inst.info(pkgs, False, frozenset([PackageInfo.LICENSES]))
        plics = ret[ImageInterface.INFO_FOUND]
        for i, pi in enumerate(plics):
            pkgname = PkgFmri(pi.fmri).get_short_fmri()
            #utils.logger.debug("fetch_licenses: " + str(pkgname))
            for lic in pi.licenses:
                lic_text = str(lic)
                # If we've already seen this license, just add the pkgname
                # to the list of package names with this license
                if lic_text in license_dict:
                    if not pkgname in license_dict[lic_text][1]:
                        license_dict[lic_text][1].append(pkgname)
                    continue

                # We haven't seen this license before.
                # Create new entry
                license_dict[lic_text] = (lic_name, [pkgname])

                #import re
                #fname = str(lic_name) + str(pkgname)
                #pat = re.compile("[^a-z0-9_-]+")
                #fname = re.sub(pat, "_", fname)
                #f = open("/tmp/" + fname, "wb")
                #f.write(lic_text)
                #f.close()


        # We've finished traversing the package plan. Now loop through the
        # license dictionary and concatenate license data
        for lic_text in license_dict:
            lic_name, lic_pkg_names = license_dict[lic_text]

            # Write license name
            licenses = "".join([licenses, "==========\n", "\n".join(lic_pkg_names), "\n\n", lic_text, "\n\n"])
        return (licenses, None)
    except RetrievalError, e:
        return (None, str(e))
    except Exception, e:
        return (None, str(e))


def extract_catalog_retrieval_errors(failures):
    error_strs = []
    remote = []
    for pub, err in failures.args[0]:
        utils.logger.debug("Remote publisher network issue: %s" % pub)
        if isinstance(err, urllib2.HTTPError):
            error_strs.append("%s: %s - %s" % (utils.to_unicode(err.filename), utils.to_unicode(err.code), utils.to_unicode(err.msg)))
            remote.append(pub["prefix"])
        elif isinstance(err, urllib2.URLError):
            remote.append(pub["prefix"])
            if err.args[0][0] == 8:
                error_strs.append("%s: %s" % (utils.to_unicode(urlparse.urlsplit(pub["origin"])[1].split(":")[0]), utils.to_unicode(err.args[0][1])))
            else:
                if isinstance(err.args[0], socket.timeout):
                    error_strs.append("%s: %s" % (
                        utils.to_unicode(pub["origin"]), _("Timed out connecting to the publisher host")))
                else:
                    error_strs.append("%s: %s" % (utils.to_unicode(pub["origin"]), utils.to_unicode(str(err.args[0][1]))))
        elif isinstance(err, IOError):
            error_strs.append(utils.to_unicode(str(err)))
        elif isinstance(err, ValueError):
            error_strs.append(utils.to_unicode(str(err[0])))
    return (remote, error_strs)


def has_updates(imagedir, lazy=True, opname=None):
    """
    Returns false in case there are no updates or if there is any error
    """
    try:
        img = pkgimage.Image()
        img.history.client_name = INFO.CMD_NAME
        if opname:
            img.history.operation_name = opname
        img.find_root(imagedir)
        if img.type != pkgimage.IMG_USER:
            return False
        img.load_config()
        tracker = QuietProgressTracker()
        img.load_catalogs(tracker)
        img.refresh_publishers(full_refresh=not lazy)

        installed_fmris = []

        inventory = img.inventory(None, False)
        for ipkg, state in inventory:
            if state['state'] == pkgimage.PKG_STATE_INSTALLED and state['upgradable']:
                installed_fmris.append(ipkg)

        for installed in installed_fmris:
            for ipkg, state in img.inventory([], True):
                if state['state'] == pkgimage.PKG_STATE_KNOWN and not state['upgradable']:
                    manifest = get_manifest(img, ipkg, opname=opname)[0]
                    if not manifest:
                        continue
                    if manifest.fmri.is_successor(installed):
                        return True
    except ImageNotFoundException, err:
        utils.logger.warning("Updates check failed for %s", fsdec(imagedir))
        utils.logger.warning("ImageNotFoundException: %s" % repr(err))
    except RuntimeError, failures:
        error_strs = extract_catalog_retrieval_errors(failures)[1]
        utils.logger.warning("Updates check failed for %s", fsdec(imagedir))
        utils.logger.warning("\n".join(error_strs))
    except httplib.HTTPException, err:
        utils.logger.warning("Updates check failed for %s", fsdec(imagedir))
        utils.logger.warning("HTTPException: %s" % repr(err))
    except CatalogRefreshException, err:
        utils.logger.warning("Update check failed for %s", fsdec(imagedir))
        utils.logger.warning("CatalogRefreshException: %s" % repr(err))
    except:
        utils.logger.warning("Exception checking for image updates: %s", imagedir)
        utils.logger.warning(utils.format_trace())

    return False


def has_available(imagedir, lazy=True, opname=None):
    """
    Returns false in case there is nothing available to install or if there is any error
    """
    try:
        img = pkgimage.Image()
        img.history.client_name = INFO.CMD_NAME
        if opname:
            img.history.operation_name = opname
        img.find_root(imagedir)
        if img.type != pkgimage.IMG_USER:
            return False
        img.load_config()
        tracker = QuietProgressTracker()
        img.load_catalogs(tracker)
        img.refresh_publishers(full_refresh=not lazy)

        installed_fmris = [ipkg for ipkg, dummy_state in img.inventory(None, False)]

        not_installed_fmris = []
        inventory = img.inventory(None, True)
        for ipkg, state in inventory:

            have = False
            for installed in installed_fmris:
                if ipkg.is_same_pkg(installed):
                    have = True
                    break

            if not have:
                not_installed_fmris.append(ipkg)

        keep_newest_fmris(not_installed_fmris)

        return len(not_installed_fmris)
    except RuntimeError, failures:
        error_strs = extract_catalog_retrieval_errors(failures)[1]
        utils.logger.warning("\n".join(error_strs))
    except httplib.HTTPException, err:
        utils.logger.warning("Exception checking for available components: %s", fsdec(imagedir))
        utils.logger.warning("HTTPException: %s" % repr(err))
    except CatalogRefreshException, err:
        utils.logger.warning("Exception checking for available components: %s", fsdec(imagedir))
        utils.logger.warning("CatalogRefreshException: %s" % repr(err))
    except:
        utils.logger.warning("Exception checking for available components: %s", fsdec(imagedir))
        utils.logger.warning(utils.format_trace())

    return False


def has_installed(imagedir, opname=None):
    """
    Returns false in case there is nothing installed or if there is any error
    """

    try:
        all_known = True
        img = pkgimage.Image()
        img.history.client_name = INFO.CMD_NAME
        if opname:
            img.history.operation_name = opname
        img.find_root(imagedir)
        if img.type != pkgimage.IMG_USER:
            return False
        img.load_config()
        img.load_catalogs(QuietProgressTracker())

        for dummy_pkg, state in img.inventory(None, all_known):
            if state['state'] == pkgimage.PKG_STATE_INSTALLED:
                return True
    except RuntimeError, failures:
        error_strs = extract_catalog_retrieval_errors(failures)[1]
        utils.logger.warning("\n".join(error_strs))
    except httplib.HTTPException, err:
        utils.logger.warning("Exception checking for installed components: %s", fsdec(imagedir))
        utils.logger.warning("HTTPException: %s" % repr(err))
    except:
        utils.logger.warning("Exception checking for installed components: %s", fsdec(imagedir))
        utils.logger.warning(utils.format_trace())

    return False


def load_categories(img):
    """Loads mapping of packages to categories mappings from data files"""
    #
    # This code loads package to category mappings from zero or more
    # configuration files housed under <install location>/data/.
    #
    # The file names are based on the catalog names. Since each
    # catalog equates to an publisher, the names of the mapping
    # files are equal to the publisher names.
    #
    # This code handles multiple publishers and mapping files.
    #
    # Format of the file:
    #
    # dic = {"package_name":"comma,separated,categories"}
    #
    # where the package_name corresponds to the pkg.client.image.fmri.get_name()
    #
    # An example:
    #
    #   [updatetool]
    #   category = System Tools
    #
    #   [wxpython2.8-minimal]
    #   category = GUI Toolkits
    #
    #   [python2.4-minimal]
    #   category = Scripting
    #
    #   [pkg]
    #   category = System Tools
    #

    categories = {}
    for p in img.gen_publishers():
        catalog = p['prefix']
        category = {}
        categories_file = os.path.join(fsenc(img.get_root()), fsenc(u"updatetool"), fsenc(u"data"), fsenc(catalog))
        config_parsed = utils.get_config_parser(categories_file)
        if config_parsed:
            for section in config_parsed.sections():
                category[section] = config_parsed.get(section, "category")
            categories[catalog] = category

    return categories


def search(img, local=False, case_sensitive=False, criteria=None):
    """Search through the reverse index databases for the given token."""

    try:
        # return_action is set to True here so that we can search older repos
        # that don't support returning just packages.
        query = [Query(criteria, case_sensitive, return_actions=True)]
        searches = []
        err_msg = ""
        if local:
            searches.append(img.local_search(query))
        else:
            searches.append(img.remote_search(query))
        # By default assume we don't find anything.
        retcode = False

        msg = []
        for result in itertools.chain(*searches):
            msg.append(get_fmri_from_search_result(result))
            retcode = True

    except (IncorrectIndexFileHash, InconsistentIndexException):
        return (False, _("The search index appears corrupted.  Please "
                "rebuild the index with 'pkg rebuild-index'."), msg)
    except ProblematicSearchServers, e:
        return (False, str(e), msg)
    except SlowSearchUsed, e:
        pass # should there be an warning dialog here?
    except BooleanQueryException, e:
        return (False, str(e), msg)
    except RuntimeError, failed:
        retcode = False
        err_msg = _("Some servers failed to respond:\n")
        for pub, err in failed.args[0]:
            utils.logger.debug("11")
            if isinstance(err, urllib2.HTTPError):
                # XXX : Is concatenating unicode and str objects here ok?
                err_msg += utils.to_unicode("\n    %s: %s (%d)" % (pub["origin"], err.msg, err.code))
            elif isinstance(err, urllib2.URLError):
                if isinstance(err.args[0], socket.timeout):
                    err_msg += utils.to_unicode("\n    %s: %s" % (pub["origin"], "timeout"))
                else:
                    err_msg += utils.to_unicode("\n    %s: %s" %  (pub["origin"], err.args[0][1]))
            else:
                utils.logger.debug("Could note extract error message from search")

    return (retcode, err_msg, msg)


def get_fmri_from_search_result(result):
    dummy_query_num, dummy_pub, (v, return_type, tmp) = result
    if v == 0:
        dummy_index, mfmri, action, value = tmp
        if action and value:
            return str(pkg.fmri.PkgFmri(str(mfmri)))
        else:
            return str(mfmri)
    else:
        if return_type == Query.RETURN_ACTIONS:
            mfmri, dummy_match, action = tmp
        else:
            mfmri = tmp
        return str(pkg.fmri.PkgFmri(str(mfmri)))


def check_if_safe(affected_image_root=None, affected_pkg_fmris=None, opname=None, yield_func=None):
    """
    Check if operations on an image on certain pkgs are safe wrt the current execution environment.

    This checks that affected_pkg_fmris in affected_image_root do not contain

        1. the python the caller is executing with
        2. the wxPython packages the caller is executing with
        3. the pkg(5) API implementation the caller is using
        4. this current source file

    @keyword affected_image_root: the image root directory to check for safety
    @type affected_image_root: C{string} (C{img.getroot})

    @keyword affected_pkg_fmris: list of pkg(5) fmris to check for safety
    @type affected_pkg_fmris: C{list}

    @keyword opname: pkg(5) operation name for image operation log
    @type opname: C{string} (C{install}, C{uninstall} etc.)

    @keyword yield_func: Optional yield function to call during search to keep the caller responsive
    @type yield_func: C{function}

    @return: Whether the image is safe or not
    @rtype: boolean
    """
    assert affected_image_root is not None
    assert affected_pkg_fmris is not None

    import wx                   # DO NOT REMOVE
    import pkg.client.image     # DO NOT REMOVE

    affected_image_root = canonical_path(affected_image_root)

    unsafe = []

    files_to_check = [
        sys.executable,                            # python we are running under
        sys.modules['wx'].__file__,                # wxPython
        sys.modules['pkg.client.image'].__file__,  # IPS
        __file__,                                  # updatetool
    ]
    p_imgs = {}
    # Create a dict p_imgs = {image1 : [path1, path2., ...], image2 : [path1, ...]}
    for f in files_to_check:
        if yield_func is not None:
            yield_func()
        try:
            img = pkgimage.Image()
            img.history.client_name = INFO.CMD_NAME
            if opname:
                img.history.operation_name = opname
            img.find_root(f)
            if img.type != pkgimage.IMG_USER:
                utils.logger.debug("No user image for [" + f + "]. Skipping check.")
                continue
            affected_file_root = canonical_path(img.get_root())
            if affected_file_root == affected_image_root:
                utils.logger.debug("affected_file_root [" + affected_file_root + "]")
                utils.logger.debug("affected_image_root [" + affected_image_root + "]")
                p_imgs.setdefault(affected_file_root, []).append(os.path.realpath(f))
                if f.endswith('pyc') or f.endswith('pyo'): # seach for .py also
                    p_imgs[affected_file_root].append(os.path.realpath(f[:-1]))
                    utils.logger.debug("Check range now " + repr(p_imgs))
        except:
            continue

    searches = []
    found_fmris = []
    retries = 0
    done = False
    while retries <= 1 and not done:
        searches = []
        found_fmris = []
        try:
            for imgdir in p_imgs:
                if yield_func is not None:
                    yield_func()
                pths = p_imgs[imgdir]
                # NOTE: No error checking here. We need it to crash and burn (FOR NOW)
                ximg = load_image_interface(imgdir)[0]
                utils.logger.debug(repr(ximg))
                if yield_func is not None:
                    yield_func()
                for p in pths:
                    utils.logger.debug("Will try to process [" + p + "]")
                    pat = p[len(imgdir):]
                    utils.logger.debug("Variation [" + pat + "]")
                    searches.append(ximg.local_search([Query(pat, True, return_actions=True)]))

                    # XXX: Hackey searches to avoid http://defect.opensolaris.org/bz/show_bug.cgi?id=1059
                    pat = pat.replace('\\', '/')
                    utils.logger.debug("Variation [" + pat + "]")
                    searches.append(ximg.local_search([Query(pat, True, return_actions=True)]))

                    # XXX : The following is the one that really works for now
                    pat = pat.replace('/', '\\', 1)
                    utils.logger.debug("Variation [" + pat + "]")
                    searches.append(ximg.local_search([Query(pat, True, return_actions=True)]))

            # Uncomment to fake the results
            # for x in affected_pkg_fmris:
            #    unsafe.append(x)

            if not searches:
                utils.logger.debug("Returning because of nothing to search")
                return unsafe

            utils.logger.debug("Will execute searches now")

            # XXX : This is heavyweight but we can't really yield too often here due
            # to lack of control
            for result in itertools.chain(*searches):
                utils.logger.debug("Result [" + repr(result) + "]")
                if yield_func is not None:
                    yield_func()
                ff = get_fmri_from_search_result(result)
                utils.logger.debug("FMRI [" + repr(ff) + "]")
                found_fmris.append(ff)
            done = True
        except (IncorrectIndexFileHash, InconsistentIndexException, ProblematicSearchServers, SlowSearchUsed, BooleanQueryException), dummy:
            retries += 1
            if retries <= 1:
                rebuild_search_index(affected_image_root, pkg_client_name=INFO.CMD_NAME)
            else:
                raise
        except:
            raise

    found_fmris = set(found_fmris)
    for ffmri in found_fmris:
        utils.logger.debug("Found fmri " + repr(ffmri))
        if isinstance(ffmri, str):
            ffmri = pkg.fmri.PkgFmri(ffmri)
        for afmri in affected_pkg_fmris:
            assert isinstance(afmri, PkgFmri)
            # XXX : Awaiting IPS bug 1059 fix if afmri.is_same_pkg(ffmri):
            name1 = afmri.get_name()
            name2 = ffmri.get_name()
            idx = name2.find('\\')
            if idx != -1:
                name2 = name2[:idx]
            if name1 == name2:
                unsafe.append(afmri)

    return unsafe


def get_download_size_delta(old_manifest, new_manifest):
    """
    Get an uncompressed estimate of the download that will happen when an update
    from old_manifest to new_manifet is downloaded. The cache is ignored. Compression
    is ignored.

    The difference is calculated as

    d =  size of all actions in new manifest not in old manifest
         + size of all the changed actions
    """
    change = 0
    added, changed, dummy_removed = new_manifest.difference(old_manifest)

    for oldact, newact in added:
        change += pkg.misc.get_pkg_otw_size(newact)
    for oldact, newact in changed:
        # Check if the change is due to content change and not just an attribute or some other change
        try:
            if oldact.hash == newact.hash:
                continue
        except: # the actions may not have a hash attribute
            pass
        change += pkg.misc.get_pkg_otw_size(newact)
    return change


def get_installed_size_delta(old_manifest, new_manifest):
    """
    Get a somewhat usable 'installed' size change indicator between
    two versions of a package.

    The difference is calculated as

    d =  size of all actions in new manifest not in old manifest
         + size difference of all actions in new manifest that are in old manifest but different
         - size of all actions in old manifest which are not in new manifest
    """
    change = 0
    added, changed, removed = new_manifest.difference(old_manifest)

    for oldact, newact in added:
        change += int(newact.attrs.get('pkg.size', 0))
    for oldact, newact in changed:
        change -= int(oldact.attrs.get('pkg.size', 0))
        change += int(newact.attrs.get('pkg.size', 0))
    for oldact, newact in removed:
        change -= int(oldact.attrs.get('pkg.size', 0))
    return change


def get_fmri_info(fmri):
    pub, name, ver = fmri.tuple()
    pub = fmri.get_publisher()
    return (pub, name, ver)


def validate_publisher(pub_url, ssl_key=None, ssl_cert=None):
    """Test that the publisher url supplied actually points to a valid
    packaging server."""

    if ssl_key == "":
        ssl_key = None
    if ssl_cert == "":
        ssl_cert = None

    pkg.misc.versioned_urlopen(pub_url, "catalog", [0], ssl_creds=(ssl_key, ssl_cert))

    return True


def catalog_refresh(img, remote=True, lazy=True):
    """
    Loads and refreshes the image catalog in the passed C{img} instance. Returns information on success or failure.

    @param img: the image instance to refresh
    @type img: C{pkg.client.image.Image}

    @keyword remote: Whether catalog should be remote repositories
    @type remote: C{boolean}

    @keyword lazy: Whether the remote fetch should be a lazy (only incremental updates) or a full refresh
    @type lazy: C{boolean}


    @return: a tuple with (bool success, bool error_is_remote, [pub prefix, pub prefix, ... ], [error string, error string ...])
    @rtype: C{tuple}
    """

    tracker = QuietProgressTracker()

    try:
        img.load_catalogs(tracker)
    except RuntimeError, msg:
        if msg == 'empty ImageConfig':
            return (False, False, [], [_("The image configuration is empty")])
        elif msg == 'no defined publishers':
            return (False, False, [], [_("No publishers have been defined for the image yet")])
        else:
            return (False, False, [], [utils.to_unicode(str(msg))])
    except:
        msg = sys.exc_info()[1]
        return (False, False, [], [utils.to_unicode(str(msg))])

    if not remote:
        return (True, False, [], [])

    try:
        img.refresh_publishers(full_refresh=not lazy)
    except UpdateLogException, err:
        utils.logger.debug(utils.format_trace())
        return (False, True, [], [str(err)])

    except (RuntimeError, ValueError), failures:
        utils.logger.debug(utils.format_trace())
        (remote, error_strs) = extract_catalog_retrieval_errors(failures)
        if error_strs:
            return (False, remote, remote, error_strs)
        else:
            return (False, remote, remote, [utils.to_unicode(str(failures))])
    except httplib.HTTPException, err:
        utils.logger.debug(utils.format_trace())
        return (False, True, [], ["Remote server issues: %s" % str(err)])
    except CatalogRefreshException, err:
        utils.logger.debug(utils.format_trace())
        remote = [x[0]['prefix'] for x in err.failed \
                if isinstance(x[1], RetrievalError) or isinstance(x[1], TransportError)]
        messages = []
        for x in err.failed:
            if isinstance(x[1], RetrievalError):
                utils.logger.debug(str(x[1].data))
                messages.append(str(x[1].data))
            if isinstance(x[1], TransportError):
                utils.logger.debug(str(x[1]))
                messages.append(str(x[1]))
        if err and err != "":
            utils.logger.debug(str(err))
            messages.append(str(err))
        if not messages:
            messages.append("Unknown remote server issues while trying to download component catalog")
        return (False, remote, remote, messages)

    try:
        # Must reload due to IPS issue 2937
        img.load_catalogs(tracker)
        return (True, True, [], [])
    except RuntimeError, msg:
        if msg == 'empty ImageConfig':
            return (False, False, [], [_("The image configuration is empty")])
        elif msg == 'no defined publishers':
            return (False, False, [], [_("No publishers have been defined for the image yet")])
        else:
            return (False, False, [], [utils.to_unicode(str(msg))])
    except httplib.HTTPException, err:
        return (False, True, [], [_("Remote server issues: %s") % utils.to_unicode(str(err))])


def load_image(u_imagedir, opname=None):
    """
    Attempt to load an image object for further operations and trap any
    errors that might happen while doing so

    @param u_imagedir: image directory path (as known by us via C{add_image} previously)
    @type u_imagedir: unicode string literal
    @param opname: optional opname for image history
    @type opname: string
    @return: a two element tuple containing C{pkg.client.image} object and C{None} in case of success
        or c{None} and error reason string on failure
    @rtype: C{tuple}
    """
    img = pkgimage.Image()
    img.history.client_name = 'updatetool'
    if opname:
        img.history.operation_name = opname
    try:
        img.find_root(fsenc(u_imagedir))
        if img.type != pkgimage.IMG_USER:
            raise AssertionError("Not a user image")
    except (AssertionError, ImageNotFoundException):
        if utils.is_v1_image(fsenc(u_imagedir)):
            return (None, messages.NEW_IMAGE_MSG % {'path':u_imagedir})
        elif not os.path.exists(fsenc(u_imagedir)):
            return (None, messages.INACCESSIBLE_IMAGE_REMOVE_MSG % {'path':u_imagedir})
        else:
            return (None, messages.UNRECOGNIZED_IMAGE_VERIFY_MSG % {'path':u_imagedir})

    try:
        img.load_config()
    except (RuntimeError, httplib.HTTPException):
        return (None, _("Image configuration could not be loaded."))

    return (img, None)


def load_image_interface(imagedir):
    """
    Attempt to create an ImageInterface object for further operations and trap any
    errors that might happen while doing so

    @param imagedir: image directory path (as known by us via C{add_image} previously)
    @type imagedir: unicode string literal
    @param opname: optional opname for image history
    @type opname: string
    @return: a two element tuple containing C{pkg.client.api.ImageInterface} object and C{None} in case of success
        or c{None} and error reason string on failure
    @rtype: C{tuple}
    """
    try:
        img = ImageInterface(imagedir, CLIENT_API_VERSION,
                    QuietProgressTracker(), None, INFO.CMD_NAME)
    except ImageNotFoundException, e:
        return (None, _("'%s' is not an install image") % e.user_dir)
    except (RuntimeError, httplib.HTTPException):
        return (None, _("Image configuration could not be loaded."))

    # NOTE: this uses a private field (img).  The ImageInterface class doesn't
    # provide a way to get the type of the image.
    if img.img.type != pkgimage.IMG_USER:
        return (None, _("'%s' is not a supported install image") % imagedir)

    return (img, None)


def filter_addon_entries(u_image_list, feed_entries):
    '''
    Process the addon feed entries and keep only feed entries for that
    are applicable to one or more install images. For an addon entry to be
    applicable to an install image the image:
    1) Must be configured with the repo URLs specified in the addon feed
    2) Must not already have the add-on packages installed
    3) XXX Must have the add-on landmark packages installed (to be implemented)
    '''
    filtered_entries = [ ]
    for e in feed_entries:
        origins = [ ]
        for p in e[BF.PUBLISHERS]:
            origins.append(p[BF.ORIGIN])
        # Get all images configured with the specified repo origins
        u_images = get_images_by_origin(u_image_list, origins)
        if len(u_images) > 0:
            entry_kept = False
            for img in u_images:
                # If the image doesn't already have the addon packages installed
                # then the add-on is applicable to that image
                if not has_installed_pkgs(fsenc(img), e[BF.PACKAGES]):
                    entry_kept = True
                    filtered_entries.append(e)
                    utils.logger.debug( "Featured Software: keeping add-on %s: image found with repos %s and pkgs %s" %
                                      (e[BF.TITLE], origins, e[BF.PACKAGES]))
                    break
            if not entry_kept:
                utils.logger.debug(
                "Featured Software: trimming add-on %s: all images with repos %s already have pkgs %s" %
                (e[BF.TITLE], origins, e[BF.PACKAGES]))
        else:
            utils.logger.debug(
            "Featured Software: trimming add-on %s: no image found with repos %s" %
            (e[BF.TITLE], origins))
    return filtered_entries


def filter_application_entries(u_images, feed_entries):
    '''
    Remove any application that is already installed. We do this via
    landmark packages. If all landmark packages are already installed
    in a user image then assume the application is already installed
    and don't include that application in the list.
    '''
    filtered_entries = [ ]
    for e in feed_entries:
        landmark_pkgs = e[BF.PACKAGES_LANDMARK]
        # If no images have the software installed then we want to show it
        if len(get_images_by_pkgs(u_images, landmark_pkgs)) == 0:
            utils.logger.debug(
            "Featured Software: keeping app %s: no image found with pkgs %s" %
            (e[BF.TITLE], landmark_pkgs))
            filtered_entries.append(e)
        else:
            utils.logger.debug(
            "Featured Software: trimming app %s: image found with pkgs %s" %                (e[BF.TITLE], landmark_pkgs))
    return filtered_entries


def get_images_by_origin(u_images, origin_urls):
    """
    Return a list of images that are configured with repository origins
    that match all passed urls.   'images' is a list of image directories.
    """
    return [img_dir for img_dir in u_images if has_origins(fsenc(img_dir),
                                                            origin_urls)]


def get_images_by_pkgs(u_images, landmark_pkgs):
    """
    Return a list of images that have the landmark_pkgs installed
    'images' is a list of image directories.
    'landmark_pkgs' is a list of packages
    """
    image_list = [ ]
    for img_dir in u_images:
        try:
            if has_installed_pkgs(fsenc(img_dir), landmark_pkgs):
                image_list.append(img_dir)
        except (AssertionError, ImageNotFoundException):
            # If the image is not valid then skip it
            pass

    return image_list


def rebuild_search_index(imgroot, pkg_client_name=INFO.CMD_NAME):
    try:
        api_inst = ImageInterface(imgroot,
                CLIENT_API_VERSION,
                QuietProgressTracker(),  # Progress Tracker
                cancel_state_callable=None,
                pkg_client_name=pkg_client_name)
        api_inst.rebuild_search_index()
    except:
        utils.logger.debug(utils.format_trace())
