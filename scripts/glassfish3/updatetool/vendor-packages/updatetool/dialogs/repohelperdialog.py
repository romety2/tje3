# -*- coding: utf-8 -*-
#
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS HEADER.
#
# Copyright (c) 2009-2011 Oracle and/or its affiliates. All rights reserved.
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

from common.fsutils import fsenc, FSENC
from urlparse import urlparse
import wx
import os.path
import sys
import pkg.misc as pkgmisc
import dialogs
import common.utils as utils
import common.ips as ips

class RepoHelperDialog(wx.Dialog):

    _ = wx.GetTranslation

    def __init__(self, *args, **kwds):
        self.i_name = kwds['name']
        self.i_url = kwds['url']
        self.i_ssl_key = kwds['ssl_key']
        self.i_ssl_cert = kwds['ssl_cert']
        self.i_edit = kwds['edit']
        self.disabled = kwds['disabled'] # XXX : Does not do anything yet
        del kwds['name']
        del kwds['url']
        del kwds['ssl_key']
        del kwds['ssl_cert']
        del kwds['edit']
        del kwds['disabled']
        # begin wxGlade: RepoHelperDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.THICK_FRAME
        wx.Dialog.__init__(self, *args, **kwds)
        self.panel_foo = wx.Panel(self, -1)
        self.repo_name_label = wx.StaticText(self.panel_foo, -1, _("Publisher Name:"))
        self.repo_name_text_ctrl = wx.TextCtrl(self.panel_foo, -1, "")
        self.repo_url_label = wx.StaticText(self.panel_foo, -1, _("Repository URL:"))
        self.repo_url_text_ctrl = wx.TextCtrl(self.panel_foo, -1, "")
        self.repo_ssl_cert_label = wx.StaticText(self.panel_foo, -1, _("Client Certificate:"))
        self.repo_ssl_cert_ctrl = wx.FilePickerCtrl(self.panel_foo, style=wx.FLP_USE_TEXTCTRL)
        self.repo_ssl_key_label = wx.StaticText(self.panel_foo, -1, _("Client Key:"))
        self.repo_ssl_key_ctrl = wx.FilePickerCtrl(self.panel_foo, style=wx.FLP_USE_TEXTCTRL)

        if self.i_url.startswith("http:"):
            self.repo_ssl_key_label.Enable(False)
            self.repo_ssl_key_ctrl.Enable(False)
            self.repo_ssl_cert_label.Enable(False)
            self.repo_ssl_cert_ctrl.Enable(False)

        #This part of code is added to support the already existing publisher which
        #has the ssl_key and ssl_cert = None
        if not self.i_ssl_key:
            self.i_ssl_key = u""
        if not self.i_ssl_cert:
            self.i_ssl_cert = u""

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

        self.Bind(wx.EVT_TEXT, self.OnChar, self.repo_url_text_ctrl)
        self.Bind(wx.EVT_FILEPICKER_CHANGED,
                  self.OnCertChar, self.repo_ssl_cert_ctrl)
        self.Bind(wx.EVT_FILEPICKER_CHANGED,
                  self.OnKeyChar, self.repo_ssl_key_ctrl)
        self.repo_name_text_ctrl.SetFocus()
        self.Centre()


    def OnChar(self, event):
        if self.repo_url_text_ctrl.GetValue().startswith("http:"):
            self.repo_ssl_key_ctrl.SetPath(u"")
            self.repo_ssl_cert_ctrl.SetPath(u"")
            self.repo_ssl_key_label.Enable(False)
            self.repo_ssl_key_ctrl.Enable(False)
            self.repo_ssl_cert_label.Enable(False)
            self.repo_ssl_cert_ctrl.Enable(False)
        else:
            self.repo_ssl_key_label.Enable(True)
            self.repo_ssl_key_ctrl.Enable(True)
            self.repo_ssl_key_ctrl.Refresh()
            self.repo_ssl_cert_label.Enable(True)
            self.repo_ssl_cert_ctrl.Enable(True)
            self.repo_ssl_cert_ctrl.Refresh()
        event.Skip()


    def OnCertChar(self, event):
        cert_path = self.repo_ssl_cert_ctrl.GetPath()
        key_path = self.repo_ssl_key_ctrl.GetPath()
        # If the key field is empty, try to populate it with a valid path
        if key_path is None or key_path.strip() == "":
            # We populate both fields in case the user entered a key path
            # into the cert field or visa versa
            (cert_path, key_path) = self._find_matching_pair(cert_path)
            if cert_path and key_path:
                self.repo_ssl_cert_ctrl.SetPath(cert_path)
                self.repo_ssl_key_ctrl.SetPath(key_path)
        event.Skip()


    def OnKeyChar(self, event):
        cert_path = self.repo_ssl_cert_ctrl.GetPath()
        key_path = self.repo_ssl_key_ctrl.GetPath()
        # If the cert field is empty, try to populate it with a valid path
        if cert_path is None or cert_path.strip() == "":
            # We populate both fields in case the user entered a key path
            # into the cert field or visa versa
            (cert_path, key_path) = self._find_matching_pair(key_path)
            if cert_path and key_path:
                self.repo_ssl_cert_ctrl.SetPath(cert_path)
                self.repo_ssl_key_ctrl.SetPath(key_path)
        event.Skip()


    def __set_properties(self):
        # begin wxGlade: RepoHelperDialog.__set_properties
        self.SetTitle(_("Publisher Properties"))
        self.repo_name_text_ctrl.SetToolTipString(_("For example - sun.com"))
        self.repo_url_text_ctrl.SetToolTipString(_("For example - http://pkg.sun.com/layered/collection/dev/"))
        self.repo_ssl_key_ctrl.SetToolTipString(_("The SSL Client key for this publisher"))
        self.repo_ssl_cert_ctrl.SetToolTipString(_("The SSL Client certificate for this publisher"))
        self.SetMinSize((650, -1))
        # end wxGlade
        self.repo_name_text_ctrl.SetValue(self.i_name)
        self.repo_url_text_ctrl.SetValue(self.i_url)
        self.repo_ssl_key_ctrl.SetPath(self.i_ssl_key)
        self.repo_ssl_cert_ctrl.SetPath(self.i_ssl_cert)


    def __do_layout(self):
        # begin wxGlade: RepoHelperDialog.__do_layout
        main_sizer = wx.FlexGridSizer(3, 1, 0, 0)
        grid_sizer_1 = wx.FlexGridSizer(4, 2, 0, 2)
        grid_sizer_1.Add(self.repo_name_label, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_1.Add(self.repo_name_text_ctrl, 0, wx.ALL|wx.EXPAND, 5)
        grid_sizer_1.Add(self.repo_url_label, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_1.Add(self.repo_url_text_ctrl, 0, wx.ALL|wx.EXPAND, 5)
        grid_sizer_1.Add(self.repo_ssl_cert_label, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_1.Add(self.repo_ssl_cert_ctrl, 0, wx.ALL|wx.EXPAND, 5)
        grid_sizer_1.Add(self.repo_ssl_key_label, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_1.Add(self.repo_ssl_key_ctrl, 0, wx.ALL|wx.EXPAND, 5)
        self.panel_foo.SetSizer(grid_sizer_1)
        grid_sizer_1.AddGrowableCol(1)
        main_sizer.Add(self.panel_foo, 0, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(main_sizer)
        main_sizer.AddGrowableRow(0)
        main_sizer.AddGrowableCol(0)
        self.Layout()
        # end wxGlade
        bpanel, dummy1, btn_ok = dialogs.make_std_dlg_btn_szr_panel(self, (
                (wx.ID_CANCEL, _("&Cancel"), _("Cancel the edit")),
                (wx.ID_OK, _("&OK"), _("Accept the edit")),
                ))
        main_sizer.Add(bpanel, 0, wx.ALL|wx.EXPAND, 10)
        main_sizer.Fit(self)
        self.Layout()
        self.SetMinSize(self.GetSize())
        self.Bind(wx.EVT_BUTTON, self.OnValidate, btn_ok)


    def OnValidate(self, event):
        assert event.GetId() == wx.ID_OK
        wx.BeginBusyCursor()
        _url = str(self.get_repo_url().strip())
        _pub = fsenc(self.get_repo_name().strip())
        _ssl_key = fsenc(self.get_ssl_key().strip())
        _ssl_cert = fsenc(self.get_ssl_cert().strip())

        _msg = None
        if _pub == "":
            _msg = _("The publisher name can not be blank.")
        elif not pkgmisc.valid_pub_prefix(_pub):
            _msg = _("The publisher name contains invalid characters.")
        elif not self.i_edit and _pub in (a[0] for a in self.GetParent().get_pubs()): # better/simpler overall to do it in edit than here
            _msg = _("The publisher name '%s' already exists.") % _pub
        elif _url == "":
            _msg = _("Publisher URL can not be blank.")
        elif not pkgmisc.valid_pub_url(_url):
            _msg = _("The publisher URL is invalid.")
        elif len(_ssl_key) > 0 and (not os.path.exists(os.path.abspath(_ssl_key))):
            _msg = _("The SSL key file does not exist")
        elif len(_ssl_cert) > 0 and (not os.path.exists(os.path.abspath(_ssl_cert))):
            _msg = _("The SSL certificate file does not exist")
        elif ((len(_ssl_cert) > 0 and len(_ssl_key) == 0) or (len(_ssl_cert) == 0 and len(_ssl_key) > 0)):
            _msg = _("Both the certificate and key are required for an https URL.")
        else:
            # So far so good. Now make sure we can ping the URL
            try:
                ips.validate_publisher(_url, ssl_key=_ssl_key,
                                             ssl_cert=_ssl_cert)
            except:
                utils.logger.debug(utils.format_trace())
                ( _host, _credentials_provided, _info_url ) = \
                    self._check_if_entitled_support_repo(_url,
                                        ssl_key=_ssl_key, ssl_cert=_ssl_cert)
                if _host is not None and not _credentials_provided:
                    # Looks like a support publisher which they did not
                    # specify credentials for
                    _msg = _("Could not connect to the publisher\n\n%s\n\nThis "\
                            "publisher appears to require credentials to access. For more information "\
                            "go to\n\n%s\n\nClick %s to return and correct the publisher "\
                            "information.\nClick %s to use the information as you "\
                            "specified.") % (_url, _info_url, _("Cancel"), _("OK"))
                elif _url.startswith("https:"):
                    _msg = _("Could not connect to publisher\n\n%s\n\n\nYou may need " \
                            "a valid key and certificate to connect to the\npublisher or the " \
                            "publisher URL you entered may not be valid.\n\nClick %s to return " \
                            "and correct the publisher information.\nClick %s to use the information "\
                            "as you specified.") % (_url, _("Cancel"), _("OK"))
                else:
                    # Could not ping the URL. Inform the user
                    _msg = _("Could not connect to publisher\n\n%s\n\nThe "\
                            "publisher information you entered may not be valid.\nClick " \
                            "%s to return and correct the publisher information.\nClick " \
                            "%s to use the information as you specified.") % (_url, _("Cancel"), _("OK"))
                utils.logger.error(("Could not connect to publisher: %s") % (_url))
                utils.logger.error(sys.exc_info()[1])
                wx.EndBusyCursor()
                ret = wx.MessageBox(_msg,
                    style=wx.CANCEL|wx.OK|wx.ICON_ERROR|wx.CENTER,
                    caption=_("Error"), parent=self)
                _msg = None
                if ret == wx.OK:
                    event.Skip()
                else:
                    self.repo_name_text_ctrl.SetFocus()
                return

        if _msg:
            wx.EndBusyCursor()
            wx.MessageBox(_msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER,  caption=_("Error"), parent=self)
            self.repo_name_text_ctrl.SetFocus()
            return
        wx.EndBusyCursor()
        event.Skip()


    def _check_if_entitled_support_repo(self, url, ssl_key=None, ssl_cert=None):
        '''
        Checks if the specified url is likely an entitled support publisher.
        A url is considered an entitled support publisher if:
            - It's https
            - The last component is "support"
            - The host is known to host support publishers

        If the url points to a support repo then the following tuple
        is returned:
            hostname                The hostname from the url passed in
            credentials_provided    True if SSL credentials were provided,
                                    False if they were not
            more_info_url           A url to more information that the user can
                                    reference

        If the url does not point to a support repo then (None, None, None)
        is returned.
        '''
        support_repo_hosts = {
            # Repo host          For more info URL
            "pkg.sun.com" : "http://pkg.sun.com/layered/doc/supportrepositories.html",
            "pkg.oracle.com" : "http://pkg.oracle.com/layered/doc/supportrepositories.html",
        }

        if url is None or len(url) == 0:
            return (None, None, None)

        o = urlparse(url)
        _scheme = o[0]
        _netloc = o[1]
        _path = o[2]
        if _scheme != "https":
            return (None, None, None)
        if not _path.endswith("support") and not _path.endswith("support/"):
            return (None, None, None)

        for key in support_repo_hosts.keys():
            if _netloc.startswith(key):
                cred = False
                if ssl_key is not None and ssl_cert is not None and \
                                        len(ssl_key) > 0 and len(ssl_cert) > 0:
                    cred = True
                return ( _netloc, cred, support_repo_hosts[key] )

        return (None, None, None)


    def get_repo_name(self):
        """TODO: Return text or return None"""
        return self.repo_name_text_ctrl.GetValue()


    def get_repo_url(self):
        """TODO: Return text or return None"""
        return self.repo_url_text_ctrl.GetValue()


    def get_ssl_key(self):
        """TODO: Return text or return None"""
        return self.repo_ssl_key_ctrl.GetPath()


    def get_ssl_cert(self):
        """TODO: Return text or return None"""
        return self.repo_ssl_cert_ctrl.GetPath()


    def _find_matching_pair(self, path):
        """
        A Certificate consists of two files: a certificate file
        (.certificate.pem) and a key file (.key.pem). When given a path
        to one of those files this routine returns a tuple contain
        the paths to both files:
            ( path_to_cert_file, path_to_key_file)
        In order to return the paths both files must exist.
        If no match is found or both files don't exist then this
        routine returns (None, None)
        """

        # Possible pairs of suffixes
        suffixpairs = (
           (".key.pem" , ".certificate.pem"),
           (".key" ,  ".certificate"),
           (".key.pem" , ".cert.pem"),
           (".key" ,  ".cert"),
        )

        path = path.strip()
        for suffixpair in suffixpairs:
            (keysuffix, certsuffix) = suffixpair
            if path.endswith(keysuffix):
                base = path.rsplit(keysuffix)[0]
                cert_path = base + certsuffix
                if os.path.exists(cert_path) and os.path.exists(path):
                    return (cert_path, path)
            elif path.endswith(certsuffix):
                base = path.rsplit(certsuffix)[0]
                key_path = base + keysuffix
                if os.path.exists(key_path) and os.path.exists(path):
                    return (path, key_path)

        return (None, None)

# end of class RepoHelperDialog
