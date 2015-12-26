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

import wx

from common.mixins import KeywordArgsMixin
from gui.appinfonotebook import AppInfoNotebook
from common.fsutils import fsenc, fsdec
from pkg.client.progress import QuietProgressTracker

import common.utils as utils
import pkg.misc as pkgmisc
import os.path
import pkg.client.image as pkgimage

import gettext
if False:
    _ = gettext.gettext

try:
    import cStringIO as sIO
except ImportError, e:
    import StringIO as sIO



class PkgDetailsPanel(wx.Panel, KeywordArgsMixin):
    _ = wx.GetTranslation


    def __init__(self, *args, **kwargs):
        # PkgDetailsPanel           Panel
        # (sizer_pkg_details_panel)
        #   comp_title_bar          Panel
        #   (sizer_component_title) BoxSizer
        #       comp_icon           StaticBitmap
        #       comp_name           StaticText
        #   main_tabs               AppInfoNotebook
        KeywordArgsMixin.__init__(self)
        wx.Panel.__init__(self, *args, **kwargs)

        self.comp_title_bar = wx.Panel(self, -1, style=wx.NO_BORDER|wx.TAB_TRAVERSAL)
        self.main_tabs = AppInfoNotebook(self, -1)

        self.comp_icon = wx.StaticBitmap(self.comp_title_bar, -1)
        self.comp_name = wx.StaticText(self.comp_title_bar, -1)
        font = self.comp_name.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.comp_name.SetFont(font)

        self.__do_layout()


    def __do_layout(self):
        sizer_component_title = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pkg_details_panel = wx.BoxSizer(wx.VERTICAL)
        sizer_component_title.Add(self.comp_icon, 0, wx.ALL|wx.ALIGN_CENTER, 10)
        sizer_component_title.Add(self.comp_name, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 4)
        self.comp_title_bar.SetSizer(sizer_component_title)
        sizer_pkg_details_panel.Add(self.comp_title_bar, 0, wx.BOTTOM|wx.EXPAND, 4)
        sizer_pkg_details_panel.Add(self.main_tabs, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_pkg_details_panel)
        self.main_tabs.MoveAfterInTabOrder(self.comp_title_bar)


    def describe_view(self, u_imagedir, view):
        self.comp_title_bar.Hide()
        self.main_tabs.describe_view(u_imagedir, view)
        self.Layout()


    def describe_component(self, u_imagedir, fmri):
        self.main_tabs.describe_component(u_imagedir, fmri)
        self.comp_icon.SetBitmap(self.future_get_package_icon(u_imagedir, fmri))
        self.comp_name.SetLabel(self.main_tabs.description)
        if not self.comp_title_bar.IsShown():
            self.comp_title_bar.Show(True)
            self.Layout()
        self.Refresh()


    def future_get_package_icon(self, u_imagedir, fmri):
        """
        Gets the icon associated with a package using the manifest file.

        This method must be modified in future when IPS team is implementing the
        icon attribute for packages. ImageInterface must be used when an Image
        object is made available.

        @keyword u_imagedir: The image directory to get the components detail for
        @type u_imagedir: unicode string literal

        @keyword fmri: The package FMRI object.
        @type fmri: pkg.fmri.PkgFmri
        """
        try:
            comp_icon = None
            img = pkgimage.Image()
            img.history.client_name = 'updatetool'
            img.history.operation_name = 'list'
            img.find_root(fsenc(u_imagedir))
            img.load_config()
            img.load_catalogs(QuietProgressTracker())
            manifest = img.get_manifest(fmri)
            hash = manifest.get('pkg.icon.24px', "")
            file_actions = list(manifest.gen_actions_by_type('file'))
            if len(file_actions) != 0:
                for file_action in file_actions:
                    if hash == file_action.hash:
                        if img.is_installed(fmri):
                            comp_icon = wx.Image(fsdec(os.path.join(u_imagedir, file_action.attrs["path"])), wx.BITMAP_TYPE_ANY).ConvertToBitmap()
                            return comp_icon
                        else :
                            sio = sIO.StringIO()
                            pkgmisc.gunzip_from_stream(file_action.get_remote_opener(img, fmri)(), sio)
                            comp_icon = wx.ImageFromStream(sIO.StringIO(sio.getvalue())).ConvertToBitmap()
                            sio.close()
                            return comp_icon
        except:
            utils.logger.error(utils.format_trace())
        return utils.get_image("package-24x24.png")

