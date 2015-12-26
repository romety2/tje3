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

#import sys

from common.boot import safe_decode
import os
import wx

from pkg.client.progress import QuietProgressTracker
from pkg.client.constraint import ConstraintException
from pkg.client.api_errors import PlanCreationException, InventoryException
import httplib

#from common import task
import common.info as INFO
import common.utils as utils
import common.basicfeed as BF
from common import ips
from common.fsutils import fsenc
import swupdate.consts as CONST
import swupdate.utils as swutils

APP_CLIENT_NAME = INFO.UPDATE_CLIENT_NAME

NO_LIC_TXT = _("No license agreement available.")
NO_LIC_ERROR_TXT = _("Error encountered while retrieving license agreement.")

OPNAME = 'license'


class LicenseDialog(wx.Dialog):

    def __init__(self, *args, **kwds):
        self.lic_list = kwds['lic_list']
        del kwds['lic_list']

        wx.Dialog.__init__(self, *args, **kwds)

        self.lic_accepted = False

        p = wx.Panel(self)
        self.notebook = wx.Notebook(p, -1, style=wx.TAB_TRAVERSAL)

        for title, lic in self.lic_list:
            self.notebook.AddPage(self.make_page(lic), title)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.close_button = wx.Button(p, wx.ID_CANCEL, _("&Close"))
        self.Bind(wx.EVT_BUTTON, self.onClose, self.close_button)
        self.close_button.SetToolTipString(_("Close the dialog"))

        self.accept_button = wx.Button(p, -1, _("&Accept"))
        self.Bind(wx.EVT_BUTTON, self.onAccept, self.accept_button)
        self.accept_button.SetToolTipString("Accept the license agreement(s)")

        hsizer.Add(self.close_button, 0, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND, 4)
        hsizer.Add(self.accept_button, 0, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND, 4)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self.notebook, 1, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND, 8)
        vsizer.Add(hsizer, 0, wx.RIGHT | wx.LEFT | wx.BOTTOM| wx.ALIGN_RIGHT, 8)

        p.SetSizer(vsizer)
        self.SetSize(wx.DLG_SZE(self, (400, 248)))

        # Center the dialog over the frame.
        self.Centre()

        # Set the focus to the accept button to enable proper tab nav.
        self.accept_button.SetFocus()


    def onClose(self, event):
        event.Skip()


    def onAccept(self, event):
        self.lic_accepted = True
        self.Close(True)
        event.Skip()


    def make_page(self, license):

        panel = wx.Panel(self.notebook, -1)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        text_ctrl = wx.TextCtrl(panel, -1, license,
                                style = wx.TE_MULTILINE
                                      | wx.TE_READONLY
                                      | wx.TAB_TRAVERSAL)
        text_ctrl.SetMinSize((500, 400))
        hsizer.Add(text_ctrl, 1, wx.EXPAND, 0)
        panel.SetSizer(hsizer)
        panel.Layout()

        return panel

def _gen_lic_text(imageplan, title, opname=OPNAME):

    # Returns tuple (License Text, None) on success or (None, Reason) on
    # failure.

    try:
        lic, status = ips.fetch_licenses(imageplan, opname)
        if lic and lic != "":
            lic_text = utils.to_unicode(lic, encoding='latin-1')
            return (lic_text, None)
        elif lic == "":
            return (NO_LIC_TXT, None)
        else:
            utils.logger.error("Error retrieving license for :" + title)
            utils.logger.error("Error Exception:" + status)
            utils.logger.error(utils.format_trace())
            return (None, status)
    except Exception, e:
        utils.logger.error("Error retrieving license for :" + title)
        utils.logger.error("Error Exception:" + str(e))
        utils.logger.error(utils.format_trace())
        return (None, str(e))

