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
from common.widgets.checklistctrl import CheckListCtrl

import wx

if False:    # Keep Pylint happy
    import gettext
    _ = gettext.gettext


class AvailableCheckListCtrl(CheckListCtrl):
    """
    Represents the available add-ons view component data for the Update Tool GUI.
    """

    _ = wx.GetTranslation

    def __init__(self, parent, ident, *args, **kwargs):
        CheckListCtrl.__init__(self, parent, ident, *args, **kwargs)


    def OnGetItemText(self, item, col):
        """
        Interface implemented for virtual list control.

        Formats various data types here.
        """
        if col == 0: # checkbox
            return ""
        elif col == 3: # time
            return self.itemDataMap[self.itemIndexMap[item]][col].strftime("%x")
        elif col == 5: # size
            return utils.readable_size(self.itemDataMap[self.itemIndexMap[item]][col])
        else:
            return self.itemDataMap[self.itemIndexMap[item]][col]


class UpdatesCheckListCtrl(CheckListCtrl):
    """
    Represents the updates view component data for the Update Tool GUI.
    """

    _ = wx.GetTranslation

    def __init__(self, parent, ident, *args, **kwargs):
        CheckListCtrl.__init__(self, parent, ident, *args, **kwargs)


    def OnGetItemText(self, item, col):
        """
        Interface implemented for virtual list control.

        Formats various data types here.
        """
        if col == 0: # checkbox
            return ""
        elif col == 2: # security
            if self.itemDataMap[self.itemIndexMap[item]][col]:
                return "*"
            else:
                return ""
        elif col == 3: # time
            return self.itemDataMap[self.itemIndexMap[item]][col].strftime("%x")
        elif col == 6: # size
            return utils.readable_size(self.itemDataMap[self.itemIndexMap[item]][col])
        else:
            return self.itemDataMap[self.itemIndexMap[item]][col]


    def OnGetItemColumnImage(self, item, col):
        """
        Interface implemented for virtual list control. Column Sorter depends on this.
        """
        if col == 0:
            # delegate to default method for getting checkbox image index
            return self.OnGetItemImage(item)
        elif col == 2:
            # security icon is in this column. return image index.
            if self.itemDataMap[self.itemIndexMap[item]][col]:
                return 4
            else:
                return -1
        else:
            return -1



class InstalledCheckListCtrl(CheckListCtrl):
    """
    Represents the installed add-ons view component data for the Update Tool GUI.
    """

    _ = wx.GetTranslation

    def __init__(self, parent, ident, *args, **kwargs):
        CheckListCtrl.__init__(self, parent, ident, *args, **kwargs)


    def OnGetItemText(self, item, col):
        """
        Interface implemented for virtual list control.

        Formats various data types here.
        """
        if col == 0: # checkbox
            return ""
        elif col == 4: # size
            return utils.readable_size(self.itemDataMap[self.itemIndexMap[item]][col])
        else:
            return self.itemDataMap[self.itemIndexMap[item]][col]
