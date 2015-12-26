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

import common.boot
import gettext

if False:    # Keep Pylint happy
    _ = gettext.gettext

NEW_IMAGE_MSG = _("This application image is of a newer version than supported by this tool:\n\n%(path)s\n\n" \
                    "You need to use a compatible version of the Update Tool to manage this application image. " \
                    "For example, you can execute \"bin/updatetool\" from within the image.")

INACCESSIBLE_IMAGE_REMOVE_MSG = _("The installation path of this application image is no longer accessible:\n\n%(path)s\n\n" \
"The installation may have been removed or the filesystem on which it existed is no longer available.\n\n" \
"If this installation no longer exists, you can remove this entry from the list of Application Images.")

UNRECOGNIZED_IMAGE_REMOVE_MSG = _("This location no longer contains a recognizable application image:\n\n%(path)s\n\n" \
"The installation may have been removed or modified such that important installation data is no longer available." \
"\n\nYou can remove this entry from the list of Application Images.")

UNRECOGNIZED_IMAGE_VERIFY_MSG = _("This location does not contain a recognizable application image:\n\n%(path)s\n\n" \
"Verify that the selected location contains a valid application installation.")

REMOVE_ENTRY_LABEL = _("Remove Entry")
REMOVE_ENTRY_TOOLTIP = _("Remove the selected application image entry")

E_INCOMPATIBLE_IMAGE = _("Error - Incompatible Application Image")
E_INVALID_IMAGE = _("Error - Invalid Application Image")

INCOMPATIBLE_IMAGE_LABEL = _("Incompatible Application Image")
INVALID_IMAGE_LABEL = _("Invalid Application Image")

EDIT_PROPERTIES_LABEL = _("Edit Properties...")
EDIT_PROPERTIES_TOOLTIP = _("Edit the image properties")

# XXX : This is to hopefully fix the current buggy label which shows &C but the
# the accelerator reads Ctrl+W
MSG_C = _("Close Image\tCtrl+W")