def generate_license_list(image_list):

    # Returns tuple (License tuple list, None, None) on success or
    # (None, img_details, Reason) on failure

    # License tuple list (title, lic_text)
    lic_list = []

    #XXX: This needs to be optimized.  Only load the licenses when the
    #     tab is selected.
    for image_details in image_list.itervalues():
        if not image_details['checked']:
            continue

        if image_details['type'] == CONST.T_NORMAL:
            title = ips.get_image_title(fsenc(image_details['imgroot']),
                                                        opname=OPNAME)
            lic_text, reason = _gen_lic_text(image_details['imageplan'], title)

            if reason is not None:
                return (None, image_details, reason)
            lic_list.append((title, lic_text))
        elif image_details['type'] == CONST.T_ADD_ON and \
             image_details['id'] != -1:
            id = -1

            for add_on_data in image_details['add_on_image_list']:
                if add_on_data['selected']:
                    id = add_on_data['id']
                    break

            assert id != -1, \
                      "LicenseDialog: item checked state out of sync " + \
                      "with add_on_image_list selected state."

            if image_details['feed_entry'].has_key(BF.TITLE):
                title = image_details['feed_entry'][BF.TITLE]
            else:
                title = _("Untitled Add-On")

            imgroot = image_list[id]['imgroot']
            (img, reason) = ips.load_image(imgroot, opname=OPNAME)

            if img is None:
                return (None, image_details, reason)

            img.history.client_name = APP_CLIENT_NAME
            img.history.operation_name = OPNAME

            success, error_is_remote, remote, errors = \
                                        ips.catalog_refresh(img, remote=True)
            if not success:
                return (None, image_details,
                              _handle_catalog_refresh_error(error_is_remote,
                                                            remote,
                                                            errors))

            status = _make_install_plan(img, image_details['feed_entry'][BF.PACKAGES])
            if status:
                return (None, image_details, status)

            lic_text, reason = _gen_lic_text(img.imageplan, title)

            if reason is not None:
                return (None, image_details, reason)
            lic_list.append((title, lic_text))
        elif image_details['type'] == CONST.T_NEW_IMAGE and \
             image_details['id'] != -1:

            path = os.path.expanduser(image_details['imgroot'])
            title = image_details['title']

            status = swutils.create_image(fsenc(path), title,
                                  image_details['description'],
                                  image_details['publishers'])

            if status:
                return (None, image_details, status)

            (img, reason) = ips.load_image(path, opname=OPNAME)

            if img is None:
                return (None, image_details, reason)

            status = _make_install_plan(img, image_details['feed_entry'][BF.PACKAGES])
            if status:
                return (None, image_details, status)

            lic_text, reason = _gen_lic_text(img.imageplan, title)

            if reason is not None:
                return (None, image_details, reason)
            lic_list.append((title, lic_text))


    return (lic_list, None, None)


def _make_install_plan(img, pkgs):

    try:
        img.make_install_plan(pkgs, QuietProgressTracker(),
                              lambda: False, False)
    except (ConstraintException, PlanCreationException), ce:
        img.cleanup_downloads()
        return str(ce)
    except InventoryException, ie:
        img.cleanup_downloads()
        return str(ie)
    except (RuntimeError, httplib.HTTPException), msg:
        img.cleanup_downloads()
        return str(msg)
    except KeyError, msg:
        img.cleanup_downloads()
        return str(msg)
    except Exception, e:
        img.cleanup_downloads()
        return str(e)

    return None

def _handle_catalog_refresh_error(error_is_remote, remote, errors):
    emsg = u"\n".join(safe_decode(x) for x in errors)
    if emsg is None:
        emsg = u""
    if error_is_remote:
        if remote:
            msg = _("Components list could not be refreshed successfully due to a network issue" \
                    " with the following remote repositories:\n\n%(repos)s\n\nThe error was:" \
                    "\n\n%(errors)s\n\nThe available components list may not be accurate or complete.") % {
                            'repos':"\n".join(remote), 'errors':emsg}
        else:
            msg = _("Components list could not be refreshed successfully due to a network issue." \
                    "\n\n%s\n\nThe available components list may not be accurate or complete.") \
                    % emsg
    else:
        msg = _("Components list could not be refreshed successfully." \
                "\n\n%s\n\nThe available components list may not be accurate or complete.") \
                % emsg

    return msg
