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

from common.fsutils import fsenc
import wx
import common.ips as ips
import common.utils as utils
import gui.views as views
import wx.lib.agw.customtreectrl as CT
import common.basicfeed as BF

_ = wx.GetTranslation

#class AppImagesTreeCtrl(wx.TreeCtrl):
class AppImagesTreeCtrl(CT.CustomTreeCtrl):
    """Custom tree control which knows a bit about our application's model"""
    def __init__(self, parent, *args, **kwargs):
        #wx.TreeCtrl.__init__(self, parent, *args, **kwargs)
        CT.CustomTreeCtrl.__init__(self, parent, *args, **kwargs)

        self.installed_images = []
        self.AddRoot("Root")

        # When set the image_heading_item is the parent for all install image
        # nodes. We default to the tree root until it is set.
        self.image_heading_item = self.GetRootItem()

        # Heading for featured software. We may never have one of these.
        self.featured_heading_item = None

        # Wil get initialized later. See PaintLevel()
        self.default_indent = -1
        self.default_spacing = -1

        self.addon_item = None
        self.application_item = None
        self.SetSpacing(12)

        # This is need on the Mac (bug 1731) where the tree font is not
        # inherited by the tree items -- as if it were set via SetOwnFont()
        # Resetting it this way ensures the children use the tree font
        self.SetFont(self.GetFont())


    def SetImagesList(self, args=None):
        """Loads images to be used by the tree"""
        if args is None:
            return
        img_list = wx.ImageList(14, 14)
        for img in args:
            img_list.Add(utils.get_image(img))
        self.AssignImageList(img_list)


    def get_image_node(self, arg):
        """
        Returns a tuple containing (image node id in the tree, number) of an image arg or
        (C{None}, C{None}) if that image was not found.

        Raises a C{TypeError} on invalid argument type.

        @type n: number or C{unicode} string
        @param n: the image name or number (0 based) in the tree
        @rtype: C{tuple}
        @return: (child node's C{wx.TreeItemId}, num) on success or (C{None}, C{None}) on failure
        """
        if isinstance(arg, int):
            return self._get_nth_image_node(arg)
        elif isinstance(arg, basestring):
            return self._get_image_node_by_name(arg)
        else:
            raise TypeError, _("Invalid argument type: %s" % type(arg))


    def _get_nth_image_node(self, num):
        """
        0 based. Returns tuple (child node's wx.TreeItemId, num) on success or (None, None) on failure
        """
        if num < 0:
            num = abs(num) - 1

        if self.installed_images and num < len(self.installed_images):
            root = self.image_heading_item
            child = self.GetFirstChild(root)
            n = num

            while n:
                n = n - 1
                child = self.GetNextChild(root, child[1])
            return (child[0], num)
        return (None, None)


    def _get_image_node_by_name(self, u_name=None):
        """
        Returns tuple (child node's wx.TreeItemId, num) on success or (None, None) on failure
        """
        if not u_name in self.installed_images:
            return (None, None)

        return self._get_nth_image_node(self.installed_images.index(u_name))


    def remove_image_node(self, n):
        """
        Removes the nth image or image with the unicode path n from the image tree if it exists
        """
        node_id, num = self.get_image_node(n)
        if node_id:
            sibling = self.GetNextSibling(node_id) or self.GetPrevSibling(node_id)
            self.Delete(node_id)
            self.installed_images.pop(num)
            if sibling:
                def select_another_node(tree=self, node=None):
                    if node is not None:
                        tree.SelectItem(node)
                        tree.Expand(node)
                    # Playing with Focus here might be counter to a11y
                    tree.SetFocus()
                wx.CallAfter(select_another_node, self, sibling)
            return True
        return False


    def add_image_node(self, u_image_root_dir, enabled=True, opname=None):
        """
        Adds a unicode path to the image tree as it is.
        """
        if u_image_root_dir in self.installed_images:
            node_id, num = self.get_image_node(u_image_root_dir)
            self.Delete(node_id)
            self.installed_images.pop(num)
            del node_id, num

        title = ips.get_image_title(fsenc(u_image_root_dir), opname=opname)
        child = self.AppendItem(self.image_heading_item, title, image=0)
        self.SetPyData(child, PyData(u_image_root_dir, views.IMAGE, enabled))
        for row, view in enumerate(views.VIEWS):
            if view == views.IMAGE:
                continue
            c_id = self.AppendItem(child, view, image=row)
            self.SetPyData(c_id, PyData(u_image_root_dir, view, enabled))
        del row, view
        self.installed_images.append(u_image_root_dir)

        del title, child

        self._sort()
        return self.get_image_node(u_image_root_dir)


    def _add_heading(self, heading_text):
        root = self.GetRootItem()
        item = self.AppendItem(root, heading_text)
        self.SetItemBold(item)
        self.SetItemTextColour(item, wx.Colour(70, 70, 70))
        return item


    def add_image_heading(self, heading_text):
        '''
        The image heading acts as the section title and parent for the
        installed images
        '''
        item = self._add_heading(heading_text)
        self.image_heading_item = item
        return item


    def  is_heading(self, item):
        return item == self.image_heading_item or item == self.featured_heading_item


    def  is_application_image_item(self, item):
        '''
        An item is an application image if its parent is the Application Images
        heading
        '''
        try:
            return self.GetPyData(item).get_view_type() == views.IMAGE
        except:
            return False


    def add_featured_heading(self, heading_text):
        '''
        The featurd heading acts as the section title and parent for the
        featured software nodes
        '''
        item = self._add_heading(heading_text)
        self.featured_heading_item = item
        return item


    def get_image_view(self, view_id=None):
        """
        Returns a 3-tuple containing the image tree's concept of current
        imagedir, views identifier and the state of the image subtree
        (enabled or not) if view_id is not specified or if specified and
        matched.
        Otherwise returns (None, None, False) or if there is no currently
        active view.
        """

        tree_item = self.GetSelection()
        ret = tree_item and tree_item.IsOk()
        root = self.image_heading_item

        if not ret or tree_item == root:
            return (None, None, False)

        pd = self.GetPyData(tree_item)
        if pd is None:
            return (None, None, False)
        if view_id and pd.get_view_type() != view_id:
            return (None, None, False)
        return (pd.get_image_udir(), pd.get_view_type(), pd.is_enabled())


    def select_image_node(self, u_imagedir=None, view=None):
        """
        Selects the image node and expands it if necessary

        @type u_imagedir: C{unicode}
        @param u_imagedir: path as known to the us
        @type view: C{string}
        @param view: optional view name
        @return: The C{wx.TreeItemId} if the node was found or C{None} otherwise.
        """
        if not u_imagedir:
            utils.logger.debug("Nothing to select.")
            return None

        node_id = self.get_image_node(u_imagedir)[0]

        if not node_id:
            utils.logger.debug("Could not get node id of %s to select." % u_imagedir)
            return None

        return self.select_image_node_byitem(node_id, view)


    def select_image_node_byitem(self, node_id=None, view=None):
        """
        Selects the image node and expands it if necessary

        @type node_id: C{wx.TreeItemId}
        @param node_id: Tree item to select
        @type view: C{string}
        @param view: optional view name
        @return: The C{wx.TreeItemId} if the node was found or C{None} otherwise.
        """
        if node_id is None:
            return None

        if view in [views.AVAILABLE, views.UPDATES, views.INSTALLED]:
            utils.logger.debug("Nothing to select.")
            child = self.GetFirstChild(node_id)

            while child and self.GetItemText(child[0]) != view:
                child = self.GetNextChild(node_id, child[1])

            if not (child and self.GetItemText(child[0]) == view):
                return child[0]
            else:
                node_id = child[0]

        if not node_id:
            return None

        self.SelectItem(node_id)
        self.Expand(node_id)
        # Playing with Focus here might be counter to a11y
        self.SetFocus()
        return node_id


    def PaintLevel(self, item, dc, level, y, align):
        """
        We interpose on the CustomTreeCtrl PaintLevel method.
        If we are painting level 1 then we are painting one of the
        headings. In this case we do not want an expand button on the
        item and we don't want to indent it.
        """

        style = self.GetWindowStyle()
        if self.default_indent == -1:
            # Remember original indent setting for list
            self.default_indent = self._indent

        if self.default_spacing == -1:
            self.default_spacing = self._spacing

        if level == 1:
            # Supress indentation and expand button
            self._indent = 0
            self._spacing = 8
            style &= ~CT.TR_HAS_BUTTONS
            self.SetWindowStyle(style)
        else:
            self._indent = self.default_indent
            self._spacing = self.default_spacing
            style |= CT.TR_HAS_BUTTONS
            self.SetWindowStyle(style)

        # Forward call to super class
        rcode = super(AppImagesTreeCtrl, self).PaintLevel(item, dc, level, y, align)
        # Restore default values
        self._indent = self.default_indent
        self._spacing = self.default_spacing
        style |= CT.TR_HAS_BUTTONS
        self.SetWindowStyle(style)
        return rcode


    def refresh_image_node(self, u_imagedir=None, view=None, opname=None):
        """
        Selects the image node and rereads and set the title on the node
        """
        node_id = self.select_image_node(u_imagedir=u_imagedir, view=view)

        if node_id is not None:
            title = ips.get_image_title(fsenc(u_imagedir), opname=opname)
            if view == views.IMAGE:
                self.SetItemText(node_id, title)
            elif self.image_heading_item == self.GetItemParent(node_id):
                self.SetItemText(node_id, title)
            else:
                self.SetItemText(self.GetItemParent(node_id), title)
            self._sort()


    def _sort(self):
        """
        Sorts the nodes based on their labels and syncs internal images list
        """
        self.installed_images = []
        root = self.image_heading_item
        if not root:
            return

        self.SortChildren(root)

        count = self.GetChildrenCount(root)
        if not count:
            return

        child = self.GetFirstChild(root)
        while child[0] and child[0].IsOk():
            self.installed_images.append(self.GetPyData(child[0]).get_image_udir())
            child = self.GetNextChild(root, child[1])


    def load_feed(self, feeddata):
        '''
        Load featured software feed into featured software items
        '''
        self.feed = feeddata
        if self.featured_heading_item is None:
            self.add_featured_heading(_("Featured Software"))

        if self.application_item is None:
            item = self.AppendItem(self.featured_heading_item, _("Applications"))
            self.SetItemImage(item, 0, wx.TreeItemIcon_Normal)
            self.application_item = item

        if self.addon_item is None:
            item = self.AppendItem(self.featured_heading_item, _("Add-ons"))
            self.SetItemImage(item, 1, wx.TreeItemIcon_Normal)
            self.addon_item = item

        self.EnsureVisible(self.application_item)
        # Split feed into lists of apps and addons
        (apps, addons) = self._split_feed(feeddata)

        self.SetItemPyData(self.application_item, apps)
        self.SetItemPyData(self.addon_item, addons)


    def _split_feed(self, feeddata):
        """
        Split a single feeddata into two lists of entries. The
        first is for app_types of "pkg" or "native", the
        second is for app_types of "addon
        """
        apps = []
        addons = []
        for e in feeddata[BF.ENTRIES]:
            if e[BF.APP_TYPE] == "addon":
                addons.append(e)
            else:
                apps.append(e)

        return (apps, addons)


    def select_featured_application_item(self):
        self.SelectItem(self.application_item)



class PyData(object):
    def __init__(self, u_dir=None, view_type=None, enabled=True):
        self.image_udir = u_dir
        self.view_type = view_type
        self.enabled = True


    def get_image_udir(self):
        return self.image_udir


    def get_view_type(self):
        return self.view_type


    def is_enabled(self):
        return self.enabled


    def enable(self, flag=True):
        self.enabled = flag
