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

"""
This module allows co-operative soft locking of an image directory within
the same application. This is needed mainly because

    1. pkg(5) does not provide explicit image locking
    2. various user interaction events, programmtic events or bugs might want
       to switch to a different view while some view is not fully processed
       yet and an immediate switch without a clean stop on the same image causes
       data corruption due to 1.
    3. we need a single item queue for next desired view due to 3 and the reason
       that our event handlers can not block the UI forever.

To perform any operations via the lockmanager, a global C{lock()} must be first
acquired and C{release()}d as soon as possible.

The lockmanager makes use of the fact that python modules are singletons.

"""
import thread
from common import utils
from gui import views

#: global app wide lock
__lock = thread.allocate_lock()

#: hold current state of various active image/views
__images = []

#: single item queue for the desired image/view
__desired_img_view = (None, None)

# thread state flag constants
RUNNING = 1  #: the thread is running
ABORT = 2    #: the thread has been asked to/is in the process of aborting

def lock():
    """
    Acquire lockmanager lock. A lockmanager lock must be acquired before performing
    any other operations via the lockmanager. The lock should be released as soon as
    possible by called L{gui.lockmanager.release}. This method blocks till a lock is
    available.
    """
    global __lock

    __lock.acquire_lock()


def is_locked():
    """
    Is lockmanager locked?
    """
    global __lock

    return __lock.locked()


def release():
    """
    Release the lockmanager lock. See L{gui.lockmanager.lock}.
    """
    global __lock

    __lock.release()


def get_desired_image_view():
    """
    Get the image/view the GUI is waiting to switch to.

    @return: The image/view the GUI is waiting to switch to or C{(None, None)} if no such request is pending.
    @rtype: C{tuple}
    """
    global __desired_img_view

    return __desired_img_view


def set_desired_image_view(image=None, view=None):
    """
    Set the image/view the GUI is waiting to switch to.

    @return: The image/view the GUI should switch to or C{(None, None)} to clear
    @rtype: C{tuple}
    """
    global __desired_img_view

    assert (image is not None and view is None or view in views.VIEWS) or (image is None and view is None)

    __desired_img_view = (image, view)


def get_image_state(image=None):
    """
    Get the view and it's current state C{(RUNNING/ABORT)} for a specified image
    as known to the lock manager.

    @return: a tuple containing the view and the state if applicable. C{None, None} othewise.
    @rtype: C{tuple}
    """
    global __images

    assert image is not None

    for i, v, s in __images:
        if i == image:
            return (v, s)
    return (None, None)


def is_aborting(image, view):
    """
    Is a thread for a given image and view is in the process of aborting?

    @param image: the image to check
    @type image: C{unicode} string

    @param view: the view to check
    @type view: L{gui.views.VIEWS}

    @rtype: C{boolean}
    """
    global __images, ABORT

    assert image is not None
    assert view in views.VIEWS

    for i, v, s in __images:
        if i == image and v == view and s == ABORT:
            return True
    return False


def any_active():
    """
    Are any threads on any images known to us active?
    """
    global __images

    return len(__images) # Yeah I know


def abort_all():
    """
    Requests all threads on all images to abort.
    """
    global __images

    for i, v, s in __images:
        flag_abort(i)


def flag_abort_except(image=None):
    """
    Flags the thread for images except the specified image as C{ABORT} desired.
    """
    global __images, ABORT

    assert image is not None

    __images = [(i, v, ABORT) for i, v, s in __images if i != image]


def flag_abort(image=None):
    """
    Flags the thread for image as C{ABORT} desired.
    """
    global __images, ABORT

    assert image is not None

    mod = []
    did = False
    for i, v, s in __images:
        if i == image:
            mod.append((i, v, ABORT))
            if not did:
                did = True
            else:
                raise Exception("Multiple threads found running for " + repr(image))
        else:
            mod.append((i, v, s))

    if not did:
        raise Exception("Trying to abort something that was not running")
    __images = mod


def flag_running(image, view):
    """
    Flags that the thread for image/view is now C{RUNNING}.
    """
    global __images, RUNNING

    assert view in views.VIEWS

    for i, v, s in __images:
        if i == image:
            # If our application's concurrency logic stays correct, this will never happen
            raise Exception("Trying to run " + repr(image) + "/" + repr(view) + " while " + repr(i) + "/" + repr(v) + "/" + repr(s) + " was happening")
    __images.append((image, view, RUNNING))


def done(image, view):
    """
    Marks the state of an image/view thread as done. Raises an C{Exception} if the image/view
    was not locked before to prevent incorrect use of the API.
    """
    global __images

    assert view in views.VIEWS

    utils.logger.debug("Done " + repr(image) + " " + view)
    did = False
    temp = []
    for i, v, s in __images:
        if i == image:
            if v == view:
                did = True
            else:
                raise Exception("Trying to mark an unexpected view as stopped.")
        else:
            temp.append((i, v, s))
    __images = temp
    if not did:
        raise Exception("Trying to stopped a non-existant view")
