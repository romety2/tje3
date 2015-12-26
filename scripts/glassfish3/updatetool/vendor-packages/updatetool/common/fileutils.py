# -*- coding: utf-8 -*-
#
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS HEADER.
#
# Copyright (c) 2008-2010 Oracle and/or its affiliates. All rights reserved.
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

import os
import tempfile

def locate_cmd(cmdpath, image_root):
    """
    Locate given command in the image_root. The command path is assumed
    to be relative to the image_root. If the command is not found then
    common OS suffixes (.sh, .ksh, etc) are appended to the command to
    see if a match can be found.
    """
    # If path is not absolute, make it absolute. Assume it is
    # relative to image_root
    if not os.path.isabs(cmdpath):
        cmdpath = image_root + os.sep + cmdpath

    # If command is found as given, then use it
    if os.path.isfile(cmdpath):
        return cmdpath

    # Otherwise see if we can find it using a suffix. This lets you
    # specify "cmd" as the value, and find cmd.bat on Windows and
    # cmd.sh on linux
    if os.name == "nt":
        sufixes = (".bat", ".exe")
    else:
        sufixes = (".sh", ".ksh", ".csh")

    for suffix in sufixes:
        path = cmdpath + suffix
        if os.path.isfile(path):
            return path

    # Give up and return full path version of what was passed in
    return cmdpath


def create_temp_file():
    """ Create a temp file. Returns a file object """
    return tempfile.mkstemp(suffix=".txt", prefix="updatetool-")


def tail_lines(filename, linesback=10, returnlist=0):
    """Does what "tail -10 filename" would have done
       Parameters:
            filename   file to read
            linesback  Number of lines to read from end of file
            returnlist Return a list containing the lines instead of a string

    """
    avgcharsperline=75

    file = open(filename,'r')
    while 1:
        try:
            file.seek(-1 * avgcharsperline * linesback, 2)
        except IOError:
            file.seek(0)

        if file.tell() == 0:
            atstart=1
        else:
            atstart=0

        lines = file.read().split("\n")
        if (len(lines) > (linesback+1)) or atstart:
            break

        # The lines are bigger than we thought
        avgcharsperline = avgcharsperline * 1.3 #Inc avg for retry
    file.close()

    if len(lines) > linesback:
        start=len(lines)-linesback -1
    else:
        start=0

    if returnlist:
        return lines[start:len(lines)-1]

    out=""
    for l in lines[start:len(lines)-1]:
        out=out + l + "\n"
    return out


def canonical_path(path):
    """
    Normalize a path completely taking care of

    1) case-insensitive/fake case filesystems,
    2) differing file separators
    3) symlink resolution

    etc.
    """
    return os.path.normpath(os.path.normcase(os.path.realpath(path)))
