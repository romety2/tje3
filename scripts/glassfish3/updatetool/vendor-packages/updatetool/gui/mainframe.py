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

"""The Main Frame of the Update Tool application"""

import common.info as INFO
from common.boot import UPDATETOOL_LOCALE, n_, safe_decode
from common.fsutils import fsenc, fsdec, FSENC
from common.ips.apptask import ImagePlanTask, ImageUpdateTask
from common import messages
import os.path
import time
import subprocess
import httplib
import urllib2

import pkg
import pkg.client.image as pkgimage
import pkg.client.imageplan as pkgimageplan
from pkg.client.api_errors import CatalogRefreshException, ImageNotFoundException, ApiException, InventoryException
from pkg.client.api_errors import PermissionsException, InvalidDepotResponseException, PlanCreationException
from pkg.client.api_errors import ActionExecutionError, RetrievalError, TransportError
from pkg.client.progress import QuietProgressTracker
from pkg.client import global_settings
from pkg.client.constraint import ConstraintException
from pkg.fmri import PkgFmri
from common.basicfeed import BasicFeed

from pkg.client.api import ImageInterface, PackageInfo

import sys
import gc

import wx
from wx.html import HtmlHelpController
from gui import views
from common import listers, lockmanager
from common.widgets.appthrobber import AppThrobber
from common.widgets.appsearchcontrol import UTSearchCtrl
from common import ips, utils, ipcservice, fileutils
import common.basicfeed as bf
import ConfigParser

from gui.checklistctrl import InstalledCheckListCtrl, AvailableCheckListCtrl, UpdatesCheckListCtrl
from gui.imagestreecontrol import AppImagesTreeCtrl
from gui.pkgdetailspanel import PkgDetailsPanel
from gui.featureddetailspanel import FeaturedDetailsPanel
from dialogs.imagecreateeditdialog import ImageCreateEditDialog
from dialogs.licensedialog import LicenseDialog
from dialogs.scrollmsgdialog import ScrollMsgBox as msgbox
from dialogs.preopconfirmationdialog import PreOpConfirmationDialog
from dialogs.appprogresstrackerdialog import AppProgressTrackerDialog
from common.task import TASK_END_USER_ABORT, TASK_END_EXCEPTION, TASK_END_SUCCESS
from common import preferences
from common.exception import UpdateToolException
from dialogs.preferencesdialog import PreferencesDialog
from dialogs.authdialog import AuthDialog
from dialogs.fileviewerdialog import FileViewerDialog

import gettext

if False:    # Keep Pylint happy
    _ = gettext.gettext

# TODO : Convert to generic menu creation code
_MENUTEXT_NEW_IMAGE = _("&New Image...\tCtrl+N")
_TOOLTIP_NEW_IMAGE = _("Create a new image")
_MENUTEXT_OPEN_IMAGE = _("&Open Image...\tCtrl+O")
_TOOLTIP_OPEN_IMAGE = _("Open an image already present on the system")
_MENUTEXT_CLOSE_IMAGE = _("&Close Image\tCtrl+W")
_TOOLTIP_CLOSE_IMAGE = _("Remove the selected image from the list")
_MENUTEXT_IMAGE_PROPERTIES = _("Image &Properties...\tCtrl+P")
_TOOLTIP_IMAGE_PROPERTIES = _("Edit the properties of the selected image")
_MENUTEXT_PREFERENCES = _("Preferences...")
_TOOLTIP_PREFERENCES = _("Edit application preferences")
_MENUTEXT_REFRESH = _("&Refresh List\tCtrl+R")
_TOOLTIP_REFRESH = _("Refresh components list")
_MENUTEXT_SEARCH = _("&Search\tCtrl+E")
_TOOLTIP_SEARCH = _("Search for components")
_MENUTEXT_INSTALL = _("&Install\tCtrl+I")
_TOOLTIP_INSTALL = _("Install marked components")
_MENUTEXT_REMOVE = _("&Remove\tCtrl+D")
_TOOLTIP_REMOVE = _("Remove marked components")
_MENUTEXT_MARK_ALL = _("M&ark All\tCtrl+A")
_TOOLTIP_MARK_ALL = _("Mark all components")
_MENUTEXT_UNMARK_ALL = _("&Unmark All\tCtrl+U")
_TOOLTIP_UNMARK_ALL = _("Unmark all components")
_MENUTEXT_VIEW_RECENT = _("&Show Recent Versions\tCtrl+S")
_TOOLTIP_VIEW_RECENT = _("Toggle between showing recent or relevant version only")
_MENUTEXT_HELP = _("Contents\tF1")
_TOOLTIP_HELP = _("Show help on using %(application name)s") % {'application name':INFO.APP_NAME}
_MENUTEXT_ABOUT = _("About")
_TOOLTIP_ABOUT = _("About %(application name)s") % {'application name':INFO.APP_NAME}
_MENUTEXT_VIEW_LOG = _("%(application name)s Log") % {'application name':INFO.APP_NAME}
_TOOLTIP_VIEW_LOG = _("View %(application name)s Log") % {'application name':INFO.APP_NAME}
_MENUTEXT_QUIT = _("&Quit\tCtrl+Q")
_TOOLTIP_QUIT = _("Quit %(application name)s") % {'application name':INFO.APP_NAME}



