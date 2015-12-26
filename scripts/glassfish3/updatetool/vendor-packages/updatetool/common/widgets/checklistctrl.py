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

"""Main component checklist control"""

import common.utils as utils
from common.mixins import KeywordArgsMixin

import wx
from wx.lib.mixins.listctrl import CheckListCtrlMixin, ListCtrlAutoWidthMixin, ColumnSorterMixin
import locale

if False:    # Keep Pylint happy
    import gettext
    _ = gettext.gettext


class CheckListCtrl(wx.ListCtrl, CheckListCtrlMixin, ListCtrlAutoWidthMixin, ColumnSorterMixin, KeywordArgsMixin):
    """
    CheckListCtrl is a ListCtrl extended with the following capabilities:

    1) CheckListCtrlMixin - allows checking unchecking of items
    2) ListCtrlAutoWidthMixin - automatically resizes the last column of the list to fit the display
    3) ColumnSorterMixin - allows sorting of columns

    The IPS FMRIs for each row of item are stored in self.view_fmris indexed by an index which happens to
    be the row number at first insertion.

    The size (change) FMRIs for each row of item are stored in self.view_sizes indexed by an index which
    happens to be the row number at first insertion.

    A total of checked_size and checked items is kept updated constantly.

    The control assumes that the data the checkbox is in the first column of data.
    """

    _ = wx.GetTranslation


    def __init__(self, parent, ident, *args, **kwargs):
        KeywordArgsMixin.__init__(self)
        self.kwset(kwargs, 'num_cols', required=True)
        self.kwset(kwargs, 'size_column', required=True)
        kwargs['style']=wx.LC_REPORT|wx.LC_SINGLE_SEL|wx.LC_VIRTUAL

        assert self._size_column < self._num_cols
        assert self._size_column != 0 # This is the checkbox column

        self.kwset(kwargs, 'default_sort_column', default=-1)
        assert self._default_sort_column < self._num_cols

        wx.ListCtrl.__init__(self, parent, ident, *args, **kwargs)

        CheckListCtrlMixin.__init__(self) # must be inited before ColumnSorterMixin
        ListCtrlAutoWidthMixin.__init__(self)
        self._init_data()

        self._updating = False
        # init ColumnSorterMixin
        ColumnSorterMixin.__init__(self, self._num_cols)

        # This image list has been assigned by CheckListCtrlMixin
        il = self.GetImageList(wx.IMAGE_LIST_SMALL)
        self._color_attr = wx.ListItemAttr()
        self._color_attr.SetBackgroundColour(wx.Color(red=242, green=245, blue=247))
        self._white_attr = wx.ListItemAttr()
        self._white_attr.SetBackgroundColour(wx.Color(red=255, green=255, blue=255))
        self.up_arrow = il.Add(utils.get_image("arrow-up-16x16.png"))
        self.dn_arrow = il.Add(utils.get_image("arrow-down-16x16.png"))
        self.security_icon = il.Add(utils.get_image("security-16-12.png"))
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_LIST_DELETE_ALL_ITEMS, self.OnDeleteAllItems)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
        self._enhance_glyphs()


    def FilterItems(self, lst=None):
        self.Freeze()
        if self.filtered:
            self.itemIndexMap = self.old_itemIndexMap
            self.checked_size = self.old_checked_size
            self.checked_count = self.old_checked_count
            del self.old_itemIndexMap, self.old_checked_size, self.old_checked_count
            self.filtered = False
            self.SetItemCount(len(self.itemDataMap.keys()))

        if lst is None:
            self.Thaw()
            return

        self.new_itemIndexMap = {}
        self.new_checked_size = 0
        self.new_checked_count = 0
        _count = len(self.itemIndexMap)
        _newindex = -1
        for _oldidx in xrange(_count):
            _internal_key = self.itemIndexMap[_oldidx]
            item = self.itemDataMap[_internal_key]
            if self.view_fmris[_internal_key].get_fmri(anarchy=True) in lst:
                _newindex += 1
                self.new_itemIndexMap[_newindex] = _internal_key
                if item[0]:
                    self.new_checked_count += 1
                    self.new_checked_size += self.view_sizes[_internal_key]

        self.itemIndexMap, self.old_itemIndexMap  = self.new_itemIndexMap, self.itemIndexMap
        self.checked_size, self.old_checked_size = self.new_checked_size, self.checked_size
        self.checked_count, self.old_checked_count = self.new_checked_count, self.checked_count
        self.filtered = True
        self.SetItemCount(_newindex + 1)
        del self.new_itemIndexMap, _newindex
        self.Thaw()


    def SortItems(self, sorter=cmp):
        """
        Overridden to keep our internal items in sync.
        """
        items = list(self.itemDataMap.keys())
        items.sort(sorter)
        self.itemIndexMap = items

        # redraw the list
        self.Refresh()


    def OnGetItemText(self, item, col):
        """ Interface implemented for virtual list control"""
        if col == 0: # checkbox
            return ""
        else:
            return self.itemDataMap[self.itemIndexMap[item]][col]


    def OnGetItemAttr(self, row):
        """ Interface implemented for virtual list control"""
        if row % 2:
            return self._white_attr
        else:
            return self._color_attr


    def OnGetItemImage(self, item):
        """
        Interface implemented for virtual list control. Column Sorter depends on this.
        """
        if self.IsChecked(item):
            return 1
        else:
            return 0


    def OnGetItemColumnImage(self, item, col):
        """
        Interface implemented for virtual list control. Column Sorter depends on this.
        """
        if col == 0:
            if self.IsChecked(item):
                return 1
            else:
                return 0
        else:
            return -1


    def IsChecked(self, item):
        """
        Overridden from CheckListCtrlMixin to make it work with Virtual CheckListCtrlMixin.
        """
        return self.itemDataMap[self.itemIndexMap[item]][0]


    def _enhance_glyphs(self):
        """
        Tweak the checkbox glyphs used by the list control
        """
        if wx.Platform == "__WXGTK__":
            # On GTK the bottom of the checkbox glyph is clipped for
            # many themes. We nudge it up two pixels
            il = self.GetImageList(wx.IMAGE_LIST_SMALL)
            # Shift up the uncheck glyph
            bmp = il.GetBitmap(0)
            utils.shift_checkbox_bitmap(self, bmp, 2, 0)
            il.Replace(0, bmp)
            # Shift up the checked glyph
            bmp = il.GetBitmap(1)
            utils.shift_checkbox_bitmap(self, bmp, 2, wx.CONTROL_CHECKED )
            il.Replace(1, bmp)
            #self._shift_checkbox(2, 0)
            #self._shift_checkbox(2, wx.CONTROL_CHECKED )


    def set_updating(self, boolean=True):
        # Hack needed to disable sorting while the list is being updated because we do not control the
        # ColumnSorterMixin
        #utils.logger.debug("set_updating " + repr(boolean) + " called from " + utils.calling_method_name())
        self._updating = boolean


    def is_updating(self):
        #utils.logger.debug("is_updating called from " + utils.calling_method_name())
        return self._updating


    def OnColClick(self, evt):
        if self.is_updating():
            # Prevent sorting
            return
        else:
            evt.Skip()


    def GetSortImages(self):
        """
        Interface used by ColumnSorterMixin
        """
        return (self.dn_arrow, self.up_arrow)


    def GetListCtrl(self):
        """
        Interface required by ColumnSorterMixin
        """
        return self


    def get_fmri(self, row):
        return self.view_fmris[self.itemIndexMap[row]]


    def get_bytesize(self, row):
        return self.view_sizes[self.itemIndexMap[row]]


    def _init_data(self):
        """
        The itemDataMap stores data used by the ColumnSorterMixin. See constructor for other
        details.

        """
        self.view_fmris = {}
        self.view_sizes = {}
        self.checked_size = 0
        self.checked_count = 0
        self.itemDataMap = {}       # Maps unique key (not a physical list row number) to a row of data
        self.itemIndexMap = []      # Maps physical row number to itemDataMap key
        self.SetItemCount(0)
        self.filtered = False


    def OnItemActivated(self, evt):
        """Overridden callback to provide checking/unchecking on sequential clicks"""
        self.ToggleItem(evt.m_itemIndex)
        evt.Skip()


    def ToggleItem(self, itm):
        self.itemDataMap[self.itemIndexMap[itm]][0] = not self.IsChecked(itm)
        self.OnCheckItem(itm, self.itemDataMap[self.itemIndexMap[itm]][0])


    def OnDeleteAllItems(self, evt):
        self._init_data()
        evt.Skip()


    def GetColumnSorter(self):
        """
        Interface required by ColumnSorterMixin. Returns a sorter with custom knowledge of our data.
        """
        return self._app_column_sorter


    def _app_column_sorter(self, key1, key2):
        """
        Custom sorting logic needed by ColumnSorterMixin.
        """
        col = self._col
        ascending = self._colSortFlag[col]
        # Note : First (checkboxes) column is represented in the itemDataMap as integers 0 an 1
        # and maintained in the OnCheckItem handler by the application
        if col == self._size_column:
            item1 = self.view_sizes[key1]
            item2 = self.view_sizes[key2]
        else:
            item1 = self.itemDataMap[key1][col]
            item2 = self.itemDataMap[key2][col]

        #--- Internationalization of string sorting with locale module
        if type(item1) == type('') or type(item2) == type(''):
            cmpVal = locale.strcoll(str(item1), str(item2))
        else:
            cmpVal = cmp(item1, item2)
        #---

        # If the items are equal then pick something else to make the sort value unique
        if cmpVal == 0:
            cmpVal = apply(cmp, self.GetSecondarySortValues(col, key1, key2))

        if ascending:
            return cmpVal
        else:
            return -cmpVal


    def OnCheckItem(self, idx, flag):
        self.itemDataMap[self.itemIndexMap[idx]][0] = flag # Update the representative data for checkbox for sorting
        if flag:
            self.checked_size += self.get_bytesize(idx)
            self.checked_count += 1
        else:
            self.checked_size -= self.get_bytesize(idx)
            self.checked_count -= 1
        self.Refresh()


    def GetSecondarySortValues(self, col, key1, key2):
        """
        Returns a tuple of 2 values to use for secondary sort values when the
        items in the selected column match equal.
        """
        if col != self._default_sort_column and self._default_sort_column != -1:
            return (self.itemDataMap[key1][self._default_sort_column], self.itemDataMap[key2][self._default_sort_column])
        else:
            return (key1, key2)


    def append_data_row(self, fmri=None, size=None, items=[]):
        """
        Appends a row of data
        """
        assert fmri is not None
        assert size is not None
        if not self.is_updating():
            utils.logger.error("Throwing exception on append request for " + repr(fmri))
            raise "Call updating(True) before updating the list from", utils.calling_method_name()
        idx = len(self.itemDataMap.keys())
        self.view_fmris[idx] = fmri
        self.view_sizes[idx] = size
        self.itemDataMap[idx] = items
        self.itemIndexMap.append(idx)
        self.SetItemCount(idx+1)
        if items[0]:
            self.checked_size += self.get_bytesize(idx)
            self.checked_count += 1
        wx.YieldIfNeeded()


    def GetSortState(self):
        """
        Return a tuple containing the index of the column that was last sorted
        and the sort direction of that column.
        Usage:
        col, ascending = self.GetSortState()
        # Make changes to list items... then resort
        self.SortListItems(col, ascending)
        """
        return (self._col, self._colSortFlag[self._col])


    def sort(self, column=-1, order=1):
        if column == -1:
            if self._default_sort_column != -1:
                self.SortListItems(col=self._default_sort_column)
                wx.CallAfter(self.OnSortOrderChanged)
        else:
            self.SortListItems(col=column, ascending=order)
            wx.CallAfter(self.OnSortOrderChanged)


    def get_sort_flag(self, column):
        return self._colSortFlag[column]


    def set_initial_selection(self):
        '''
        Select an appropriate row in the list contrl. Return -1 on failure or the index selected.
        '''

        # If no items no selection
        if self.GetItemCount() < 1:
            return -1

        if not self.IsShown():
            return -1

        _sel = self.GetFirstSelected()

        # If nothing checked or selected, select top item
        if self.checked_count < 1 and _sel == -1:
            idx = self.GetTopItem()
            self.SetItemState(idx, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            self.SetItemState(idx, wx.LIST_STATE_FOCUSED, wx.LIST_STATE_FOCUSED)
            return idx

        if _sel != -1:
            self.EnsureVisible(_sel)
            return _sel

        # Something is checked. Find the first one and select it
        # and ensure it is visible
        for idx in range(self.GetItemCount()):
            if self.IsChecked(idx):
                self.SetItemState(idx, wx.LIST_STATE_SELECTED,
                                       wx.LIST_STATE_SELECTED)
                self.SetItemState(idx, wx.LIST_STATE_FOCUSED,
                                       wx.LIST_STATE_FOCUSED)
                self.EnsureVisible(idx)
                return idx
        return -1