class MainFrame(wx.Frame):
    """The main frame of the Update Tool application"""

    _ = wx.GetTranslation
    APP_ID_INSTALL = wx.NewId()
    APP_ID_SEARCH = wx.NewId()
    APP_ID_REMOVE = wx.NewId()
    APP_ID_CLOSE_IMAGE = wx.NewId()
    APP_ID_EDIT_IMAGE = wx.NewId()
    APP_ID_UNMARK_ALL = wx.NewId()
    APP_ID_MARK_ALL = wx.NewId()
    APP_ID_VIEW_RECENT = wx.NewId()
    APP_ID_VIEW_LOG = wx.NewId()


    #CATEGORIES = [
    #    (_('Web Application Servers'), 'browse-servers-24x24.png'),
    #    (_('Identity Management'), 'browse-identity-management-24x24.png'),
    #    (_('Databases and Tools'), 'browse-databases-24x24.png'),
    #    (_('Developer Tools'), 'browse-developer-tools-24x24.png'),
    #    (_('Operating Systems'), 'browse-operating-systems-24x24.png'),
    #]

    def __init__(self, *args, **kwds):
        self._shutdown = False
        self.help = None                # We lazy init it first successful help access
        self.u_cached_last_dir = None     # provide facility to remember the last dir in directory
                                        # dialogs when OSes do not maintain the cache

        #Load initial config.
        self.config = preferences.Preferences(kwds['config'])
        utils.create_logger(self.config)
        utils.log_system_information()
        del kwds['config']

        self.version = utils.get_version()

        self._show_old_updates = kwds['show_old_updates']
        del kwds['show_old_updates']

        self._enable_feature_feed = kwds['enable_feature_feed']
        del kwds['enable_feature_feed']

        self._prev_sort_col = -1
        self._prev_sort_flag = 1
        self._prev_imagedir = None
        self._prev_view = None
        self.worker = None
        self.view_recent = False

        # Pre_mark is a dictionary keyed by imagedir that contains
        # a list of packages to pre_mark for installation.
        self._pre_mark_table = { }

        # Featured software feed
        basicfeed = None
        # Details about featured software in right panel
        self.featured_details_panel = None
        self.ad_panel = None

        self._imagedir_destroy_list = [ ]

        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.main_splitter = wx.SplitterWindow(self, -1, style=wx.SP_NOBORDER)
        self.right_panel = wx.Panel(self.main_splitter, -1, style=wx.NO_BORDER|wx.TAB_TRAVERSAL)
        self.right_splitter = wx.SplitterWindow(self.right_panel, -1, style=wx.SP_BORDER)

        self.top_right = wx.Panel(self.right_splitter, -1, style=wx.NO_BORDER|wx.TAB_TRAVERSAL)
        self.list_ctrl = wx.Panel(self.top_right, -1, style=wx.NO_BORDER|wx.TAB_TRAVERSAL)
        self.list_msg = wx.StaticText(self.top_right, -1, "")
        _font = self.list_msg.GetFont()
        _font.SetWeight(wx.BOLD)
        self.list_msg.SetFont(_font)
        self.list_msg.SetBackgroundColour(wx.WHITE)
        self.top_right.SetBackgroundColour(wx.WHITE)

        self.pkg_details_panel = PkgDetailsPanel(self.right_splitter, -1, style=wx.NO_BORDER|wx.TAB_TRAVERSAL)
        self.left_panel = wx.Panel(self.main_splitter, -1, style=wx.NO_BORDER|wx.TAB_TRAVERSAL)

        # Menu Bar
        self.menubar = wx.MenuBar()
        file_menu = wx.Menu()
        file_new = wx.MenuItem(file_menu, wx.ID_NEW, _MENUTEXT_NEW_IMAGE, _TOOLTIP_NEW_IMAGE, wx.ITEM_NORMAL)
        file_new.SetBitmap(utils.get_image("menu-new-16x16.png"))
        file_menu.AppendItem(file_new)
        file_open = wx.MenuItem(file_menu, wx.ID_OPEN, _MENUTEXT_OPEN_IMAGE, _TOOLTIP_OPEN_IMAGE, wx.ITEM_NORMAL)
        file_open.SetBitmap(utils.get_image("menu-open-16x16.png"))
        file_menu.AppendItem(file_open)
        file_menu.AppendSeparator()
        file_close = wx.MenuItem(file_menu, MainFrame.APP_ID_CLOSE_IMAGE, _MENUTEXT_CLOSE_IMAGE, _TOOLTIP_CLOSE_IMAGE, wx.ITEM_NORMAL)
        file_close.SetBitmap(utils.get_image("menu-close-16x16.png"))
        file_menu.AppendItem(file_close)
        file_menu.AppendSeparator()
        file_prop = wx.MenuItem(file_menu, MainFrame.APP_ID_EDIT_IMAGE, _MENUTEXT_IMAGE_PROPERTIES, _TOOLTIP_IMAGE_PROPERTIES, wx.ITEM_NORMAL)
        file_prop.SetBitmap(utils.get_image("menu-properties-16x16.png"))
        file_menu.AppendItem(file_prop)
        file_menu.AppendSeparator()
        file_quit = wx.MenuItem(file_menu, wx.ID_EXIT, _MENUTEXT_QUIT, _TOOLTIP_QUIT, wx.ITEM_NORMAL)
        file_quit.SetBitmap(utils.get_image("menu-exit-16x16.png"))
        file_menu.AppendItem(file_quit)
        self.menubar.Append(file_menu, _("&File"))
        edit_menu = wx.Menu()
        edit_search = wx.MenuItem(edit_menu, MainFrame.APP_ID_SEARCH, _MENUTEXT_SEARCH, _TOOLTIP_SEARCH, wx.ITEM_NORMAL)
        edit_search.SetBitmap(utils.get_image("menu-search-16x16.png"))
        edit_menu.AppendItem(edit_search)
        edit_menu.AppendSeparator()
        edit_install = wx.MenuItem(edit_menu, MainFrame.APP_ID_INSTALL, _MENUTEXT_INSTALL, _TOOLTIP_INSTALL, wx.ITEM_NORMAL)
        edit_install.SetBitmap(utils.get_image("menu-install-16x16.png"))
        edit_menu.AppendItem(edit_install)
        edit_remove = wx.MenuItem(edit_menu, MainFrame.APP_ID_REMOVE, _MENUTEXT_REMOVE, _TOOLTIP_REMOVE, wx.ITEM_NORMAL)
        edit_remove.SetBitmap(utils.get_image("menu-remove-16x16.png"))
        edit_menu.AppendItem(edit_remove)
        edit_menu.AppendSeparator()
        edit_menu.Append(MainFrame.APP_ID_MARK_ALL, _MENUTEXT_MARK_ALL, _TOOLTIP_MARK_ALL, wx.ITEM_NORMAL)
        edit_menu.Append(MainFrame.APP_ID_UNMARK_ALL, _MENUTEXT_UNMARK_ALL, _TOOLTIP_UNMARK_ALL, wx.ITEM_NORMAL)
        edit_menu.AppendSeparator()
        edit_refresh = wx.MenuItem(edit_menu, wx.ID_REFRESH, _MENUTEXT_REFRESH, _TOOLTIP_REFRESH, wx.ITEM_NORMAL)
        edit_refresh.SetBitmap(utils.get_image("menu-refresh-16x16.png"))
        edit_menu.AppendItem(edit_refresh)
        edit_menu.AppendSeparator()
        edit_pref = wx.MenuItem(edit_menu, wx.ID_PREFERENCES, _MENUTEXT_PREFERENCES, _TOOLTIP_PREFERENCES, wx.ITEM_NORMAL)
        edit_pref.SetBitmap(utils.get_image("menu-preferences-16x16.png"))
        edit_menu.AppendItem(edit_pref)
        self.menubar.Append(edit_menu, _("&Edit"))
        view_menu = wx.Menu()
        view_recent = wx.MenuItem(view_menu, MainFrame.APP_ID_VIEW_RECENT, _MENUTEXT_VIEW_RECENT, _TOOLTIP_VIEW_RECENT, wx.ITEM_CHECK)
        view_menu.AppendItem(view_recent)
        self.menubar.Append(view_menu, _("&View"))
        help_menu = wx.Menu()
        help_contents = wx.MenuItem(help_menu, wx.ID_HELP, _MENUTEXT_HELP, _TOOLTIP_HELP, wx.ITEM_NORMAL)
        help_contents.SetBitmap(utils.get_image("menu-contents-16x16.png"))
        help_menu.AppendItem(help_contents)
        help_log = wx.MenuItem(help_menu, MainFrame.APP_ID_VIEW_LOG, _MENUTEXT_VIEW_LOG, _TOOLTIP_VIEW_LOG, wx.ITEM_NORMAL)
        help_menu.AppendItem(help_log)
        help_menu.AppendSeparator()
        help_about = wx.MenuItem(help_menu, wx.ID_ABOUT, _MENUTEXT_ABOUT, _TOOLTIP_ABOUT, wx.ITEM_NORMAL)
        help_about.SetBitmap(utils.get_image("menu-about-16x16.png"))
        help_menu.AppendItem(help_about)
        self.menubar.Append(help_menu, _("&Help"))
        self.SetMenuBar(self.menubar)
        # Menu Bar end

        # private to discourage direct SetStatusText which is to slow on Mac
        self._statusbar = self.CreateStatusBar(2, 0)

        self.imgs_tree = AppImagesTreeCtrl(self.left_panel, -1, style=wx.TR_HAS_BUTTONS|wx.TR_NO_LINES|wx.TR_LINES_AT_ROOT|wx.TR_HIDE_ROOT|wx.TR_DEFAULT_STYLE|wx.NO_BORDER)
        self.imgs_tree.add_image_heading(_("Application Images"))
        featured_feed_url = self.config.get('main', 'featured.feed.url')
        if self._enable_feature_feed and \
           featured_feed_url is not None and \
           len(featured_feed_url) > 0:
            basicfeed = BasicFeed(url=str(featured_feed_url))

        # Right-click Menu for List Views
        self.list_context_menu = wx.Menu()
        list_context_install = wx.MenuItem(self.list_context_menu, MainFrame.APP_ID_INSTALL, _("&Install Marked Components\tCtrl+I"),
                _TOOLTIP_INSTALL, wx.ITEM_NORMAL)
        list_context_install.SetBitmap(utils.get_image("menu-install-16x16.png"))
        self.list_context_menu.AppendItem(list_context_install)
        list_context_remove = wx.MenuItem(self.list_context_menu, MainFrame.APP_ID_REMOVE, _("&Remove Marked Components\tCtrl+D"),
                _TOOLTIP_REMOVE, wx.ITEM_NORMAL)
        list_context_remove.SetBitmap(utils.get_image("menu-remove-16x16.png"))
        self.list_context_menu.AppendItem(list_context_remove)
        self.list_context_menu.AppendSeparator()
        list_context_markall = wx.MenuItem(self.list_context_menu, MainFrame.APP_ID_MARK_ALL, _("M&ark All\tCtrl+A"),
                _TOOLTIP_MARK_ALL, wx.ITEM_NORMAL)
        self.list_context_menu.AppendItem(list_context_markall)
        list_context_unmarkall = wx.MenuItem(self.list_context_menu, MainFrame.APP_ID_UNMARK_ALL, _("&Unmark All\tCtrl+U"),
                _TOOLTIP_UNMARK_ALL, wx.ITEM_NORMAL)
        self.list_context_menu.AppendItem(list_context_unmarkall)
        self.list_context_menu.AppendSeparator()
        list_context_refresh = wx.MenuItem(self.list_context_menu, wx.ID_REFRESH, _("&Refresh List\tCtrl+R"),
                _TOOLTIP_REFRESH, wx.ITEM_NORMAL)
        list_context_refresh.SetBitmap(utils.get_image("menu-refresh-16x16.png"))
        self.list_context_menu.AppendItem(list_context_refresh)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self._make_toolbar()
        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_MENU, self.OnNewImage, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.OnOpenImage, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnCloseImage, id=MainFrame.APP_ID_CLOSE_IMAGE)
        self.Bind(wx.EVT_MENU, self.OnEditImage, id=MainFrame.APP_ID_EDIT_IMAGE)
        self.Bind(wx.EVT_MENU, self.OnExit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.OnSearch, id=MainFrame.APP_ID_SEARCH)
        self.Bind(wx.EVT_MENU, self.OnMarkAll, id=MainFrame.APP_ID_MARK_ALL)
        self.Bind(wx.EVT_MENU, self.OnUnmarkAll, id=MainFrame.APP_ID_UNMARK_ALL)
        self.Bind(wx.EVT_MENU, self.OnRefresh, id=wx.ID_REFRESH)
        self.Bind(wx.EVT_MENU, self.OnPreferences, id=wx.ID_PREFERENCES)
        self.Bind(wx.EVT_MENU, self.OnToggleViewRecentVersions, id=MainFrame.APP_ID_VIEW_RECENT)
        self.Bind(wx.EVT_MENU, self.OnHelp, id=wx.ID_HELP)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.OnViewLog, id=MainFrame.APP_ID_VIEW_LOG)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateShowRecentVersions, id=MainFrame.APP_ID_VIEW_RECENT)
        self.Bind(wx.EVT_TOOL, self.OnNewImage, id=wx.ID_NEW)
        self.Bind(wx.EVT_TOOL, self.OnOpenImage, id=wx.ID_OPEN)
        self.Bind(wx.EVT_TOOL, self.OnPreferences, id=wx.ID_PREFERENCES)
        self.Bind(wx.EVT_TOOL, self.OnRefresh, id=wx.ID_REFRESH)
        self.Bind(wx.EVT_TOOL, self.OnInstall, id=MainFrame.APP_ID_INSTALL)
        self.Bind(wx.EVT_TOOL, self.OnRemove, id=MainFrame.APP_ID_REMOVE)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnImageSelectionChanged, self.imgs_tree)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSING, self.OnImageItemCollapsing, self.imgs_tree)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightClick, self.imgs_tree)
        if '__WXMAC__' == wx.Platform:
            self.left_panel.Bind(wx.EVT_NAVIGATION_KEY, self.OnNavigationKey)
        self.Bind(wx.EVT_ICONIZE, self.OnMinimize) # for issue 762 and 991
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_CLOSE, self.OnCloseFrame)
        global_settings.client_name = INFO.CLIENT_NAME

        flag = self.config.getboolean('network', 'proxy.auth')
        username = ""
        password = ""
        if flag:
            try:
                username = self.config.get('network', 'proxy.username')
            except ConfigParser.NoOptionError, e:
                #It is not an error at this level if the user and/or pass are
                #missing.
                pass

            try:
                password = self.config.get('network', 'proxy.password')
            except ConfigParser.NoOptionError, e:
                #It is not an error at this level if the user and/or pass are
                #missing.
                pass
            if len(password) == 0:
                dlg = AuthDialog(self, -1, _("%(APP_NAME)s: Proxy Authentication") % {'APP_NAME':INFO.APP_NAME})
                if len(username) != 0:
                    dlg.set_auth_info(username)
                dummy = dlg.ShowModal()
                dlg.Destroy()
                if len(os.getenv('HTTP_PROXY_USERNAME')) == 0 and len(os.getenv('HTTP_PROXY_PASSWORD')) == 0:
                    self.Close()
        utils.set_net_proxy(self.config)

        if basicfeed is not None:
            # basicfeed.set_debug_delay(5)
            basicfeed.parse(self.featured_feed_callback)


    def __set_properties(self):
        self.SetTitle(INFO.APP_NAME)
        self.SetSize((1024, 700))
        self._statusbar.SetStatusWidths([-2, -1])
        self._statusbar.SetFields(["", ""])

        # Issue 1131
        self._status_timer_interval = 0
        if '__WXMAC__' == wx.Platform:
            self._status_timer_interval = 0.5 # seconds
            self._last_status_update_time = 0
            self._cached_status_text = [u"", u""]
            status_timer_id = wx.NewId()
            self.status_timer = wx.Timer(self, status_timer_id)
            self.status_timer.Start(400)  # x400 milliseconds
            wx.EVT_TIMER(self, status_timer_id, self.OnStatusBarTimerEvent)  # call the on_timer function
            del status_timer_id

        self.imgs_tree.SetBackgroundColour(wx.Colour(230, 237, 247))
        self.imgs_tree.SetImagesList([views.ICON[views.IMAGE], views.ICON[views.AVAILABLE], views.ICON[views.UPDATES], views.ICON[views.INSTALLED]])
        #self.label_browse_list.SetBackgroundColour(wx.Colour(230, 237, 247))
        #self.browse_list.SetBackgroundColour(wx.Colour(230, 237, 247))
        self.left_panel.SetBackgroundColour(wx.Colour(230, 237, 247))

        icon_bundle = wx.IconBundle()
        if wx.Platform == "__WXMSW__":
            # Using an .ico file results in the icon being displayed
            # when a user uses alt-tab.
            for size in [16, 32, 48]:
                try:
                    icon = wx.Icon(os.path.join(os.path.dirname(__file__), "..", "images",
                        'application-update-tool.ico'), wx.BITMAP_TYPE_ICO,
                        desiredWidth=size, desiredHeight=size)
                    icon_bundle.AddIcon(icon)
                except:
                    pass
        else:
            for size in [16, 48, 72]: # glob module
                icon_bundle.AddIconFromFile(fsdec(os.path.join(os.path.dirname(__file__), "..",
                    "images", "application-update-tool-%sx%s.png" % (size, size))),
                    wx.BITMAP_TYPE_ANY)
        self.SetIcons(icon_bundle)

        # populate 'browser other software' list
        #imgList = wx.ImageList(16, 16)
        #for png in zip(*MainFrame.CATEGORIES)[1]:
            #imgList.Add(utils.get_scaled_image(png, 16, 16))
        #self.browse_list.AssignImageList(imgList, wx.IMAGE_LIST_NORMAL)
        #self.browse_list.InsertColumn(0, "", width=-1, format=wx.LIST_FORMAT_LEFT)
        #for idx, item in enumerate(MainFrame.CATEGORIES):
            #index = self.browse_list.InsertStringItem(sys.maxint, "")
            #self.browse_list.SetStringItem(index, 0, item[0])
            #self.browse_list.SetItemImage(index, idx)
            #self.browse_list.SetColumnWidth(index, 200)

        self.main_splitter.SetMinimumPaneSize(50)
        self.right_splitter.SetMinimumPaneSize(50)
        self.right_splitter.SetSashGravity(0.5)
        self._enable_mark_all(False)
        self._enable_unmark_all(False)
        self._enable_install(False)
        self._enable_remove(False)
        self._enable_refresh(True)
        self.main_splitter.UpdateSize()
        self.right_splitter.UpdateSize()


    def __do_layout(self):
        # main_splitter
        #    right_panel (right_panel_sizer)
        #        featured_details_panel
        #        right_splitter
        #           top_right
        #               list_ctrl
        #               list_msg
        #           pkg_details_panel
        #    left_panel
        #        imgs_tree
        self.right_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer_left_panel = wx.BoxSizer(wx.VERTICAL)
        self.sizer_left_panel.Add(self.imgs_tree, 1, wx.LEFT|wx.EXPAND, 0)
        self.left_panel.SetSizer(self.sizer_left_panel)
        self.right_panel_sizer.Add(self.right_splitter, 1, wx.EXPAND, 0)
        self.right_panel.SetSizer(self.right_panel_sizer)

        if self.ad_panel is not None:
            self.sizer_left_panel.Add(self.ad_panel, 0, wx.EXPAND, 0)

        self.top_right_sizer = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        self.top_right_sizer.Add(self.list_ctrl, 1, wx.EXPAND, 0)
        self.top_right_sizer.Add(self.list_msg, 1, wx.EXPAND|wx.ALL, 5)
        self.list_msg.Hide()
        self.top_right.SetSizer(self.top_right_sizer)
        self.top_right_sizer.Fit(self.top_right)
        self.top_right_sizer.AddGrowableRow(0)
        self.top_right_sizer.AddGrowableRow(1)
        self.top_right_sizer.AddGrowableCol(0)

        self.main_splitter.SplitVertically(self.left_panel, self.right_panel, 220)
        self.right_splitter.SplitHorizontally(self.top_right, self.pkg_details_panel, 260)

        self.main_sizer.Add(self.main_splitter, 1, wx.TOP|wx.EXPAND, 1)
        self.SetSizer(self.main_sizer)
        self.Layout()
        self.Centre()


    def _make_toolbar(self):
        self.toolbar_sizer = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        self.toolbar_sizer.AddGrowableCol(0)
        self.main_sizer.Add(self.toolbar_sizer, flag=wx.GROW)

        self.toolbar = AppToolBar(self)
        _size = self.toolbar.size
        self.toolbar.AddLabelTool(wx.ID_NEW, _("New Image"),
            utils.get_image("toolbar-new-%dx%d.png" % (_size, _size)),
            wx.NullBitmap, wx.ITEM_NORMAL, _TOOLTIP_NEW_IMAGE, _TOOLTIP_NEW_IMAGE)
        self.toolbar.AddLabelTool(wx.ID_OPEN, _("Open Image"),
            utils.get_image("toolbar-open-%dx%d.png" % (_size, _size)),
            wx.NullBitmap, wx.ITEM_NORMAL, _TOOLTIP_OPEN_IMAGE, _TOOLTIP_OPEN_IMAGE)
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(wx.ID_PREFERENCES, _("Preferences"),
            utils.get_image("toolbar-preferences-%dx%d.png" % (_size, _size)),
            wx.NullBitmap, wx.ITEM_NORMAL, _TOOLTIP_PREFERENCES, _TOOLTIP_PREFERENCES)
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(wx.ID_REFRESH, _("Refresh"),
            utils.get_image("toolbar-refresh-%dx%d.png" % (_size, _size)),
            wx.NullBitmap, wx.ITEM_NORMAL, _TOOLTIP_REFRESH, _TOOLTIP_REFRESH)
        self.toolbar.AddLabelTool(MainFrame.APP_ID_INSTALL, _("Install"),
            utils.get_image("toolbar-install-%dx%d.png" % (_size, _size)),
            wx.NullBitmap, wx.ITEM_NORMAL, _TOOLTIP_INSTALL, _TOOLTIP_INSTALL)
        self.toolbar.AddLabelTool(MainFrame.APP_ID_REMOVE, _("Remove"),
            utils.get_image("toolbar-remove-%dx%d.png" % (_size, _size)),
            wx.NullBitmap, wx.ITEM_NORMAL, _TOOLTIP_REMOVE, _TOOLTIP_REMOVE)
        self.toolbar.Realize()

        self.search_toolbar = AppToolBar(self)

        if '__WXMSW__' in wx.PlatformInfo:
            # Add a fake item to have the right toolbar resize vertically completely on windows
            temp_id = wx.NewId()
            self.search_toolbar.AddLabelTool(temp_id, _(" "), utils.get_image("transparent-%dx%d.png" %(_size, _size)),
                    wx.NullBitmap, wx.ITEM_NORMAL)
            self.search_toolbar.EnableTool(temp_id, False)
            del temp_id

        focus_forward = [self.right_panel, self.left_panel]
        focus_backward = [self.left_panel, self.right_panel]
        self.search_ctrl = UTSearchCtrl(self.search_toolbar, size=(150, -1), doSearch=self.DoSearch,
                            focusForward=focus_forward, focusBackward=focus_backward)
        self.search_ctrl.SetToolTipString(_("Search for components"))
        self.search_ctrl.SetDescriptiveText(_("Search"))
        self.search_toolbar.AddControl(self.search_ctrl)
        if '__WXMAC__' in wx.PlatformInfo:
            self.throbber = AppThrobber(self.search_toolbar, -1, isize=(16, 16), vsize=(32, 32))
        else:
            self.throbber = AppThrobber(self.search_toolbar, -1, isize=(16, 16), vsize=(24, 24))
        self.search_toolbar.AddControl(self.throbber)
        self.search_toolbar.Realize()

        self.toolbar_sizer.Add(self.toolbar, 0, flag=wx.EXPAND) #, flag=|wx.ALIGN_CENTER_VERTICAL)
        self.toolbar_sizer.Add(self.search_toolbar, 1) #, flag=wx.GROW|wx.ALIGN_CENTER_VERTICAL)
        if '__WXMSW__' not in wx.PlatformInfo:
            szt = self.toolbar.GetClientSize()
            szs = self.search_toolbar.GetClientSize()
            self.toolbar_sizer.SetItemMinSize(self.search_toolbar, szs.width, szt.height)


    def _init_list_ctrl(self, view=None, columns=None, size_col=-1, sort_col=1):
        assert columns is not None
        assert view in views.LIST_VIEWS

        cols = columns
        num_cols = len(cols)

        # Issue 248 - ugly rectangle flicker
        self.right_panel.Freeze()

        if view == views.AVAILABLE:
            new_list_ctrl = AvailableCheckListCtrl(self.top_right, -1,
                    num_cols=num_cols, size_column=size_col, default_sort_column=sort_col)
        elif view == views.UPDATES:
            new_list_ctrl = UpdatesCheckListCtrl(self.top_right, -1,
                    num_cols=num_cols, size_column=size_col, default_sort_column=sort_col)
        elif view == views.INSTALLED:
            new_list_ctrl = InstalledCheckListCtrl(self.top_right, -1,
                    num_cols=num_cols, size_column=size_col, default_sort_column=sort_col)
        col_info = wx.ListItem()
        col_info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
        for index, col in enumerate(cols):
            col_info.m_text = col[0]
            col_info.m_format = col[2]
            new_list_ctrl.InsertColumnInfo(index, col_info)
            new_list_ctrl.SetColumnWidth(index, col[1])

        self.top_right_sizer.Replace(self.list_ctrl, new_list_ctrl)
        if not self.right_splitter.IsSplit():
            self.right_splitter.SplitHorizontally(self.top_right, self.pkg_details_panel, 260)
        self.top_right_sizer.Layout()
        self.right_panel.Layout()
        old_list_ctrl, self.list_ctrl = self.list_ctrl, new_list_ctrl

        # [Issue 1134] wx.CallAfter because there might still be some event
        # handlers attached to this one
        wx.CallAfter(old_list_ctrl.Destroy)

        del old_list_ctrl
        self.list_ctrl.resizeLastColumn(cols[len(cols) -1][1] + 1)
        self.list_ctrl.view = view
        self.list_ctrl.old_OnCheckItem = self.list_ctrl.OnCheckItem
        self.list_ctrl.OnCheckItem = self.OnCheckItem
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListItemSelected, self.list_ctrl)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnListRightClick, self.list_ctrl)
        self.list_ctrl.old_OnSortOrderChanged = self.list_ctrl.OnSortOrderChanged
        self.list_ctrl.OnSortOrderChanged = self.OnSortOrderChanged
        self.right_panel.Layout()
        self.right_splitter.UpdateSize()

        self.right_panel.Thaw()


    def OnUpdateShowRecentVersions(self, event):
        # Needed to keep popup and main menu check items in sync
        event.Check(self.view_recent)


    def OnMinimize(self, event): # for issue 762
        # If we are being restored on windows
        if wx.Platform == "__WXMSW__" and not self.IsIconized():
            # Interesting thing is that SashPosition is correct but just didn't get redrawn
            wx.CallAfter(self.main_splitter.SetSashPosition, self.main_splitter.GetSashPosition(), True)
            wx.CallAfter(self.right_splitter.SetSashPosition, self.right_splitter.GetSashPosition(), True)
        else:
            # issue 991 - this should be harmless on all platforms
            if not self.IsIconized():
                self.Raise()
        event.Skip()


    def OnRightClick(self, event):
        item = event.GetItem()

        if not self.imgs_tree.is_application_image_item(item):
            return

        # this attribute acts additionally as an indicator that we came via a right click menu
        self.context_menu_imagedir = self.imgs_tree.GetPyData(item).get_image_udir()

        context_menu = wx.Menu()
        context_close = wx.MenuItem(context_menu, MainFrame.APP_ID_CLOSE_IMAGE, _("&Close\tCtrl+W"), _("Remove the selected image from the list"), wx.ITEM_NORMAL)
        context_close.SetBitmap(utils.get_image("menu-close-16x16.png"))
        context_menu.AppendItem(context_close)
        context_menu.AppendSeparator()
        context_prop = wx.MenuItem(context_menu, MainFrame.APP_ID_EDIT_IMAGE, _("&Properties...\tCtrl+P"), _("Edit the properties of the selected image"), wx.ITEM_NORMAL)
        context_prop.SetBitmap(utils.get_image("menu-properties-16x16.png"))
        context_menu.AppendItem(context_prop)
        self.imgs_tree.PopupMenu(context_menu)

        # clear the attribute so that further close/edit operations don't reuse this
        del self.context_menu_imagedir

        context_menu.Destroy()


    def OnSortOrderChanged(self):
        if isinstance(self.list_ctrl, wx.ListCtrl):
            self._prev_imagedir, self._prev_view = self.imgs_tree.get_image_view()[0:2]
            self._prev_sort_col, self._prev_sort_flag = self.list_ctrl.GetSortState()
            self.list_ctrl.old_OnSortOrderChanged()


    def OnListRightClick(self, event):
        the_list = event.GetEventObject()
        if the_list.is_updating():
            event.Skip()
            return
        # Append or remove the last separator and recent item entries based on the view
        if the_list.view in [views.AVAILABLE, views.UPDATES]:
            # Add the recent items menuitem
            i = self.list_context_menu.FindItemById(MainFrame.APP_ID_VIEW_RECENT)
            if i is None:
                items = self.list_context_menu.GetMenuItems()
                itemcount = self.list_context_menu.GetMenuItemCount()
                if itemcount < 1:
                    self.list_context_menu.AppendSeparator()
                else:
                    i = items.__getitem__(itemcount-1)
                    if not i.IsSeparator():
                        self.list_context_menu.AppendSeparator()
                    i = wx.MenuItem(self.list_context_menu, MainFrame.APP_ID_VIEW_RECENT, _MENUTEXT_VIEW_RECENT, _TOOLTIP_VIEW_RECENT, wx.ITEM_CHECK)
                    self.list_context_menu.AppendItem(i)
                    self.Bind(wx.EVT_MENU, self.OnToggleViewRecentVersions, i)
                    self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateShowRecentVersions, i)
            i.Enable(True)
        else:
            items = self.list_context_menu.GetMenuItems()
            itemcount = self.list_context_menu.GetMenuItemCount()
            i = self.list_context_menu.FindItemById(MainFrame.APP_ID_VIEW_RECENT)
            if i in items:
                self.list_context_menu.RemoveItem(i)
                itemcount -= 1
                if itemcount > 0:
                    i = items.__getitem__(itemcount-1)
                    if i.IsSeparator():
                        self.list_context_menu.RemoveItem(i)

        the_list.PopupMenu(self.list_context_menu)
        event.Skip()


    def OnListItemSelected(self, event):
        # This is presumably thread safe as the component has obviously already been listed
        # and the manifests fetched.
        if event.GetId() != self.list_ctrl.GetId() or not self.list_ctrl.IsShown():
            return
        imagedir = self.imgs_tree.get_image_view()[0]
        fmri = self.list_ctrl.get_fmri(event.m_itemIndex)
        self.pkg_details_panel.describe_component(imagedir, fmri)
        self.list_ctrl.SetFocus()
        event.Skip()


    def OnCheckItem(self, idx, flag):
        self.list_ctrl.old_OnCheckItem(idx, flag)
        if self.list_ctrl.view == views.INSTALLED:
            if not self.list_ctrl.is_updating():
                self._enable_remove(self.list_ctrl.checked_count)
        elif self.list_ctrl.view in [views.AVAILABLE, views.UPDATES]:
            if not self.list_ctrl.is_updating():
                self._enable_install(self.list_ctrl.checked_count)
        else:
            # This should not happen
            utils.logger.error("OnCheckItem called in unknown view")
            wx.MessageBox(_("An unexpected error occurred. Application will now close to prevent data corruption."),
                    style=wx.OK|wx.ICON_INFORMATION|wx.CENTER, caption=_("Internal error"), parent=self)

        self._enable_mark_all(self.list_ctrl.GetItemCount() and self.list_ctrl.GetItemCount() != self.list_ctrl.checked_count)
        self._enable_unmark_all(self.list_ctrl.checked_count)

        self.update_top_status()


    def OnExit(self, dummy_event):
        """
        Handles wx.ID_EXIT e.g. in Menu item etc. and asks the frame to close.
        """
        self.Close()


    def OnCloseFrame(self, dummy_event):
        """
        Perform cleanup when the application frame close by the user clicking the Frame close button or
        manually via L{OnExit} calling C{Close()}. Manually bound via C{wx.EVT_CLOSE}.
        """

        # If we are using timers on this platform
        self._shutdown = True
        if self._status_timer_interval > 0:
            self._status_timer_interval = 0
            self.status_timer.Stop()
            self.status_timer = None
        lockmanager.lock()
        lockmanager.abort_all()
        lockmanager.release()
        wx.YieldIfNeeded()

        # Pause to check whether we need to display a wait dialog or not
        _sec = 2
        while lockmanager.any_active() and _sec > 0: # OK to access if unlocked?
            wx.MilliSleep(500)
            _sec -= 1

        if lockmanager.any_active(): # OK to access if unlocked?
            wx.YieldIfNeeded()
            self.Unbind(listers.EVT_LISTING_COMPONENT)
            self.Hide()
            wx.YieldIfNeeded()
            lockmanager.lock()
            lockmanager.abort_all()
            lockmanager.release()
            _cnt = 0
            _tm = time.time()
            while lockmanager.any_active() and (time.time() - _tm) < 60: # OK to access if unlocked?
                wx.YieldIfNeeded()
                if _cnt % 5 == 0:
                    utils.logger.debug(str(lockmanager.any_active()) + " threads still active")
                wx.MilliSleep(1000) # sadly, this interferes with the throbber timer
                wx.YieldIfNeeded()
                _cnt += 1
            del _cnt
        if self.IsShown():
            self.Hide()
        self.Destroy()


    def OnAbout(self, dummy_event):
        utils.display_about(self)


    def OnViewLog(self, dummy_event):
        '''
        Display Update Tool's log file
        '''
        wx.BeginBusyCursor()
        dlg = FileViewerDialog(self,
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER,
            title=_("Update Tool Log File"), size=(800, 400))
        dlg.load_file(utils.log_file_path)
        dlg.Center()
        dlg.Show()
        # Pause for dramatic effect
        wx.MilliSleep(250)
        wx.EndBusyCursor()


    def OnOpenImage(self, dummy_event):
        """
        Open (an existing image) event handler
        """
        dlg = wx.DirDialog(self, _("Choose Installation Image Directory"), style=wx.DD_DEFAULT_STYLE)
        if self.u_cached_last_dir and os.path.isdir(fsenc(self.u_cached_last_dir)):
            dlg.SetPath(self.u_cached_last_dir)

        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return

        u_chosen_dir = dlg.GetPath()

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()

        u_chosen_dir = os.path.expanduser(u_chosen_dir) # Expand ~ etc.
        self.u_cached_last_dir = u_chosen_dir
        u_chosen_dir, success = self.add_image(u_chosen_dir, quiet=False, opname='list')
        self.imgs_tree.select_image_node(u_chosen_dir)
        self.save_images_list()


    def OnIdle(self, dummy_event):
        """
        We lock if we start an image/view and don't release it.
        """
        if lockmanager.is_locked():
            return

        lockmanager.lock()
        img, view = lockmanager.get_desired_image_view()
        # If a view for a non-active image is desired, switch to it
        if img is not None and lockmanager.get_image_state(img)[0] is None:
            utils.logger.debug("OnIdle - Desired is " + repr(img) + " " + repr(view))

            # Issue 1430 - race condition between the old list and new view
            try:
                self.Unbind(wx.EVT_LIST_ITEM_SELECTED, self.list_ctrl)
            except:
                pass
            try:
                self.list_ctrl.Unbind(wx.EVT_LIST_ITEM_RIGHT_CLICK)
            except:
                pass
            self.Unbind(listers.EVT_LISTING_COMPONENT)

            lockmanager.flag_abort_except(img)
            lockmanager.set_desired_image_view(None, None)
            try:
                self.update_image_view(img, view)
            except:
                utils.logger.debug("Logging error in OnIdle")
                utils.logger.error(utils.format_trace())
                if lockmanager.is_locked():
                    lockmanager.release()
            self.imgs_tree.SetFocus()
        else:
            lockmanager.release()

        # We may have pending imagedirs to cleanup from an aborted
        # application install. We do this here because it helps to ensure
        # any gyrations involved with the image are complete.
        if self._imagedir_destroy_list:
            for path in self._imagedir_destroy_list:
                try:
                    # Likely uneccessary, but force a GC to ensure any objects
                    # that could be holding a reference to a file are collected.
                    gc.collect()
                    utils.logger.info("Removing cancelled install directory %s" % path)
                    ips.destroy_image(path)
                except OSError, e:
                    utils.logger.warning("OSError removing image directory %s" % e)
                    utils.logger.debug(utils.format_trace())
                except Exception, e:
                    utils.logger.warning("Error removing image directory %s: %s" % (path, e))
                    utils.logger.debug(utils.format_trace())

        self._imagedir_destroy_list = [ ]


    def OnImageItemCollapsing(self, event):
        item = event.GetItem()
        # Prevent user from Collapsing a heading item
        if self.imgs_tree.is_heading(item):
            event.Veto()
        else:
            event.Skip()


    def OnImageSelectionChanged(self, event):
        lockmanager.lock()

        item = event.GetItem()
        utils.logger.debug("OnImageSelectionChanged: " + repr(item))
        root = self.imgs_tree.GetRootItem()
        heading_item = self.imgs_tree.image_heading_item
        featured_heading_item = self.imgs_tree.featured_heading_item

        # If item is the root item then no active selection
        if item == root:
            # XXX : Issue 1272 is happening here
            self.set_list_msg(_("Please create or open a new image"))
            self.pkg_details_panel.describe_view(None, None)
            lockmanager.release()
            return

        if self.imgs_tree.is_heading(item):
            # Selection on one of the tree section headings. A no-op
            lockmanager.release()
            return

        if item is None or not item.IsOk() or item == root:
            utils.logger.debug("OnImageSelectionChanged returning cuz invalid")
            lockmanager.release()
            return

        img = None
        view = None
        pnode = self.imgs_tree.GetItemParent(item)
        if pnode == heading_item:
            img = self.imgs_tree.GetPyData(item).get_image_udir()
            view = views.IMAGE
        elif pnode == featured_heading_item:
            # Featured software node
            pydata = self.imgs_tree.GetItemPyData(item)
            self.featured_callback(self.imgs_tree, pydata)
            lockmanager.release()
            return
        else:
            pdata = self.imgs_tree.GetPyData(item)
            img = pdata.get_image_udir()
            view = pdata.get_view_type()

        cv, cs = lockmanager.get_image_state(img)
        utils.logger.debug("OnImageSelectionChanged - active state for " + repr(img) + " is " + repr(cv) + "/" + repr(cs))
        utils.logger.debug("OnImageSelectionChanged - desired state for " + repr(img) + " is " + repr(view))

        if cv == None:
            lockmanager.set_desired_image_view(img, view)
            lockmanager.release()
            return
        elif cv == view:
            if cs == lockmanager.RUNNING:
                lockmanager.release()
                return
            elif cs == lockmanager.ABORT:
                lockmanager.set_desired_image_view(img, view)
                lockmanager.release()
                return
            else:
                raise Exception("This should not happen")
        else:
            lockmanager.flag_abort(img)
            lockmanager.set_desired_image_view(img, view)
            lockmanager.release()
            return


    def OnNavigationKey(self, event):
        '''
        This is needed for the Mac, because for some reason it has trouble
        tabbing into the imgs_tree. This forces the focus to the imgs_tree
        when the user has traversed to it using mouseless
        '''
        focus_window = event.GetCurrentFocus()
        if focus_window != self.left_panel and focus_window != self.imgs_tree:
            self.imgs_tree.SetFocus()
        else:
            event.Skip()


    def _enable_install(self, boolean):
        self.toolbar.EnableTool(MainFrame.APP_ID_INSTALL, boolean)
        self.GetMenuBar().Enable(MainFrame.APP_ID_INSTALL, boolean)
        self.list_context_menu.Enable(MainFrame.APP_ID_INSTALL, boolean)


    def _enable_remove(self, boolean):
        self.toolbar.EnableTool(MainFrame.APP_ID_REMOVE, boolean)
        self.GetMenuBar().Enable(MainFrame.APP_ID_REMOVE, boolean)
        self.list_context_menu.Enable(MainFrame.APP_ID_REMOVE, boolean)


    def _enable_mark_all(self, boolean):
        self.GetMenuBar().Enable(MainFrame.APP_ID_MARK_ALL, boolean)
        self.list_context_menu.Enable(MainFrame.APP_ID_MARK_ALL, boolean)


    def _show_enable_search(self, show_boolean, enable_boolean):
        if show_boolean:
            self.search_ctrl.Show()
        else:
            self.search_ctrl.Hide()
        self.search_ctrl.Enable(enable_boolean)
        self.GetMenuBar().Enable(MainFrame.APP_ID_SEARCH, enable_boolean)


    def _enable_unmark_all(self, boolean):
        self.GetMenuBar().Enable(MainFrame.APP_ID_UNMARK_ALL, boolean)
        self.list_context_menu.Enable(MainFrame.APP_ID_UNMARK_ALL, boolean)


    def _enable_refresh(self, boolean):
        self.GetMenuBar().Enable(wx.ID_REFRESH, boolean)
        self.toolbar.EnableTool(wx.ID_REFRESH, boolean)
        self.list_context_menu.Enable(wx.ID_REFRESH, boolean)


    def _enable_recent(self, boolean):
        # Show recent version toggle works like refresh
        self.GetMenuBar().Enable(MainFrame.APP_ID_VIEW_RECENT, boolean)
        i = self.list_context_menu.FindItemById(MainFrame.APP_ID_VIEW_RECENT)
        if i is not None:
            i.Enable(boolean)


    def _get_maximum_recent_items(self):
        if self.view_recent:
            max_recent = self.config.get('main', 'maximum_recent_items')
            if isinstance(max_recent, basestring) and max_recent.strip() == 'None': # string 'None'
                max_recent = preferences.MAX_RECENT_ITEMS
            elif max_recent is None:
                max_recent = preferences.MAX_RECENT_ITEMS
            elif max_recent.isdigit():
                max_recent = int(max_recent)
                if max_recent > preferences.MAX_RECENT_ITEMS:
                    max_recent = preferences.MAX_RECENT_ITEMS
            else:
                max_recent = int(preferences.get_default('main', 'maximum_recent_items', '3'))
        else:
            max_recent = 1

        return max_recent


    def update_image_view(self, imagedir=None, view=None, enabled=True):
        """
        NOTE: If you pass an imagedirectory and a view then make sure to have a
        lockmanager.lock() which we will release.

        @type enabled: C{bool}
        @param enabled: Whether this node is enabled or not
        """
        self.search_ctrl.Clear()
        if self.featured_details_panel is not None:
            self.hide_featured_details_panel()

        if not self.right_splitter.IsShown():
            self.right_splitter.Show()

        self.right_panel.Layout()

        if imagedir is None and view is None:
            lockmanager.lock()
            imagedir, view, enabled = self.imgs_tree.get_image_view()
        elif (imagedir is None and view is not None) or (imagedir is not None and view is None):
            utils.logger.error("Internal error: update_image_view(" + repr(imagedir) + ", " + repr(view) + ")")
            wx.MessageBox(_("An unexpected error occurred. Application will now close to prevent data corruption."),
                    style=wx.OK|wx.ICON_INFORMATION|wx.CENTER, caption=_("Internal error"), parent=self)
            self.Close()
        else:
            # Someone else passed us the image and the view and already has the lock
            pass

        valid_image = True
        if utils.is_v1_image(fsenc(imagedir)) or not os.path.exists(fsenc(imagedir)) or ips.load_image(imagedir)[0] is None:
            valid_image = False

        # This is done to remove the double tab which is showing up because of
        # top status, a flicker in UI update. Issue 911
        if view == views.IMAGE or not valid_image:
            self.set_status("", 1)
            if self.right_splitter.IsSplit():
                self.right_splitter.Unsplit(toRemove=self.top_right)
                self.right_splitter.UpdateSize()
            self.right_panel.Layout()
        else:
            self._list_msg_clear()

        self._show_enable_search(True, False)
        self.set_status("", 1)
        self.throbber.Show()
        self.throbber.Start()

        if imagedir is not None:
            self.config.set("main", "_last_active_image", imagedir.encode('utf-8'))
            self.config.save_config()

        lockmanager.flag_running(imagedir, view)
        lockmanager.release()
        if enabled:
            self.pkg_details_panel.describe_view(imagedir, view)
        else:
            self.pkg_details_panel.describe_view(None, None)

        # Get list (if any) of packages to pre-select for installation
        pre_mark_list = None
        if self._pre_mark_table.has_key(imagedir):
            pre_mark_list = self._pre_mark_table.pop(imagedir)

        # Since we just switched view, there is nothing selected so nothing to apply
        self._enable_mark_all(False)
        self._enable_unmark_all(False)
        self._enable_install(False)
        self._enable_remove(False)
        self._enable_refresh(False)

        if view == views.IMAGE or (view in views.LIST_VIEWS and not valid_image):
            self._enable_refresh(True)
            self.throbber.Rest()
            self._show_enable_search(False, False)
            lockmanager.lock()
            lockmanager.done(imagedir, view)
            lockmanager.release()
            self.set_status("", 1)
            self.imgs_tree.Expand(self.imgs_tree.GetSelection())
            self._enable_recent(True)
            return
        else:
            self._show_enable_search(True, False)
            wx.YieldIfNeeded()

            self._enable_recent(False)
            if view == views.AVAILABLE:
                self.search_ctrl.SetToolTipString(_("Search in available add-ons"))
                self._init_list_ctrl(views.AVAILABLE, [
                    # Label, width, format
                    ("", 30, wx.LIST_FORMAT_CENTER),
                    (_("Component"), 230, wx.LIST_FORMAT_LEFT),
                    (_("Category"), 145, wx.LIST_FORMAT_LEFT),
                    (_("Published"), 100, wx.LIST_FORMAT_CENTER),
                    (_("Version"), 85, wx.LIST_FORMAT_LEFT),
                    (_("Install Size"), 95, wx.LIST_FORMAT_RIGHT),
                    (_("Source"), wx.LIST_AUTOSIZE, wx.LIST_FORMAT_LEFT)
                ], size_col=5, sort_col=2)
                self.Bind(listers.EVT_LISTING_COMPONENT, self.OnListingEvent)
                self.list_ctrl.set_updating(True)
                self.worker = listers.AvailableListerThread(parent=self, uid=self.list_ctrl.GetId(), imagedir=imagedir, max_recent=self._get_maximum_recent_items(), pre_mark=pre_mark_list)
            elif view == views.INSTALLED:
                self.search_ctrl.SetToolTipString(_("Search in installed components"))
                self._init_list_ctrl(views.INSTALLED, [
                    # Label, width, format
                    ("", 30, wx.LIST_FORMAT_CENTER),
                    (_("Component"), 220, wx.LIST_FORMAT_LEFT),
                    (_("Category"), 145, wx.LIST_FORMAT_LEFT),
                    (_("Version"), 95, wx.LIST_FORMAT_LEFT),
                    (_("Installed Size"), 115, wx.LIST_FORMAT_RIGHT),
                    (_("Source"), wx.LIST_AUTOSIZE, wx.LIST_FORMAT_LEFT)
                ], size_col=4, sort_col=2)
                self.Bind(listers.EVT_LISTING_COMPONENT, self.OnListingEvent)
                self.list_ctrl.set_updating(True)
                self.worker = listers.InstalledListerThread(parent=self, uid=self.list_ctrl.GetId(), imagedir=imagedir, max_recent=self._get_maximum_recent_items())
            elif view == views.UPDATES:
                self.search_ctrl.SetToolTipString(_("Search in available updates"))
                self._init_list_ctrl(views.UPDATES, [
                    # Label, width, format
                    ("", 30, wx.LIST_FORMAT_CENTER),
                    (_("Component"), 180, wx.LIST_FORMAT_LEFT),
                    ("!", 20, wx.LIST_FORMAT_CENTER),
                    (_("Published"), 100, wx.LIST_FORMAT_CENTER),
                    (_("New Version"), 100, wx.LIST_FORMAT_LEFT),
                    (_("Installed Version"), 125, wx.LIST_FORMAT_LEFT),
                    (_("Download"), 80, wx.LIST_FORMAT_RIGHT),
                    (_("Source"), wx.LIST_AUTOSIZE, wx.LIST_FORMAT_LEFT)
                ], size_col=6, sort_col=2)

                security_attr, security_keywords = ips.get_security_defs(self.config)

                self.Bind(listers.EVT_LISTING_COMPONENT, self.OnListingEvent)
                self.list_ctrl.set_updating(True)
                self.worker = listers.UpdatesListerThread(parent=self, uid=self.list_ctrl.GetId(), imagedir=imagedir, max_recent=self._get_maximum_recent_items(),
                        auto_mark=not self.view_recent, show_old_updates=self._show_old_updates, security_attr=security_attr, security_keywords=security_keywords)
            else:
                utils.logger.debug("Invalid view!")
                self.throbber.Rest()
                raise Exception("Invalid view!")


    def OnRefresh(self, dummy_event):
        """
        Since available add-ons and updates view do a remote refresh on
        entering anyway, we just delegate to that code and do not perform a
        refresh ourselves.
        """
        imagedir = self.imgs_tree.get_image_view()[0]
        if not imagedir:
            wx.MessageBox(_("Please select an image to refresh first."), style=wx.OK|wx.ICON_EXCLAMATION|wx.CENTER,
                          caption=_("Tip"), parent=self)
            return

        (img, reason) = ips.load_image(imagedir, opname="list")
        if img is None:
            wx.MessageBox(_("Image could not be loaded.\n\n%s") % reason, style=wx.OK|wx.ICON_EXCLAMATION|wx.CENTER,
                          caption=_("Tip"), parent=self)
            return

        # Now update the display (wx.CallAfter in case any more code gets introduced below)
        self.update_image_view()


    def OnSearch(self, dummy_event):
        self.search_ctrl.SetFocus()


    def OnInstall(self, dummy_event):
        imagedir, view = self.imgs_tree.get_image_view()[0:2]
        if not view:
            wx.MessageBox(_("Please select some components first."), style=wx.OK|wx.ICON_EXCLAMATION|wx.CENTER,
                          caption=_("Tip"), parent=self)
            return

        if view not in [views.AVAILABLE,  views.UPDATES]:
            utils.logger.error("Install event generated outside available/updates view")
            wx.MessageBox(_("An unexpected error occurred. Application will now close to prevent data corruption."),
                    style=wx.OK|wx.ICON_INFORMATION|wx.CENTER, caption=_("Internal error"), parent=self)
            self.Destroy()
            return # We'll be dead

        # Issue 1504: The tree still has the focus and will cause a tree selection event
        # when the license dialog, launched from the button handler is dismissed. And that
        # causes a list refresh while install happens, So make sure to give the focus to
        # the list.
        self.list_ctrl.SetFocus()
        self._install_components(imagedir)


    def OnRemove(self, dummy_event):
        imagedir, view = self.imgs_tree.get_image_view()[0:2]
        if not view:
            wx.MessageBox(_("Please select some components first."), style=wx.OK|wx.ICON_EXCLAMATION|wx.CENTER,
                          caption=_("Tip"), parent=self)
            return

        if view != views.INSTALLED:
            utils.logger.error("Remove event generated outside installed components view")
            wx.MessageBox(_("An unexpected error occurred. Application will now close to prevent data corruption."),
                    style=wx.OK|wx.ICON_INFORMATION|wx.CENTER, caption=_("Internal error"), parent=self)
            self.Destroy()
            return
        # Issue 1504: The tree still has the focus and will cause a tree selection event
        # when the license dialog, launched from the button handler is dismissed. And that
        # causes a list refresh while install happens, So make sure to give the focus to
        # the list.
        self.list_ctrl.SetFocus()
        self._remove_components(imagedir)


    def OnNewImage(self, dummy_event):
        dlg = ImageCreateEditDialog(self, opname='image-create')
        if self.u_cached_last_dir and os.path.isdir(fsenc(self.u_cached_last_dir)):
            dlg.set_path(self.u_cached_last_dir)

        u_chosen_dir, success = self.create_new_image(dlg)
        if success:
            self.imgs_tree.select_image_node(u_chosen_dir, views.AVAILABLE)
        else:
            self.imgs_tree.select_image_node(u_chosen_dir)


    def create_new_image(self, dlg):
        """
        Create a new image. Returns a tuple containing:
        a unicode object of the actually added path and True in case of success
        or
        path supplied by the user and False in case of failure.
        """

        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it.
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            # User did not select an image directory
            return (None, False)

        chosen_dir = dlg.get_directory()
        pubs = dlg.get_pubs()
        img_title = dlg.get_image_title()
        img_desc = dlg.get_image_description()

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()

        return self._create_new_image(chosen_dir, pubs, img_title, img_desc)


    def _encode_pubs(self, pubs):
        '''
        Make sure various pubs files are properly encoded
        1) name is fs encoded
        2) key and cert paths need to be string (Issue 180 and 1823)

        TODO: This needs to be moved to ips.set_publishers
        '''
        for p in pubs:
            p[0] = fsenc(p[0])
            if isinstance(p[3], unicode):
                # Actually we just need a str object but this excepts less
                p[3] = p[3].encode(FSENC)
            if isinstance(p[4], unicode):
                # Actually we just need a str object but this excepts less
                p[4] = p[4].encode(FSENC)


    def _create_new_image(self, chosen_dir, pubs, img_title, img_desc):

        self.u_cached_last_dir = chosen_dir

        self._encode_pubs(pubs)

        preferred_pub_name, preferred_pub_url, preferred_ssl_key_path, preferred_ssl_cert_path = \
            [(n, u, k, c) for n, u, p, k, c, d in pubs if p][0]

        chosen_dir = os.path.expanduser(chosen_dir)

        try:
            self.set_status(_("Creating image..."))
            ips.create_image(fsenc(chosen_dir), img_title, preferred_pub_name, preferred_pub_url,
                    ssl_key=preferred_ssl_key_path, ssl_cert=preferred_ssl_cert_path, opname="image-create")
            self.set_status("")
        except OSError, e:
            self.set_status("")
            msg = _("Can not create image.\n\nReason: %s") % e.args[1]
            wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER,  caption=_("Error"), parent=self)
            return (chosen_dir, False)
        except RuntimeError, failures:
            self.set_status("")
            (remote, error_strs) = ips.extract_catalog_retrieval_errors(failures)

            if error_strs:
                emsg = u"\n\n".join(safe_decode(x) for x in error_strs)
                if remote:
                    msg = _("Could not create image. Please make sure that the remote publisher is "\
                        "accessible.\n\n%s") % emsg
                else:
                    msg = _("Could not create image.\n\n%s") % emsg
                wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER,  caption=_("Error"), parent=self)
            else:
                msgbox(short_msg=_("Image creation failed.\n" \
                        "Please report the following error text to %(REPORT_TO)s.") % {
                            'REPORT_TO':INFO.REPORT_TO},
                        long_msg=utils.format_trace(), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                        caption=_("Error"), parent=self)

            return (chosen_dir, False)
        except httplib.HTTPException, msg:
            wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER,  caption=_("Error"), parent=self)
            return (chosen_dir, False)
        except InvalidDepotResponseException, e: # ApiException
            # NOTE: At this point a directory exists but is not a valid image and
            # trying to just open it fails. So we claim that it was not created (successfully).
            utils.logger.debug(str(e))
            self.set_status("")
            msg = _("Can not create image.\n\nReason: %s") % str(e)
            wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER,  caption=_("Error"), parent=self)
            return (chosen_dir, False)
        except CatalogRefreshException:
            self.set_status("")
            ips.set_image_title(fsenc(chosen_dir), img_title, opname='image-create')
            msg = _("The application image has been created.\nHowever, an error " \
            "occurred while downloading the catalog for the image.\n\n" \
            "Use Edit Properties to correct the publisher access information.")
            wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER,  caption=_("Error"), parent=self)
        except:
            self.set_status("")
            msgbox(short_msg=_("Image creation failed.\n"
                "Please report the following error text to %(REPORT_TO)s.") % {
                    'REPORT_TO':INFO.REPORT_TO},
                long_msg=utils.format_trace(), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                caption=_("Error"), parent=self)
            return (chosen_dir, False)

        self.set_status(_("Setting image description..."))
        ips.set_image_description(fsenc(chosen_dir), img_desc, opname='image-create')
        self.set_status(_("Adding publishers..."))
        ret, res = ips.set_publishers(fsenc(chosen_dir), pubs, opname='image-create')

        if not ret:
            msg = _("Could not assign all publishers to the image.\n\n%s") % res
            wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER,  caption=_("Warning"), parent=self)

        self.set_status("Loading image...")
        u_chosen_dir, success = self.add_image(chosen_dir, quiet=False, opname='image-create')
        self.save_images_list()

        return (u_chosen_dir, success)


    def _set_premark_list(self, imagedir, pre_mark_list):
        # Specify packages to pre-select in image. The lister will
        # Pick this up
        if pre_mark_list is not None:
            c_path = os.path.normcase(os.path.realpath(imagedir))
            self._pre_mark_table[c_path] = pre_mark_list


    def OnEditImage(self, dummy_event):
        if hasattr(self, 'context_menu_imagedir'):
            imagedir, view = self.context_menu_imagedir, None
        else:
            imagedir, view = self.imgs_tree.get_image_view()[0:2]
        if not imagedir:
            wx.MessageBox(_("Please select an image to edit first."), style=wx.OK|wx.ICON_EXCLAMATION|wx.CENTER,
                    caption=_("Tip"), parent=self)
            return

        lockmanager.lock()
        if lockmanager.get_image_state(imagedir)[1] is not None:
            lockmanager.release()
            wx.MessageBox(_("This image is currently busy. Please try this operation later."), style=wx.OK|wx.ICON_EXCLAMATION|wx.CENTER,
                    caption=_("Tip"), parent=self)
            return
        lockmanager.release()

        dlg = ImageCreateEditDialog(self, image=imagedir, opname='image-edit')
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        img_title = dlg.get_image_title()
        img_desc = dlg.get_image_description()
        pubs = dlg.get_pubs()
        dlg.Destroy()
        if not pubs:
            wx.MessageBox(_("You must specify at least one publisher."),
                    style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
            return

        preferred_publisher = [(x, y) for x, y, z, dummy_k, dummy_c, dummy_a in pubs if z]
        if not preferred_publisher:
            wx.MessageBox(_("You must specify at least one publisher."),
                    style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
            return

        if len(preferred_publisher) > 1: # Should never happen usually
            wx.MessageBox(_("You must specify only one preferred publisher."),
                    style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
            return

        self.set_status("")
        ips.set_image_title(fsenc(imagedir), img_title, opname='edit-image')
        ips.set_image_description(fsenc(imagedir), img_desc, opname='edit-image')
        try:
            self._encode_pubs(pubs)
            res, reason = ips.set_publishers(fsenc(imagedir), pubs, opname='edit-image')
            if not res:
                msg = _("Could not correctly apply the new publishers list to the image.\n\n%s") % reason
                wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER,  caption=_("Error"), parent=self)
        except UpdateToolException, e:
            msg = _("Could not correctly apply the new publishers list to the image.\n\n%s") % e
            utils.logger.error(msg)
            wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER,  caption=_("Error"), parent=self)
        except:
            utils.logger.error(utils.format_trace())
            msg = _("Could not correctly apply the new publishers list to the image.\n\n%s") % utils.format_trace()
            utils.logger.error(msg)
            wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER,  caption=_("Error"), parent=self)
        self.imgs_tree.refresh_image_node(imagedir, view, opname='image-edit')
        self.update_image_view()


    def OnCloseImage(self, dummy_event):
        if hasattr(self, 'context_menu_imagedir'):
            imagedir = self.context_menu_imagedir
        else:
            imagedir = self.imgs_tree.get_image_view()[0]
        if not imagedir:
            wx.MessageBox(_("Please select an image to close first."), style=wx.OK|wx.ICON_EXCLAMATION|wx.CENTER,
                    caption=_("Tip"), parent=self)
            return
        self._close_image(imagedir)


    def _close_image(self, imagedir):
        if self.imgs_tree.remove_image_node(imagedir):
            self.u_cached_last_dir = imagedir
            self.config.remove_option("main", "_last_active_image")
            self.set_status("", 1)
            self.right_splitter.UpdateSize()
            self.right_panel.Layout()
            self.save_images_list()
            # When an image is closed ask the notifier to reload its prefs
            # and check for updates without notification.  This will cause
            # the notifier icon to be removed from the taskbar if this was
            # the last image to have pending updates.  Issue 596
            ipcservice.send_command("nt_lock", "LOAD_CONFIG")
            ipcservice.send_command("nt_lock", "CHECK_UPDATES")
        if len(self.imgs_tree.installed_images) < 1:
            self.set_list_msg(_("Please create or open a new image"))
            self.pkg_details_panel.describe_view(None, None)


    def OnPrefAction(self, event):
        """Process Apply and Ok PreferenceDialog events"""

        # Process proxy settings
        utils.set_net_proxy(self.config)

        # When the user applies the prefs inform the notifier (if it is
        # running) to reload its config.  We don't care if it was successful
        # as the notifier may not be running.
        ipcservice.send_command("nt_lock", "LOAD_CONFIG")

        event.Skip()


    def OnPreferences(self, dummy_event):
        dlg = PreferencesDialog(self, -1, _("%(APP_NAME)s: Preferences") % {'APP_NAME':INFO.APP_NAME})

        dlg.set_prefs_action_handler(self.OnPrefAction)

        # We need to provide the Prefs Dialog an image path.  It is
        # the image that the notifier is reg/unreg to.
        image_path = ips.get_python_image_path()
        if image_path == "":
            image_path = self.imgs_tree.get_image_view()[0]

        # Before we display the dialog check that we have the current
        # defaults.cfg loaded (issue 1053)
        self.reload_config()

        # Update the Preferences GUI with the current config and image.
        dlg.set_config(self.config, image_path)

        dummy = dlg.ShowModal()
        dlg.Destroy()


    def OnMarkAll(self, dummy_event):
        wx.BeginBusyCursor()
        view = self.imgs_tree.get_image_view()[1]
        if not view or not isinstance(self.list_ctrl, wx.ListCtrl):
            wx.EndBusyCursor()
            return

        item_count = self.list_ctrl.GetItemCount()
        for i in xrange(item_count):
            if not self.list_ctrl.IsChecked(i):
                self.list_ctrl.old_OnCheckItem(i, True)
        if self.list_ctrl.view == views.INSTALLED:
            self._enable_remove(item_count > 0)
        elif self.list_ctrl.view in [views.AVAILABLE, views.UPDATES]:
            self._enable_install(item_count > 0)
        else:
            # This should not happen
            utils.logger.error("OnMarkAll called in unknown view")
            wx.MessageBox(_("An unexpected error occurred. Application will now close to prevent data corruption."),
                    style=wx.OK|wx.ICON_INFORMATION|wx.CENTER, caption=_("Internal error"), parent=self)
        self._enable_mark_all(False)
        self._enable_unmark_all(item_count > 0)
        wx.EndBusyCursor()
        self.update_top_status()


    def OnUnmarkAll(self, dummy_event):
        wx.BeginBusyCursor()
        view = self.imgs_tree.get_image_view()[1]
        if not view or not isinstance(self.list_ctrl, wx.ListCtrl):
            wx.EndBusyCursor()
            return

        item_count = self.list_ctrl.GetItemCount()
        for i in xrange(item_count):
            if self.list_ctrl.IsChecked(i):
                self.list_ctrl.old_OnCheckItem(i, False)
        if self.list_ctrl.view == views.INSTALLED:
            self._enable_remove(False)
        elif self.list_ctrl.view in [views.AVAILABLE, views.UPDATES]:
            self._enable_install(False)
        else:
            # This should not happen
            utils.logger.error("OnUnmarkAll called in unknown view")
            wx.MessageBox(_("An unexpected error occurred. Application will now close to prevent data corruption."),
                    style=wx.OK|wx.ICON_INFORMATION|wx.CENTER, caption=_("Internal error"), parent=self)
        self._enable_mark_all(item_count > 0)
        self._enable_unmark_all(False)
        wx.EndBusyCursor()
        self.update_top_status()


    def OnHelp(self, dummy_event):
        if not self.help:
            filename = "help.hhp"
            helppath = os.path.join(os.path.dirname(__file__), "..", "help", 'C', filename)

            loc = UPDATETOOL_LOCALE
            if loc is not None:
                if len(loc) >= 5 and loc.upper()[:5] == 'ZH_TW':
                    helppath = os.path.join(os.path.dirname(__file__), "..", "help", 'zh_TW', filename)
                elif len(loc) >= 2 and loc.upper()[:2] in ['ZH']:
                    helppath = os.path.join(os.path.dirname(__file__), "..", "help", 'zh_CN', filename)
                elif len(loc) >= 5 and loc.upper()[:5] == 'PT_BR':
                    # XXX: Only use these translations for Brazillian Portguese and no other portguese?
                    helppath = os.path.join(os.path.dirname(__file__), "..", "help", 'pt_BR', filename)
                elif len(loc) >= 2 and loc.upper()[:2] in ['DE', 'ES', 'FR', 'JA', 'KO']:
                    helppath = os.path.join(os.path.dirname(__file__), "..", "help", loc[:2].lower(), filename)

            temp_controller = HtmlHelpController(parentWindow=self)
            if not temp_controller.AddBook(helppath):
                return

            self.help = temp_controller

        self.help.DisplayContents()
        self.help.FindTopLevelWindow().Centre(wx.BOTH)


    def raise_frame(self):
        self.Raise()
        self.Restore()


    def restart_if_needed(self):
        """
        This method is triggered when the GUI needs to check if the
        files it depends on have been updated.
        """

        current_version = utils.get_version()

        if utils.get_version() == self.version:
            utils.logger.debug("restart_if_needed: restart not require")
            return

        msg = _("Important updates to the %(APP_NAME)s have been applied. " \
                "The %(APP_NAME)s should be restarted immediately to ensure " \
                "proper operation.\n\nWould you like to restart the " \
                "%(APP_NAME)s?") % {'APP_NAME':INFO.APP_NAME}

        if wx.YES == wx.MessageBox(msg,
                                   caption=_("Restart %(APP_NAME)s") % {'APP_NAME':INFO.APP_NAME},
                                   style=wx.YES|wx.NO|wx.ICON_WARNING|wx.CENTER, parent=self):
            # A return code of 88 indicates a restart is needed.
            os._exit(88)


    def notifier_apply_updates(self):
        """
        This method is triggered by the notifier when the user chooses to
        apply updates.
        """
        self.notifier_updates()


    def notifier_updates(self):
        op = 'notifier'
        self.right_panel.Layout()
        imagedir = self.imgs_tree.get_image_view()[0]
        new_updates = []

        security_attr, security_keywords = ips.get_security_defs(self.config)

        # Construct a list of images that have pending updates.
        for imagedir in self.imgs_tree.installed_images:
            try:
                component_list, security_updates = ips.enumerate_pkgs(fsenc(imagedir), check_type="updates", security_attr=security_attr, security_keywords=security_keywords, client=INFO.CLIENT_NAME, opname=op)

                # If there is a list of components that need to be
                # updated then store the image name and the list
                # of components.
                if component_list:
                    new_updates.append([imagedir, component_list])

                # If there is more than one image with pending
                # updates we don't need to continue to walk through
                # the list of images looking for more updates.
                # Later we will figure out which image to open.
                if len(new_updates) > 1:
                    break

            except (RuntimeError, httplib.HTTPException, ApiException):
                # Igore those images where we can't access the repo.
                pass

        # If there is only one image that has pending updates then
        # present a dialog requesting confirmations to installed the
        # updates.
        if len(new_updates) == 1:

            # If the current view is the Update view for the correct image
            # the check boxes may not be selected so by calling
            # update_image_view() in this case we ensure the check boxes
            # for the components to be updated are selected.
            selected_imagedir, selected_view = self.imgs_tree.get_image_view()[0:2]
            if selected_imagedir == new_updates[0][0] and \
               selected_view == views.UPDATES:
                self.update_image_view()

            self.imgs_tree.select_image_node(new_updates[0][0],
                                             views.UPDATES)

            # On OS X calling notifier_apply_dialog directly results in the
            # component view not being properly updated.  The short delay
            # introduced below works around this issue.
            wx.FutureCall(250, self.notifier_apply_dialog,
                                                 imgroot=new_updates[0][0],
                                                 security=security_updates)
            return

        # If there is more than one image that has pending updates then
        # we just choose either the current image or another image that
        # has updates.  We do not display a dialog.
        elif len(new_updates) > 1:
            # Check to see if the current selected image has any updates.
            # If it does we highlight those updates.
            imagedir = self.imgs_tree.get_image_view()[0]
            if imagedir and ips.has_updates(imagedir, opname=op):
                self.imgs_tree.select_image_node(imagedir, views.UPDATES)
            else:
                for imagedir in self.imgs_tree.installed_images:
                    if ips.has_updates(imagedir, opname=op):
                        self.imgs_tree.select_image_node(imagedir, views.UPDATES)
                        break

        # No images have pending updates.
        elif len(new_updates) == 0:
            msg = _("No application images currently have pending updates.")
            wx.MessageBox(msg, style=wx.OK|wx.ICON_INFORMATION|wx.CENTER,
                    caption=_("No updates available"), parent=self)


    def notifier_apply_dialog(self, *dummy_args, **kwargs):

        imagedir = kwargs['imgroot']
        security_updates = kwargs['security']

        if security_updates:
            security_str = _(" security")
        else:
            security_str = ""

        if self.list_ctrl.checked_count < 1:
            return

        if self.list_ctrl.checked_count == 1:
            msg = _("An update is available for the following \napplication:\n\n")
            msg = "".join([msg, _("   %(app_name)s:\n         1%(security_id)s update available\n\n") % {
                'app_name' : ips.get_image_title(imagedir, opname='notifier'), 'security_id' : security_str}])
            msg = "".join([msg, _("Press OK to install this update.")])
        else:
            msg = _("Updates are available for the following \napplications:\n\n")
            msg = "".join([msg, _("   %(app_name)s:\n         %(count)d%(security_id)s updates available\n\n") % {
                'app_name' : ips.get_image_title(imagedir, opname='notifier'), 'count' : self.list_ctrl.checked_count, 'security_id' : security_str}])
            msg = "".join([msg, _("Press OK to install these updates.")])

        if wx.OK == wx.MessageBox(msg, style=wx.OK|wx.CANCEL|wx.ICON_QUESTION|wx.CENTER, caption=_("Updates are available"),
                parent=self):
            self._install_components(imagedir)


    def reload_config(self):
        """
        If the pref's are updated via the notifier prefs dialog the GUI is
        sent a LOAD_CONFIG IPC message.  This method is called to respond
        to the reload request.
        """
        if self.config:
            self.config.load_config()
            utils.set_net_proxy(self.config)


    def _remove_components(self, imagedir):
        wx.BeginBusyCursor()
        _enabled = self.toolbar.FindById(MainFrame.APP_ID_REMOVE).IsEnabled()
        self._enable_remove(False)
        self.set_status(_("Checking selections..."))

        item_count = self.list_ctrl.GetItemCount()
        to_remove = [self.list_ctrl.get_fmri(i) \
                for i in xrange(item_count) if self.list_ctrl.IsChecked(i)]

        self.set_status("")
        if not to_remove:
            wx.EndBusyCursor()
            self.set_status("")
            wx.MessageBox(_("No components are selected for removal."), style=wx.OK|wx.ICON_EXCLAMATION|wx.CENTER,
                    caption=_("Tip"), parent=self)
            self._enable_remove(_enabled)
            return
        self.set_status(_("Confirming image..."))
        img = pkgimage.Image()
        img.history.client_name = 'updatetool'
        img.history.operation_name = 'uninstall'
        try:
            img.find_root(fsenc(imagedir))
            if img.type != pkgimage.IMG_USER:
                raise AssertionError("Not a user image")
            self.set_status("")
        except (AssertionError, ImageNotFoundException):
            wx.EndBusyCursor()
            self.set_status("")
            msgbox(short_msg=_("'%(directory)s' is not a user install image.\n" \
                    "Please report the following error text to %(email)s.") % {
                        'directory':imagedir, 'email':INFO.REPORT_TO},
                    long_msg=utils.format_trace(), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                    caption=_("Error"), parent=self)

            self._enable_remove(_enabled)
            return

        self.set_status(_("Loading image configuration..."))
        img.load_config()
        self.set_status(_("Loading components catalog..."))
        img.load_catalogs(QuietProgressTracker())
        self.set_status("")
        tracker_task = ImagePlanTask()

        recursive_removal = True
        iplan = pkgimageplan.ImagePlan(img, tracker_task, recursive_removal, lambda: False)
        tracker_task.set_image_plan(iplan)

        self.set_status(_("Creating removal plan"))
        for rpat in to_remove:
            try:
                pat_without_auth = rpat.get_fmri(anarchy=True)
                matches = list(img.inventory([ pat_without_auth ], False))
            except (RuntimeError, httplib.HTTPException, InventoryException), ex:
                # No matching package could be found for the following FMRIs in
                # any of the catalogs for the current authorities:
                # pkg://updates/javadb@10.2.2,0-0.7:20080425T022159Z
                wx.EndBusyCursor()
                self.set_status("")
                wx.MessageBox(_("The component\n\n%s\n\nis not in any of the catalogs for the current authorities.\n\nPlease try refreshing the list.") % rpat,
                        style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
                # Now update the display
                wx.CallAfter(self.update_image_view)
                return

            if len(matches) > 1:
                wx.EndBusyCursor()
                self.set_status("")
                msg = _("Unexpected error. '%s' matches multiple packages.") % rpat
                wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
                # Now update the display
                wx.CallAfter(self.update_image_view)
                return

            if len(matches) < 1:
                wx.EndBusyCursor()
                self.set_status("")
                wx.MessageBox(_("'%s' matches no installed packages.\nPlease try refreshing the list.") % rpat,
                        style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
                # Now update the display
                wx.CallAfter(self.update_image_view)
                return

            iplan.propose_fmri_removal(matches[0][0])

        try:
            self.set_status(_("Evaluating removal plan"))
            iplan.evaluate()
        except ConstraintException, ce:
            wx.EndBusyCursor()
            self.set_status("")
            msg = str(ce)
            msg += "\n\n"
            msg += _("Removal can not proceed.")
            self.set_status("")
            wx.MessageBox(msg, caption=_("Error"), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                    parent=self)
            wx.CallAfter(self.update_image_view)
            return
        except KeyError, msg:
            wx.EndBusyCursor()
            self.set_status("")
            # TODO : Improve the error message
            wx.MessageBox(msg, caption=_("Error"), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                    parent=self)
            wx.CallAfter(self.update_image_view)
            return

        self.set_status(_("Performing safety checks..."))
        img.imageplan = iplan

        if iplan.nothingtodo():
            wx.EndBusyCursor()
            self.set_status("")
            wx.MessageBox(_("Nothing to do."), caption=_("Component removal"),
                    style=wx.OK|wx.ICON_INFORMATION|wx.CENTER, parent=self)
            self.OnUnmarkAll(None)
            return

        short_name_set = []
        final_fmri_set = []
        affected = []
        for pplan in iplan.pkg_plans:
            if pplan.origin_fmri and not pplan.destination_fmri:
                short_name_set.append("%s (%s)" % (
                    pplan.origin_fmri.get_name(), pplan.origin_fmri.version.get_short_version()))
                final_fmri_set.append(pplan.origin_fmri)

            try:
                affected.extend(ips.check_if_safe(affected_image_root=img.get_root(), affected_pkg_fmris=final_fmri_set, opname='uninstall', yield_func=wx.YieldIfNeeded))
            except:
                wx.EndBusyCursor()
                self.set_status("")
                msgbox(short_msg=_("Error encountered during component removal.\n\n" \
                        "Safety checks failed.\n\nPlease report the following error text to %(REPORT_TO)s.") % {
                            'REPORT_TO':INFO.REPORT_TO},
                        long_msg=utils.format_trace(), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                        caption=_("Error"), parent=self)
                self.OnUnmarkAll(None)
                return

        self.set_status("")

        if affected:
            affected = sorted(set(affected))
            wx.EndBusyCursor()
            self.set_status("")
            msg = _("This causes the removal of the following components which are necessary to support the %(app_name)s.\n\n%(component_names)s\n\nRemoval of " \
                    "these components will cause the %(app_name)s to no longer operate properly.\n\n" \
                    "Would you like to remove these critical components?") % {
                            'app_name':INFO.APP_NAME, 'component_names': "\n".join([afmri.get_name() for afmri in affected])}
            if wx.YES != wx.MessageBox(msg, caption=_("Remove critical components?"),
                    style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_WARNING|wx.CENTER, parent=self):
                self.OnUnmarkAll(None)
                return
            else:
                wx.BeginBusyCursor()

        wx.EndBusyCursor()
        short_name_set = sorted(set(short_name_set))
        if len(short_name_set) != len(to_remove):
            preop_dlg = PreOpConfirmationDialog(self, -1, confirm_type=PreOpConfirmationDialog.REMOVE,
                    items=short_name_set, pkg_count=len(to_remove),
                    extra_pkg_count= len(short_name_set) - len(to_remove))

            # preop_dlg.set_pre_op_size(123456)

            if preop_dlg.ShowModal() != wx.ID_OK:
                self.set_status("")
                preop_dlg.Destroy()
                self.OnUnmarkAll(None)
                return

            preop_dlg.Destroy()
        else:
            preop_dlg = PreOpConfirmationDialog(self, -1, confirm_type=PreOpConfirmationDialog.REMOVE,
                    items=short_name_set, pkg_count=len(to_remove), extra_pkg_count=0)

            # preop_dlg.set_pre_op_size(123456)

            if preop_dlg.ShowModal() != wx.ID_OK:
                self.set_status("")
                preop_dlg.Destroy()
                self.OnUnmarkAll(None)
                return

            preop_dlg.Destroy()

        try:
            wx.BeginBusyCursor()
            pdlg = AppProgressTrackerDialog(self, -1, "", task=tracker_task)
            tracker_task.set_progress_dialog(pdlg)

            # Run pre-remove scripts on packages
            self.run_configurators(iplan, remove=True, task=tracker_task, pdlg=pdlg, opname='uninstall')
            tracker_task.start()
            pdlg.ShowModal()
            ret = tracker_task.get_result()

            if ret[0] == TASK_END_USER_ABORT:
                wx.EndBusyCursor()
                wx.MessageBox(_("Removal cancelled."), style=wx.OK|wx.ICON_INFORMATION|wx.CENTER, caption=_("User abort"), parent=self)
                # Now update the display (wx.CallAfter in case any more code gets introduced below)
                wx.CallAfter(self.update_image_view)
                return
            elif ret[0] == TASK_END_EXCEPTION:
                raise ret[1][0], ret[1][1], ret[1][2]
            elif ret[0] != TASK_END_SUCCESS:
                raise UpdateToolException(_("ThreadedTask did not communicate the result properly."))
            else:
                # Run configurators after packages are installed.
                # self.run_configurators(iplan, remove=False)
                tracker_task.task_finished()
            wx.EndBusyCursor()

            # When pkgs are removed from an image ask the notifier to reload
            # its prefs and check for updates without notification.  This
            # will cause the notifier icon to be removed from the taskbar
            # if this was the last image to have pending updates.  Issue 596
            ipcservice.send_command("nt_lock", "LOAD_CONFIG")
            ipcservice.send_command("nt_lock", "CHECK_UPDATES")

        except Exception, e:
            val = sys.exc_info()[1]
            wx.EndBusyCursor()
            self.set_status("")
            try:
                if tracker_task is not None and tracker_task.is_running():
                    tracker_task.task_finished()
            except:
                pass
            if isinstance(val, PermissionsException): # rely on pkg(5) to give us the right msg
                wx.MessageBox(str(val), style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
            else:
                msgbox(short_msg=_("Error encountered during component removal.\n" \
                        "Please report the following error text to %(REPORT_TO)s.") % {
                            'REPORT_TO':INFO.REPORT_TO},
                        long_msg=utils.format_trace(), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                        caption=_("Error"), parent=self)
        self.update_image_view()


    def _install_components(self, imagedir, to_install=None):
        """
        Returns:
        0 on success
        >0 on error
        <0 if user cancelled install
        TODO : Merge both kinds of tasks to use ImageInterface api
        """
        wx.BeginBusyCursor()
        _enabled = self.toolbar.FindById(MainFrame.APP_ID_INSTALL).IsEnabled()
        self._enable_install(False)
        item_count = 0
        if not to_install:
            item_count = self.list_ctrl.GetItemCount()
            self.set_status(_("Checking selections..."))
            if item_count >= 1:
                to_install = [self.list_ctrl.get_fmri(i) \
                    for i in xrange(item_count) if self.list_ctrl.IsChecked(i)]

        self.set_status("")
        if not to_install:
            wx.EndBusyCursor()
            self.set_status("")
            wx.MessageBox(_("Nothing to do."), caption=_("Information"), style=wx.OK|wx.ICON_INFORMATION|wx.CENTER,
                    parent=self)
            self._enable_install(_enabled)
            self.update_image_view()
            return 0

        if isinstance(self.list_ctrl, wx.ListCtrl) and \
           self.list_ctrl.view == views.UPDATES and \
           not self.list_ctrl.filtered and \
           not self.view_recent and \
           item_count == len(to_install):

            # HACK : We can do an image update here to work around Issue 1020 with incorporations
            wx.EndBusyCursor()
            self.set_status("")
            rcode = self.__image_update(imagedir, self.list_ctrl.imageplan)
        else:
            wx.EndBusyCursor()
            self.set_status("")
            rcode = self.__image_install(imagedir, to_install)
        self._enable_install(_enabled)
        self.update_image_view()
        return rcode


    def __image_install(self, imagedir, to_install=None):
        """
        NOTE: Do not call this method directly. Call _install_components instead.
        """
        assert to_install is not None and type(to_install) == type([]) and len(to_install)

        self.set_status(_("Confirming image..."))
        img = pkgimage.Image()
        img.history.client_name = 'updatetool'
        img.history.operation_name = 'install'

        wx.BeginBusyCursor()
        try:
            img.find_root(fsenc(imagedir))
            if img.type != pkgimage.IMG_USER:
                raise AssertionError("Not a user image")
            self.set_status("")
        except (AssertionError, ImageNotFoundException):
            wx.EndBusyCursor()
            self.set_status("")
            msg = _("Install can not proceed.\n\n'%s'\n\nis not a valid user install image.") % imagedir
            wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
            return 1
        self.set_status(_("Loading image configuration"))
        img.load_config()
        self.set_status(_("Loading components catalog..."))
        img.load_catalogs(QuietProgressTracker())
        self.set_status("")
        tracker_task = ImagePlanTask()

        try:
            self.set_status(_("Creating install plan..."))
            pkg_list = [str(f) for f in to_install]
            img.make_install_plan(pkg_list, tracker_task, lambda: False, False)
            self.set_status("")
        except (ConstraintException, PlanCreationException), ce:
            wx.EndBusyCursor()
            # TODO : Beautify by supplying own __str__ method
            msg = str(ce)
            msg += "\n\n"
            msg += _("Install can not proceed.")
            self.set_status("")
            caption = _("Installation Error")
            if isinstance(ce, ConstraintException):
                caption = _("Installation Constraints Error")
            wx.MessageBox(msg, caption=caption, style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                                parent=self)
            self.set_status(_("Performing cleanup..."))
            img.cleanup_downloads()
            self.set_status("")
            return 1
        except InventoryException, ie:
            wx.EndBusyCursor()
            # TODO : Beautify by supplying own __str__ method
            msg = str(ie)
            msg += "\n\n"
            msg += _("Install can not proceed.")
            self.set_status("")
            wx.MessageBox(msg, caption=_("Publisher Inventory Error"), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                                parent=self)
            self.set_status(_("Performing cleanup..."))
            img.cleanup_downloads()
            self.set_status("")
            return 1
        except (RuntimeError, httplib.HTTPException), msg:
            wx.EndBusyCursor()
            self.set_status("")
            if str(msg).find("No packages were installed because package dependencies could not be satisfied"):
                _msg = _("Error detected on the components publisher's end.\n" \
                        "Please report the following error text to the component publisher or "\
                        "the maintainers as appropriate.")
            else:
                _msg = str(msg)
            msgbox(short_msg=_msg, long_msg=utils.format_trace(), caption=_("Error"), parent=self)
            self.set_status(_("Performing cleanup..."))
            img.cleanup_downloads()
            self.set_status("")
            return 1

        except KeyError, msg:
            wx.EndBusyCursor()
            self.set_status("")
            # TODO : Improve the error message
            if wx.OK != wx.MessageBox(msg, caption=_("Error"), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                    parent=self):
                self.set_status(_("Performing cleanup..."))
                img.cleanup_downloads()
                self.set_status("")
                return 1
        except:
            wx.EndBusyCursor()
            self.set_status("")
            msgbox(short_msg=_("An unexpected error occurred.\n" \
                    "Please report the following error text to %(REPORT_TO)s.") % {
                        'REPORT_TO':INFO.REPORT_TO},
                    long_msg=utils.format_trace(), caption=_("Error"), parent=self)
            self.set_status(_("Performing cleanup..."))
            img.cleanup_downloads()
            self.set_status("")
            return 1

        self.set_status(_("Performing safety checks..."))

        iplan = img.imageplan
        tracker_task.set_image_plan(iplan)
        fmri_set = sorted(set(iplan.target_fmris))
        pkg_plans = iplan.pkg_plans

        if not fmri_set:   # maybe the component is installed from some other publisher
            self.set_status("")
            wx.EndBusyCursor()
            wx.MessageBox(_("Nothing to do."), caption=_("Information"), style=wx.OK|wx.ICON_INFORMATION|wx.CENTER,
                    parent=self)
            self.set_status(_("Performing cleanup..."))
            img.cleanup_downloads()
            self.set_status("")
            return 0

        try:
            affected = ips.check_if_safe(affected_image_root=img.get_root(), affected_pkg_fmris=fmri_set, opname='install', yield_func=wx.YieldIfNeeded)
        except:
            self.set_status("")
            wx.EndBusyCursor()
            msgbox(short_msg=_("Installation failed.\n\n"\
                    "Safety checks failed.\n\nPlease report the following error text to %(REPORT_TO)s.") % {
                        'REPORT_TO':INFO.REPORT_TO},
                    long_msg=utils.format_trace(), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                    caption=_("Error"), parent=self)
            self.set_status(_("Performing cleanup..."))
            img.cleanup_downloads()
            self.set_status("")
            return 1

        self.set_status("")

        if len(fmri_set) != len(to_install):
            final_list = []
            for fmri in iplan.target_fmris:
                final_list.append("%s (%s)" % (fmri.get_name(), fmri.version.get_short_version()))

            wx.EndBusyCursor()
            self.set_status("")
            preop_dlg = PreOpConfirmationDialog(self, -1, confirm_type=PreOpConfirmationDialog.INSTALL,
                    items=final_list, pkg_count=len(to_install), extra_pkg_count= len(fmri_set) - len(to_install))

            # preop_dlg.set_pre_op_size(123456)

            if preop_dlg.ShowModal() != wx.ID_OK:
                preop_dlg.Destroy()
                self.set_status(_("Performing cleanup..."))
                img.cleanup_downloads()
                self.set_status("")
                return -1

            wx.BeginBusyCursor()

            preop_dlg.Destroy()

        try:
            self.set_status(_("Fetching licenses..."))
            license_text, err_text = ips.fetch_licenses(iplan, opname='install')
            if err_text:
                wx.EndBusyCursor()
                self.set_status("")
                wx.MessageBox(_("Could not fetch licenses.\n\n%s\n\nInstallation did not occur.") % err_text,
                    style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
                self.set_status(_("Performing cleanup..."))
                try:
                    img.cleanup_downloads()
                except:
                    pass
                self.set_status("")
                return 1
            self.set_status("")
        except:
            wx.EndBusyCursor()
            self.set_status("")
            msgbox(short_msg=_("Could not fetch licenses.\n"\
                    "Installation did not occur.\n\n"\
                    "Please report the following error text to %(REPORT_TO)s.") % {
                        'REPORT_TO':INFO.REPORT_TO},
                    long_msg=utils.format_trace(), caption=_("Error"), parent=self)
            return 1

        wx.EndBusyCursor()
        self.set_status("")

        tou_s = ips.get_image_property(img, "image-tou-url", opname='install')
        if license_text and license_text != "" and LicenseDialog(self, msg=license_text, tou_url=tou_s).ShowModal() != wx.ID_OK:
            self.OnUnmarkAll(None)
            self.set_status(_("Performing cleanup..."))
            img.cleanup_downloads()
            self.set_status("")
            return -1

        rcode = 0
        try:
            self.set_status(_("Downloading and installing..."))
            pdlg = AppProgressTrackerDialog(self, -1, "", task=tracker_task)
            tracker_task.set_progress_dialog(pdlg)
            tracker_task.start()
            pdlg.ShowModal()
            ret = tracker_task.get_result()

            if ret[0] == TASK_END_USER_ABORT:
                wx.MessageBox(_("Download cancelled."), style=wx.OK|wx.ICON_INFORMATION|wx.CENTER, caption=_("Download cancelled"), parent=self)
                rcode = -1
            elif ret[0] == TASK_END_EXCEPTION:
                raise ret[1][0], ret[1][1], ret[1][2]
            elif ret[0] != TASK_END_SUCCESS:
                raise UpdateToolException(_("Internal Error: ThreadedTask did not communicate result properly"))
            else:

                # Run configurators after packages are installed.
                self.set_status(_("Performing configuration..."))
                iplan.pkg_plans = pkg_plans
                self.run_configurators(iplan, remove=False, task=tracker_task, pdlg=pdlg, opname='install')
                tracker_task.task_finished()

                self.set_status(_("Performing cleanup..."))
                img.cleanup_downloads()
                self.set_status("")

                # After updates have been applied we ping the notifer.
                # This causes the notifer to update its knowledge of pending
                # updates and determine if it needs to restart.
                view = self.imgs_tree.get_image_view()[1]
                if view == views.UPDATES:
                    ipcservice.send_command("nt_lock", "RESTART_CHECK")
                    ipcservice.send_command("nt_lock", "CHECK_UPDATES")

                if affected:
                    msg = _("Important updates to the %(APP_NAME)s have been applied. The %(APP_NAME)s should be " \
                            "restarted immediately to ensure proper operation.\n\nWould you like to restart the " \
                            "%(APP_NAME)s?") % {'APP_NAME':INFO.APP_NAME}
                    if wx.YES == wx.MessageBox(msg, caption=_("Restart %(APP_NAME)s") % {'APP_NAME':INFO.APP_NAME},
                            style=wx.YES|wx.NO|wx.ICON_WARNING|wx.CENTER, parent=self):
                        # A return code of 88 indicates a restart is needed.
                        os._exit(88)

        except:
            rcode = 1
            (typ, val) = sys.exc_info()[0:2]
            utils.logger.error(utils.format_trace())
            try:
                if tracker_task is not None and tracker_task.is_running():
                    tracker_task.task_finished()
            except:
                pass
            if isinstance(val, PermissionsException):
                if val.path:
                    msg = _("Could not operate on\n\n%s\n\nbecause of insufficient "
                                "permissions. Please retry with increased permissions.") % val.path
                else:
                    msg =  _("Could not complete the operation because of insufficient permissions.\n" \
                            "Please retry with increased permissions")
                wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
            elif isinstance(val, httplib.HTTPException) or isinstance(val, urllib2.HTTPError):
                # TODO : Replace this or remove this if better handling happens in IPS
                msg = _("Installation failed. Remote publisher could not be accessed.\n\nInternal error msg: %s") % \
                        utils.to_unicode(str(val))
                wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
            elif isinstance(val, ActionExecutionError):
                msg = _("Installation failed.\n\nInternal error msg: %s") % \
                        utils.to_unicode(str(val))
                wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
            elif isinstance(val, RetrievalError) \
                    or isinstance(val, TransportError):
                wx.MessageBox(_("Installation failed. Error while retrieving files:\n\n%(details)s") % {'details': str(val)},
                    style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
            elif str(typ) == 'urllib2.URLError':
                if isinstance(val, IOError):
                    if hasattr(val, 'reason'):
                        msg = _("Installation failed. Remote publisher could not be accessed.\n\nInternal error msg: %s") % \
                                val.reason
                        wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
                    elif hasattr(val, 'code'):
                        msg = _('Installation failed. The publishing server couldn\'t fulfill the request.'\
                               '\nError code: %s') % val.code
                        wx.MessageBox(msg, style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
                    else:
                        msgbox(short_msg=_("Installation failed.\n" \
                                "Please report the following error text to %(REPORT_TO)s.") % {
                                    'REPORT_TO':INFO.REPORT_TO},
                                long_msg=utils.format_trace(), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                                caption=_("Error"), parent=self)
                else:
                    msgbox(short_msg=_("Installation failed.\n"\
                            "Please report the following error text to %(REPORT_TO)s.") % {
                                'REPORT_TO':INFO.REPORT_TO},
                            long_msg=utils.format_trace(), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                            caption=_("Error"), parent=self)
            elif str(typ) == 'exceptions.RuntimeError':
                import re
                mat = re.match("^Cannot install (.+), file is in use$", str(val))
                if mat != None:
                    wx.MessageBox(_("Installation or updated failed. The file\n\n%s\n\nis in use. " \
                            "Please close any programs which might be using that file and try the " \
                            "operation again.") % mat.group(1),
                            style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
                else:
                    msgbox(short_msg=_("Installation failed.\n" \
                            "Please report the following error text to %(REPORT_TO)s.") % {
                                'REPORT_TO':INFO.REPORT_TO},
                            long_msg=utils.format_trace(), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                            caption=_("Error"), parent=self)
            else:
                msgbox(short_msg=_("Installation failed.\n" \
                        "Please report the following error text to %(REPORT_TO)s.") % {
                            'REPORT_TO':INFO.REPORT_TO},
                        long_msg=utils.format_trace(), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                        caption=_("Error"), parent=self)

        self.set_status(_("Performing cleanup..."))
        img.cleanup_downloads()
        self.set_status("")
        return rcode


    def __image_update(self, imagedir, iplan):
        """
        Do not call me directly. Use _install_components instead.
        Returns
        0 Success
        <0 User cancelled operation
        >0 Error
        """

        tracker_task = None

        try:
            wx.BeginBusyCursor()
            try:
                self.set_status(_("Fetching licenses..."))
                license_text, err_text = ips.fetch_licenses(iplan, opname='image-update')
                if err_text:
                    wx.EndBusyCursor()
                    self.set_status("")
                    wx.MessageBox(_("Could not fetch licenses.\n\n%s\n\nInstallation did not occur.") % err_text,
                        style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
                    return 1
                self.set_status("")
            except:
                wx.EndBusyCursor()
                self.set_status("")
                msgbox(short_msg=_("Could not fetch licenses.\n"\
                        "Installation did not occur.\n\n"\
                        "Please report the following error text to %(REPORT_TO)s.") % {
                            'REPORT_TO':INFO.REPORT_TO},
                        long_msg=utils.format_trace(), caption=_("Error"), parent=self)
                return 1

            wx.EndBusyCursor()
            self.set_status("")

            tou_s = ips.get_image_property(fsenc(imagedir), "image-tou-url", opname='image-update')
            if license_text and license_text != "" and LicenseDialog(self, msg=license_text, tou_url=tou_s).ShowModal() != wx.ID_OK:
                self.OnUnmarkAll(None)
                self.set_status("")
                return -1
            tracker_task = ImageUpdateTask(imageroot=imagedir, op_type='image-update')

            pdlg = AppProgressTrackerDialog(self, -1, "", task=tracker_task)
            tracker_task.set_progress_dialog(pdlg)
            tracker_task.start()

            pdlg.ShowModal()
            ret = tracker_task.get_result()

            if ret[0] == TASK_END_USER_ABORT:
                wx.MessageBox(_("Download cancelled."), style=wx.OK|wx.ICON_INFORMATION|wx.CENTER, caption=_("Download cancelled"), parent=self)
            elif ret[0] == TASK_END_EXCEPTION:
                raise ret[1][0], ret[1][1], ret[1][2]
            elif ret[0] != TASK_END_SUCCESS:
                raise UpdateToolException(_("Internal Error: ThreadedTask did not communicate result properly"))
            else:
                if not tracker_task.imageplan:
                    # issue 1675 - Somebody installed the packages some other way
                    # so this plan may not be empty
                    self.set_status("")
                    return 0

                # Run configurators after packages are installed.
                self.set_status(_("Performing configuration..."))
                iplan = tracker_task.imageplan
                self.run_configurators(tracker_task.imageplan, remove=False, task=tracker_task, pdlg=pdlg, opname='install')
                # HACK : Now rebuild the search index that we didn't let happen before due to the need to get at
                # imageplan.pkg_plans which get cleared if index creation is part of image update
                tracker_task.task_progress(_("Rebuilding search index"))
                ips.rebuild_search_index(fsenc(imagedir))
                tracker_task.task_finished()

                #self.set_status(_("Performing cleanup..."))
                #img.cleanup_downloads()
                #self.set_status("")

                # After updates have been applied we ping the notifer.
                # This causes the notifer to update its knowledge of pending
                # updates.
                view = self.imgs_tree.get_image_view()[1]
                if view == views.UPDATES:
                    ipcservice.send_command("nt_lock", "RESTART_CHECK")
                    ipcservice.send_command("nt_lock", "CHECK_UPDATES")

                final_fmri_set = []
                affected = []
                for pplan in iplan.pkg_plans:
                    if pplan.destination_fmri:
                        final_fmri_set.append(pplan.destination_fmri)

                    try:
                        affected.extend(ips.check_if_safe(affected_image_root=fsenc(imagedir), affected_pkg_fmris=final_fmri_set, opname='uninstall', yield_func=wx.YieldIfNeeded))
                    except:
                        x = utils.format_trace()
                        self.set_status("")
                        msgbox(short_msg=_("Installation failed.\n\n"\
                                "Safety checks failed.\n\nPlease report the following error text to %(REPORT_TO)s.") % {
                                    'REPORT_TO':INFO.REPORT_TO},
                                long_msg=x, style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                                caption=_("Error"), parent=self)
                        # we are logging here to avoid any L10n issue stopping us earlier
                        utils.logger.error(x)
                        return 1

                self.set_status("")

                if affected:
                    affected = sorted(set(affected))
                    msg = _("Important updates to the %(APP_NAME)s have been applied. The %(APP_NAME)s should be " \
                            "restarted immediately to ensure proper operation.\n\nWould you like to restart the " \
                            "%(APP_NAME)s?") % {'APP_NAME':INFO.APP_NAME}
                    if wx.YES == wx.MessageBox(msg, caption=_("Restart %(APP_NAME)s") % {'APP_NAME':INFO.APP_NAME},
                            style=wx.YES|wx.NO|wx.ICON_WARNING|wx.CENTER, parent=self):
                        # A return code of 88 indicates a restart is needed.
                        os._exit(88)

                self.set_status("")
                return 0
        except:
            (typ, val) = sys.exc_info()[0:2]
            utils.logger.error(utils.format_trace())
            try:
                if tracker_task is not None and tracker_task.is_running():
                    tracker_task.task_finished()
            except:
                pass
            if isinstance(val, UpdateToolException):
                wx.MessageBox(str(val), style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
            else:
                msgbox(short_msg=_("Installation failed.\n" \
                        "Please report the following error text to %(REPORT_TO)s.") % {
                            'REPORT_TO':INFO.REPORT_TO},
                        long_msg=utils.format_trace(), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                        caption=_("Error"), parent=self)

            self.set_status("")
            return 1


    def add_image(self, u_dir, quiet=True, add_any=False, opname=None):
        """
        Returns a tuple containing a unicode object of the actually added path and True
        in case of success or unicode path supplied and False in case of failure.
        """
        imgroot = ips.get_user_image_rootdir(fsenc(u_dir), opname=opname)

        if not imgroot:
            if add_any:
                self.imgs_tree.add_image_node(u_dir, enabled=False, opname=opname)
            if utils.is_v1_image(fsenc(u_dir)):
                msg = messages.NEW_IMAGE_MSG % {'path':u_dir}
                capn = messages.E_INCOMPATIBLE_IMAGE
            else:
                msg = messages.UNRECOGNIZED_IMAGE_VERIFY_MSG % {'path':u_dir}
                capn = messages.E_INVALID_IMAGE
            if not quiet:
                wx.MessageBox(msg, style=wx.OK|wx.ICON_EXCLAMATION|wx.CENTER, caption=capn, parent=self)
            utils.logger.debug(repr(msg))
            if add_any:
                return (u_dir, False)
            else:
                return (None, False)
        else:
            imgroot = fileutils.canonical_path(imgroot)
            self.imgs_tree.add_image_node(fsdec(imgroot), enabled=True, opname=opname)
            return (fsdec(imgroot), True)


    def load_images_list(self, add_any=True):
        if not self.config.has_option('main', 'image_list'):
            # No value saved yet
            return

        for path in utils.to_unicode(self.config.get('main', 'image_list')).splitlines():
            # XXX : We ignore the return here for now
            self.add_image(path.strip(), quiet=True, add_any=add_any, opname='list')


    def save_images_list(self):
        self.set_status("Saving list of images...")
        image_list_str = u""

        # Append newlines to the image pathes.  Newlines will be the
        # path spearator.
        for image in self.imgs_tree.installed_images:
            image_list_str = image_list_str + image + u"\n"

        if image_list_str != u"":
            self.config.set("main", "image_list", image_list_str.encode('utf8'))
        else:
            self.config.remove_option("main", "image_list")

        self.config.save_config()
        self.set_status("")


    def OnListingEvent(self, event):
        """Throws an exception on error"""
        if self._shutdown:
            self.Unbind(listers.EVT_LISTING_COMPONENT)
            return
        if self.list_ctrl.GetId() != event.GetId(): # We already removed this list
            return
        a, b = event.value
        if a == listers.LISTING_DATA:
            self.list_ctrl.append_data_row(fmri=b['fmri'], size=b['size'], items=b['items'])
            if self.list_ctrl.view == views.UPDATES:
                self.list_ctrl.imageplan = b['imageplan']
        elif a == listers.LISTING_INFORMATION:
            self.set_status(b)
        elif a == listers.LISTING_WARNING:
            # a warning message is not a final message so it will be followed by
            # a LISTING_SUCCESS, LISTING_ERROR or a LISTING_LONG_ERROR message.
            # Any dialogs popped up there must be aware of a previous dialog popped
            # up here.
            self.set_status("")
            wx.MessageBox(b, style=wx.OK|wx.ICON_WARNING|wx.CENTER,  caption=_("Warning"), parent=self)
        elif a == listers.LISTING_ERROR:
            wx.MessageBox(b, style=wx.OK|wx.ICON_ERROR|wx.CENTER,  caption=_("Error"), parent=self)
        elif a == listers.LISTING_LONG_ERROR:
            msgbox(short_msg=b[0], long_msg=b[1], style=wx.OK|wx.ICON_ERROR|wx.CENTER,  caption=_("Error"), parent=self)
        elif a == listers.LISTING_SUCCESS:
            pass
        else:
            utils.logger.error("Unknown OnListingEvent type encountered")
        if a in [listers.LISTING_ERROR, listers.LISTING_LONG_ERROR, listers.LISTING_SUCCESS]:
            self.Unbind(listers.EVT_LISTING_COMPONENT)
            self.set_status("")
            self.throbber.Rest()
            self.list_ctrl.set_updating(False)
            self.update_top_status()
            if self._prev_view == self.list_ctrl.view:
                self.list_ctrl.sort(column=self._prev_sort_col, order=self._prev_sort_flag)
            self.list_ctrl.set_initial_selection()
            if self.list_ctrl.view in [views.AVAILABLE, views.UPDATES]:
                self._enable_recent(True)
                self._enable_install(self.list_ctrl.checked_count != 0)
            if self.list_ctrl.view in [views.INSTALLED]:
                self._enable_remove(self.list_ctrl.checked_count != 0)
            if a in [listers.LISTING_ERROR, listers.LISTING_LONG_ERROR]:
                self.set_list_msg(_("Error encountered."))
            self._enable_refresh(True)

        wx.YieldIfNeeded()


    def run_configurators(self, imageplan, remove=False, task=None, pdlg=None, opname=None):
        """
        Run any configurators specified on packages using the
        com.sun.application.[postinstall|postupdate|preremove] attributes.

        For package install or update this should be called after
        the new packages are installed using the imageplan that was used
        to install the packages.

        For package removal this should be called before the packages are
        removed using the imageplan that will be used to remove the pacakges
        and "remove" should be set to False.
        """

        if imageplan == None:
            return

        l = utils.logger
        l.debug("==== Checking for configurators...")

        # Get root of image we are operating on
        image_root = imageplan.image.root

        # We scan the image plan and keep track of the pkgs and configuratros
        # to run in these two lists. We use lists because order is important
        # pkgs contains the package fmri, cmds contains the command strings
        pkgs = [ ]
        cmds = [ ]

        # For backwards compatibility we support old tags and new
        preremovetags   = [ "org.updatetool,preremove",
                            "com.sun.application.preremove" ]
        postinstalltags = [ "org.updatetool,postinstall",
                            "com.sun.application.postinstall" ]
        postupdatetags  = [ "org.updatetool,postupdate",
                            "com.sun.application.postupdate" ]

        seen_a_cmd = False

        # Imageplan should list packages in order that they were processed
        for pplan in imageplan.pkg_plans:
            if remove == True:
                # Package removal. We get info off the installed package
                pfmri = pplan.origin_fmri
                attrs = preremovetags
            elif pplan.origin_fmri == None:
                # There is no installed package. Therefore new install
                pfmri = pplan.destination_fmri
                attrs = postinstalltags
            else:
                # There is an installed package. Therefore update
                pfmri = pplan.destination_fmri
                attrs = postupdatetags

            mfst = ips.get_manifest(imageplan.image, pfmri, opname=opname)[0]

            # XXX : Should we abort all here or only one? What if they were interrelated?
            if not mfst:
                wx.MessageBox(_("Manifest for component '%s' could not be retrieved.\n\n" \
                        "It will not be configured.") % pfmri,\
                        style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"), parent=self)
                continue

            # Get value of command to run
            for s in attrs:
                cmdstring = mfst.get(s, None)
                if cmdstring != None:
                    break

            del mfst

            # If we already have an entry for this pkg, skip it
            if pfmri in pkgs:
                continue

            if cmdstring != None:
                seen_a_cmd = True
                # Save command string for this package.
                pkgs.append(pfmri)
                cmds.append(cmdstring)
                l.debug("Found configurator: %s: %s", pfmri, cmdstring)

        # If no configurators don't bother to do anything
        if seen_a_cmd == False:
            return

        # Done scanning image plan. Now process configurator commands

        if task != None:
            task.task_started(len(pkgs) * 2)
            wx.YieldIfNeeded()

        n = 0
        for pfmri in pkgs:
            cmdstring = cmds[n]
            n = n + 1

            if cmdstring == None:
                continue

            sfmri = pfmri.get_short_fmri()
            if remove:
                status_text = _("Unconfiguring %s...") % sfmri
            else:
                status_text = _("Configuring %s...") % sfmri

            if task != None:
                task.task_progress(status_text, (2 * n) - 1)
                if n <= 1:
                    # XXX 375 Make sure dialog is not modal, since we don't want
                    # to block in the dialog. This is a hack until fix this
                    # correctly by making configuration an ImagePlanTask
                    try:
                        pdlg.EndModal(0)
                    except:
                        # Some platforms throw an exception if the dialog was
                        # modal already. An IsModal check did not
                        # work in all cases
                        pass
                    pdlg.cancel_button.Enable(False)
                    pdlg.task.start_time = time.time()
                    pdlg.Show()

                pdlg.Refresh()
                wx.YieldIfNeeded()
                wx.Log.FlushActive()

            self.set_status(status_text)

            cmdlist = cmdstring.split()

            # Convert command to full path to command
            cmdlist[0] = fileutils.locate_cmd(cmdlist[0], image_root)

            msg_text = None
            if not os.path.isfile(cmdlist[0]):
                msg_text = _(
                    "The package script\n" \
                    "    %(script_path)s\n" \
                    "for package\n" \
                    "    %(package_name)s\n" \
                    "could not be found. The package script will be ignored.") % {
                            'script_path':cmdlist[0], 'package_name':sfmri}
            elif not os.access(cmdlist[0], os.X_OK):
                msg_text = _(
                    "The package script\n" \
                    "    %(script_path)s\n" \
                    "for package\n" \
                    "    %(package_name)s\n" \
                    "is not executable. The package script will be ignored.") % {
                            'script_path':cmdlist[0], 'package_name':sfmri}

            if msg_text != None:
                wx.MessageBox(msg_text,
                        style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"),
                        parent=self)
                if task != None:
                    task.task_progress("", (2 * n))
                continue

            # Create temp file to hold config script output
            temp_file = fileutils.create_temp_file()
            outputpath = temp_file[1]
            outputfile = os.fdopen(temp_file[0])

            # Windows doesn't support close_fds
            if os.name == "nt":
                use_close_fds = False
            else:
                use_close_fds = True

            # Execute config script
            try:
                wx.BeginBusyCursor()
                l.debug("Executing  %s", cmdstring)
                retcode = subprocess.call(cmdlist, bufsize=0, executable=None,
                    stdin=None, stdout=outputfile, stderr=subprocess.STDOUT,
                    preexec_fn=None, close_fds=use_close_fds, shell=False,
                    cwd=image_root, env=None, universal_newlines=False,
                    startupinfo=None, creationflags=0)
                self.set_status("")
                wx.EndBusyCursor()
            except:
                msgbox(
                    short_msg=_("The package script\n" \
                        "    %(script_path)s\n" \
                        "for package\n" \
                        "    %(package_name)s\n" \
                        "failed to execute. The package script will be ignored.\n" \
                        "Please report the following error text to %(email)s.") % {
                            'script_path':cmdstring, 'package_name':sfmri, 'email':INFO.REPORT_TO},
                    long_msg=utils.format_trace(), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                    caption=_("Error"), parent=self)
                self.set_status("")
                wx.EndBusyCursor()
                if task != None:
                    task.task_progress("", (2 * n))
                continue

            if task != None:
                task.task_progress("", (2 * n))

            # Check return code
            if not retcode == 0:
                # Error
                if remove:
                    msg_text = _(
                        "The unconfigure script\n" \
                        "    %(script_path)s\n" \
                        "for package\n" \
                        "    %(package_name)s\n" \
                        "reported the following error (%(error_number)d). The package will be removed from " \
                        "the system, but the package may not have cleaned up " \
                        "correctly. For more details see the script output " \
                        "in\n" \
                        "    %(output_path)s") % {
                                'script_path':cmdstring, 'package_name':sfmri, 'error_number':retcode, 'output_path':outputpath}
                else:
                    msg_text = _(
                        "The configuration script\n" \
                        "    %(script_path)s\n" \
                        "for package\n" \
                        "    %(package_name)s\n" \
                        "reported the following error (%(error_number)d). Package installation was " \
                        "successful, but the package may not be configured " \
                        "correctly. For more details see the script output " \
                        "in\n" \
                        "    %(output_path)s") % {
                                'script_path':cmdstring, 'package_name':sfmri, 'error_number':retcode, 'output_path':outputpath}
                # Display last 80 lines of output for user
                output_msg = fileutils.tail_lines(outputpath, 80)
                msgbox(short_msg=msg_text, long_msg=output_msg,
                    style=wx.OK|wx.ICON_ERROR|wx.CENTER, caption=_("Error"),
                    parent=self)
                outputfile.close()
            else:
                outputfile.close()
                os.remove(outputpath)

        if pdlg != None:
            pdlg.Hide()

        l.debug("Done with configurators")


    def _get_info_url(self, manifest):
        """
        Get the info URL from a package manifest.
        """
        return manifest.get(ips.INFO_URL_ATTR, None)


    def update_top_status(self):
        imagedir, view = self.imgs_tree.get_image_view()[0:2]
        if not imagedir:
            if self.imgs_tree.installed_images:
                self.set_status(_("Please select an image"), 1)
            else:
                self.set_status(_("Please create or open a new image"), 1)
            wx.YieldIfNeeded()
            return

        if not view or view == views.IMAGE:
            utils.logger.debug("no view so emptying the label")
            self.set_status("", 1)
            self.throbber.Rest()
            wx.YieldIfNeeded()
            return

        self._show_enable_search(True, False)
        wx.YieldIfNeeded()

        # It is possible that the list ctrl has not replaced the panel yet.
        # This happens on Mac OS X.
        if not isinstance(self.list_ctrl, wx.ListCtrl):
            self.set_status("", 1)
            self.right_panel.Layout()
            wx.YieldIfNeeded()
            return

        cnt = self.list_ctrl.GetItemCount()
        chk_cnt = self.list_ctrl.checked_count
        if view == views.INSTALLED:
            if not chk_cnt:
                if not cnt:
                    if self.list_ctrl.filtered:
                        self.set_status(_("No matches found"), 1)
                    else:
                        self.set_list_msg(_("No packages are installed.\nUse %s view to install components") % \
                                views.AVAILABLE)
                else:
                    if self.list_ctrl.filtered:
                        self.set_status(
                                n_("%(count)d matching component is installed",
                                    "%(count)d matching components are installed", cnt) % {'count':cnt}, 1)
                    else:
                        self.set_status(
                                n_("%(count)d component is installed",
                                    "%(count)d components are installed", cnt) % {'count':cnt}, 1)
            else:
                assert cnt >= chk_cnt, "checked items are more than actual items in the list"
                if self.list_ctrl.filtered:
                    self.set_status(
                            n_("%(count)d matching component will be removed (%(bytes_size)s)",
                                "%(count)d matching components will be removed (%(bytes_size)s)", chk_cnt) % {
                                    'count':chk_cnt, 'bytes_size':str(utils.readable_size(self.list_ctrl.checked_size))}, 1)
                else:
                    self.set_status(
                            n_("%(count)d component will be removed (%(bytes_size)s)",
                                "%(count)d components will be removed (%(bytes_size)s)", chk_cnt) % {
                                    'count':chk_cnt, 'bytes_size':str(utils.readable_size(self.list_ctrl.checked_size))}, 1)
            self._show_enable_search(True, cnt > 0 or self.list_ctrl.filtered)
        elif view == views.UPDATES:
            if not chk_cnt:
                if not cnt:
                    if self.list_ctrl.filtered:
                        self.set_status(_("No matches found"), 1)
                    else:
                        self.set_list_msg(_("No updates are available."))
                else:
                    self.set_status(
                            n_("%(count)d update is available",
                                "%(count)d updates are available", cnt) % {'count':cnt}, 1)
            else:
                assert cnt >= chk_cnt, "checked items are more than actual items in the list"
                self.set_status(
                    n_("%(count)d component will be updated (%(bytes_size)s)",
                        "%(count)d components will be updated (%(bytes_size)s)", chk_cnt) % {
                            'count':chk_cnt, 'bytes_size':str(utils.readable_size(self.list_ctrl.checked_size))}, 1)
            self._show_enable_search(True, cnt > 0 or self.list_ctrl.filtered)
        elif view == views.AVAILABLE:
            if not chk_cnt:
                if not cnt:
                    if self.list_ctrl.filtered:
                        self.set_status(_("No matches found"), 1)
                    else:
                        self.set_list_msg(_("No add-ons are available."))
                else:
                    if self.list_ctrl.filtered:
                        self.set_status(
                                n_("%(count)d matching component can be installed",
                                    "%(count)d matching components can be installed", cnt) % {'count':cnt}, 1)
                    else:
                        self.set_status(
                                n_("%(count)d component can be installed",
                                    "%(count)d components can be installed", cnt) % {'count':cnt}, 1)
            else:
                assert cnt >= chk_cnt, "checked items are more than actual items in the list"
                if self.list_ctrl.filtered:
                    self.set_status(
                            n_("%(count)d matching component will be installed (%(bytes_size)s)",
                                "%(count)d matching components will be installed (%(bytes_size)s)", chk_cnt) % {
                                    'count':chk_cnt, 'bytes_size':str(utils.readable_size(self.list_ctrl.checked_size))}, 1)
                else:
                    self.set_status(
                            n_("%(count)d component will be installed (%(bytes_size)s)",
                                "%(count)d components will be installed (%(bytes_size)s)", chk_cnt) % {
                                    'count':chk_cnt, 'bytes_size':str(utils.readable_size(self.list_ctrl.checked_size))}, 1)
            self._show_enable_search(True, cnt > 0 or self.list_ctrl.filtered)
        else:
            pass

        self._enable_mark_all(cnt > chk_cnt >= 0)
        self._enable_unmark_all(cnt > 0 and chk_cnt > 0)
        if not self.list_ctrl.is_updating():
            self._enable_refresh(True)
            self._enable_install((chk_cnt > 0) and (view in [views.AVAILABLE, views.UPDATES]))
            self._enable_remove((chk_cnt > 0) and (view in [views.INSTALLED]))
        wx.YieldIfNeeded()


    def OnToggleViewRecentVersions(self, dummy_event):
        # Issue 572 - event.Skip() causes multiple event triggers so don't do it
        # event.Skip()
        self.view_recent = not self.view_recent
        view = self.imgs_tree.get_image_view()[1]
        if view == views.AVAILABLE or view == views.UPDATES:
            self.update_image_view()


    def set_status(self, text, field=0):
        """
        Set status bar text for this frame. This is done lazily on Mac because each update
        causes a full Update() on that platform. See Issue 1131.
        """
        if not self._statusbar: # On app close, this can cause trace if not checked
            return

        if self._status_timer_interval > 0: # If we are using timers on this platform
            self._cached_status_text[field] = utils.to_unicode(text)
        else:
            self._statusbar.SetStatusText(utils.to_unicode(text), field)


    def OnStatusBarTimerEvent(self, dummy_event):
        # TODO : Maybe turn timer off completely if it has been idle for a while
        # TODO : and restart it on the next status event
        if self._status_timer_interval > 0 \
                and (time.time() - self._last_status_update_time) > self._status_timer_interval \
                and self._statusbar.GetFields() != self._cached_status_text:
            self._statusbar.SetFields(self._cached_status_text)
            self._last_status_update_time = time.time()
            wx.YieldIfNeeded()


    def show_featured_details_panel(self):
        self.right_panel_sizer.Hide(self.top_right)
        self.featured_details_panel.Show()
        self.right_panel.Layout()
        self.right_panel.Show()


    def hide_featured_details_panel(self):
        self.featured_details_panel.Hide()
        self.right_panel_sizer.Show(self.top_right)
        self.right_panel.Layout()
        self.right_panel.Show()


    def featured_callback(self, tree, entries):
        '''
        Called when an item in the Featured Software tree ctrl is selected
        '''
        wx.BeginBusyCursor()
        self.set_status(_("Processing..."))

        self.set_status("", 1)
        if self.right_splitter.IsShown():
            self.right_splitter.Hide()
            self._show_enable_search(False, False)
            self.throbber.Rest()
            self.right_panel.Layout()
            wx.YieldIfNeeded()

        if self.featured_details_panel is None:
            self.featured_details_panel = FeaturedDetailsPanel(self.right_panel, -1, style=wx.TAB_TRAVERSAL|wx.NO_BORDER)
            self.featured_details_panel.set_install_handler(
                                        self.OnInstallFeaturedSoftware)
            self.featured_details_panel.set_info_handler(
                                        self.OnLearnMoreFeaturedSoftware)

            self.right_panel_sizer.Add(self.featured_details_panel,
                                        1, wx.EXPAND, 1)
        else:
            self.featured_details_panel.delete_entries()

        try:
            # We don't necessarily show all entries. In particular we only show
            # add-on entries that are applicable to software that is already
            # installed, and we only show applications if they are NOT already
            # installed.
            images = self.imgs_tree.installed_images
            if entries is None or len(entries) == 0:
                filtered_entries = [ ]
            elif entries[0][bf.APP_TYPE] == "addon":
                filtered_entries = ips.filter_addon_entries(images, entries)
            else:
                filtered_entries = ips.filter_application_entries(images,
                                                                  entries)
        except Exception, e:
            short_msg=_("Error processing Featured Software")
            long_msg = utils.format_trace()
            utils.logger.error(short_msg)
            utils.logger.error(long_msg)
            msgbox(short_msg=short_msg, long_msg=long_msg,
                   style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                   caption=_("Error"), parent=self)
            self.set_status("")
            wx.EndBusyCursor()
            return

        self.featured_details_panel.load_entries(filtered_entries)
        self.show_featured_details_panel()
        # Disable toolbar buttons
        self._enable_install(False)
        self._enable_remove(False)
        self._enable_refresh(False)
        self.set_status("")
        wx.EndBusyCursor()


    def featured_feed_callback(self, basicfeed):
        '''
        After the featured software Atom feed is loaded we are called
        with the feed
        '''
        wx.YieldIfNeeded()
        try:
            feeddata = basicfeed.get_feed()
        except Exception, e:
            wx.YieldIfNeeded()
            utils.logger.warning("Unable to get featured software feed %s: %s",
                              basicfeed.get_url(), e)
            utils.logger.debug(utils.format_trace())
            return

        wx.YieldIfNeeded()

        try:
            # Load feed into images tree
            self.imgs_tree.load_feed(feeddata)
        except Exception, e:
            wx.YieldIfNeeded()
            utils.logger.warning("Unable to load feed %s into UI: %s",
                              basicfeed.get_url(), e)
            utils.logger.debug(utils.format_trace())
            return

        wx.YieldIfNeeded()


    def _choose_image(self, images=None):
        '''
        Put up a SingleChoiceDialog to have the user select an image.
        images is a list of image directories
        Returns the selected image directory
        '''

        if images is None or len(images) == 0:
            return None

        if len(images) == 1:
            single_image = True
        else:
            single_image = False

        # Create list of formatted choice items
        img_choices = [ ]
        for img in images:
            nodeid = self.imgs_tree.get_image_node(img)[0]
            if nodeid is not None:
                img_choices.append("%-30s %s" % (self.imgs_tree.GetItemText(nodeid), img.strip()))

        if single_image:
            dlg = wx.SingleChoiceDialog(self,
                message=_("This add-on applies to the following installed application.\nClick OK to install the add-on into this application, else click Cancel."),
                caption=_("Confirm Application Image"),
                choices=img_choices,
                )
        else:
            dlg = wx.SingleChoiceDialog(self,
                message=_("This add-on applies to multiple installed applications.\nPlease choose the application you would like to install the add-on into."),
                caption=_("Choose Application Image"),
                choices=img_choices,
                )
        #font = dlg.GetFont()
        #font.SetFamily(wx.FONTFAMILY_TELETYPE)
        #dlg.SetFont(font)
        #dlg.Refresh()

        if dlg.ShowModal() == wx.ID_OK:
            if single_image:
                sel = 0
            else:
                sel = dlg.GetSelection()
            dlg.Destroy()
            if sel >= 0:
                return images[sel]
            else:
                # User clicked OK but no image is selected.
                msg_text = _("Please choose the application you would " \
                        "like to install the add-on into or click Cancel" \
                        )
                wx.MessageBox(msg_text,
                        style=wx.OK|wx.ICON_INFORMATION|wx.CENTER,
                        caption=_("Information"), parent=self)
                # Prompt them again.
                return self._choose_image(images)
        else:
            dlg.Destroy()
            return None


    def OnInstallFeaturedSoftware(self, event):

        # Get Atom feed data from event
        entry = event.GetClientData()

        # Kepp track if this installation of featured software resulted
        # in a new directory being created
        new_directory = False
        application = False

        if entry is None or len(entry) < 1:
            return

        if entry[bf.APP_TYPE] in ("other"):
            if entry.has_key(bf.REL_URL):
                # For non IPS packaged software we just vector to web page
                wx.LaunchDefaultBrowser(entry[bf.REL_URL])
            return

        if entry[bf.APP_TYPE] in ("add-on", "addon"):
            # For add-ons we find an image that is configured with the
            # publisher this addon will come from.
            # Likely it will be one origin, but we handle multiple
            origins = [ p[bf.ORIGIN] for p in entry[bf.PUBLISHERS] ]
            # Get all images configured with these repo URLs
            images = ips.get_images_by_origin(
                            self.imgs_tree.installed_images, origins)
            if images is None:
                return

            # We only want images without the packages already installed
            image_list = [ img for img in images if not ips.has_installed_pkgs(fsenc(img),
                            entry[bf.PACKAGES]) ]

            if len(image_list) == 0:
                return
            # The add-on is applicable to one or more images.
            # Confirm which image to use
            u_chosen_dir = self._choose_image(images=image_list)
            if u_chosen_dir is None or len(u_chosen_dir) == 0:
                return
            # Now we go on to install the packages
        else:
            # Installing new software
            application = True

            # Create ImageCreateEditDialog and populate with default values
            # that we get from Atom feed

            dlg = ImageCreateEditDialog(self, opname='image-create',
                                    install=True)
            dlg.set_image_title(entry[bf.TITLE])
            dlg.set_image_description(entry[bf.TITLE])

            pubs = [ ( a[bf.NAME], a[bf.ORIGIN], a[bf.PREFERRED], None,
                None, a[bf.DISABLED] ) for a in entry[bf.PUBLISHERS] ]

            dlg.set_pubs(pubs)

            # Set a default installation path
            installpath = entry[bf.INSTALL_PATH]
            if installpath is not None and len(installpath) > 0:
                installpath = utils.expand_path_tokens(installpath)
            else:
                installpath = ""

            dlg.set_path(installpath, focus=True)

            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                # User did not select an image directory
                return

            chosen_dir = dlg.get_directory()
            pubs = dlg.get_pubs()
            img_title = dlg.get_image_title()
            img_desc = dlg.get_image_description()

            # Only destroy a dialog after you're done with it.
            dlg.Destroy()

            if chosen_dir is None or len(chosen_dir) == 0:
                return

            # Canonicalize the path
            chosen_dir = os.path.realpath(os.path.expanduser(chosen_dir))

            # Remember if we created this directory or not
            new_directory = not os.path.exists(chosen_dir)

            u_chosen_dir, success = self._create_new_image(chosen_dir, pubs, img_title, img_desc)

            # Install packages into u_chosen_dir
            if not success or len(u_chosen_dir) == 0:
                return

        # Select image node in tree control
        self.imgs_tree.select_image_node(u_chosen_dir, view=views.IMAGE)

        # We need package fmri's with complete versions.
        wx.BeginBusyCursor()
        self.set_status(_("Getting package information..."))
        try:
            img = ImageInterface(u_chosen_dir,
                    pkg.client.api.CURRENT_API_VERSION,
                    QuietProgressTracker(), None, None)
            info = img.info(fmri_strings=list(entry[bf.PACKAGES]), local=False,
                info_needed=set([PackageInfo.IDENTITY, PackageInfo.STATE]))
        except:
            self.set_status("")
            wx.EndBusyCursor()
            msg_text = _("Installation failed. Unable get package information for image %s.") \
                            % (u_chosen_dir)
            utils.logger.error(msg_text)
            utils.logger.error(utils.format_trace())
            msgbox(short_msg=msg_text,
                    long_msg=utils.format_trace(), style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                    caption=_("Error"), parent=self)
            return

        self.set_status("")
        wx.EndBusyCursor()
        # Generate list of packages to install, and install them
        install_list = [ PkgFmri(p.fmri) for p in info[ImageInterface.INFO_FOUND] ]

        if install_list is None or len(install_list) == 0:
            msg_text = _("Package installation failed for image\n%s.\n" \
                        "Could not get package information for\n" \
                        "%s") % (u_chosen_dir , entry[bf.PACKAGES] )
            wx.MessageBox(msg_text,
                        style=wx.OK|wx.ICON_ERROR|wx.CENTER,
                        caption=_("Error"), parent=self)
            utils.logger.error(msg_text)
            return
        rcode = 0
        try:
            rcode=self._install_components(u_chosen_dir,
                                           to_install=install_list)
        except:
            utils.logger.error(utils.format_trace())
            utils.logger.error("Could not install featured software")
            rcode = 1

        # If we were installing an application and the user cancelled
        # then remove the application image from the tree list
        if application and rcode < 0:
            self._close_image(u_chosen_dir)
            wx.YieldIfNeeded()
            # Move selection back to featured applicatoins
            # This is not working correctly. Sometimes the right panel
            # is not updated correctly or an exception is thrown
            #wx.CallAfter(self.imgs_tree.select_featured_application_item)

            # If we created the image directory, then remove it
            # We put it on a list for later removal
            if new_directory:
                utils.logger.info("Installation of featured software cancelled. Scheduling %s for removal." % u_chosen_dir)
                self._imagedir_destroy_list.append(fsenc(u_chosen_dir))
        return


    def OnLearnMoreFeaturedSoftware(self, event):

        # Get Atom feed data from event
        entry = event.GetClientData()

        if entry is None or len(entry) < 1:
            return

        # Pick a URL to load into a browser for more info. Our
        # first choice is the "alt_url", if we don't have
        # that then try the "rel_url".
        for key in [ 'alt_url', 'rel_url' ]:
            if not entry.has_key(key):
                continue
            url = entry[key]
            if len(url) > 0:
                learn_more_url = url
                break

        if learn_more_url is None or len(learn_more_url) < 1:
            return

        wx.LaunchDefaultBrowser(learn_more_url)


    def set_list_msg(self, msg):
        if isinstance(self.list_ctrl, wx.ListCtrl) and self.list_ctrl.is_updating():
            utils.logger.debug("set_list_msg called from " + utils.calling_method_name() + " whilte the list was still being updated")
            return
        if not self.right_splitter.IsSplit():
            self.right_splitter.SplitHorizontally(self.top_right, self.pkg_details_panel, 260)
        self.list_ctrl.Hide()
        self.list_msg.Show()
        self.list_msg.SetLabel(msg)
        self.top_right_sizer.Layout()
        self.right_panel.Layout()
        # Bug 1420 - If list_msg is showing something, the status bar shouldn't
        self.set_status("", 1)


    def _list_msg_clear(self):
        self.list_ctrl.Show()
        self.list_msg.SetLabel("")
        self.list_msg.Hide()
        self.top_right_sizer.Layout()
        self.right_panel.Layout()


    def DoSearch(self, u_text):
        wx.BeginBusyCursor()
        utils.logger.debug(u"Searching for " + u_text + str(type(u_text)))
        # XXX: Is there is a race condition here as the view may have just changed due to user or program action?
        imagedir, view = self.imgs_tree.get_image_view()[0:2]
        if not imagedir or view not in views.LIST_VIEWS:
            utils.logger.error("Search returning quietly on incorrect view")
            self._list_msg_clear()
            wx.EndBusyCursor()
            return False
        try:
            (img, reason) = ips.load_image_interface(imagedir)
            if img is None:
                utils.logger.error(reason)
                self.set_list_msg(_("No matches found.\n\n%s") % utils.to_unicode(reason))
                self.pkg_details_panel.describe_view(imagedir, view)
                wx.EndBusyCursor()
                return
        except:
            utils.logger.error(utils.format_trace())
            utils.logger.error("Search returning on image load failure")
            self.set_list_msg(_("Could not load image information."))
            self.pkg_details_panel.describe_view(imagedir, view)
            wx.EndBusyCursor()
            return False
        local = view == views.INSTALLED
        if u_text is None or u_text == u"":
            res = None
            self._list_msg_clear()
        else:
            ret, err_msg, res = ips.search(img, local=local, case_sensitive=False, criteria=fsenc(u_text))
            if not ret and len(err_msg) != 0:
                utils.logger.error("Search failed: " + str(res))
                if len(res) != 0:
                     wx.MessageBox(utils.to_unicode(str(err_msg)),
                    style=wx.OK|wx.ICON_INFORMATION|wx.CENTER, caption=_("Internal error"), parent=self)
                else:
                    self.set_list_msg(_("Search failed\n\n%s") % utils.to_unicode(str(res)))
                    self.pkg_details_panel.describe_view(imagedir, view)
                    wx.EndBusyCursor()
                    return False
            else:
                # Some result was returned
                pass
        self.list_ctrl.FilterItems(res)
        utils.logger.debug(u"Searched for " + u_text)
        if self.list_ctrl.filtered and self.list_ctrl.GetItemCount() == 0:
            self.set_list_msg(_("No matches found."))
            self.pkg_details_panel.describe_view(imagedir, view)
        else:
            self._list_msg_clear()
            idx = self.list_ctrl.set_initial_selection()
            if idx != -1:
                self.pkg_details_panel.describe_component(imagedir, self.list_ctrl.get_fmri(idx))
            else:
                utils.logger.debug("This should not happen in DoSearch")
                self.pkg_details_panel.describe_view(imagedir, view)
        self.update_top_status()
        wx.EndBusyCursor()
        if u_text == None or u_text.strip() == u"":
            return False
        else:
            return True



class AppToolBar(wx.ToolBar):
    _ = wx.GetTranslation

    def __init__(self, *args, **kwargs):
        # NOTE: If using the defaul ToolBar in a frame use 32, otherwise just use 24
        if '__WXMAC__' in wx.PlatformInfo:
            self.size = 32
        else:
            self.size = 24
        kwargs['style'] = wx.TB_HORIZONTAL|wx.NO_BORDER|wx.TB_NODIVIDER|wx.TB_FLAT|wx.TB_TEXT|wx.TAB_TRAVERSAL
        wx.ToolBar.__init__(self, *args, **kwargs)
        self.SetToolBitmapSize((self.size, self.size))
        self.Realize()

