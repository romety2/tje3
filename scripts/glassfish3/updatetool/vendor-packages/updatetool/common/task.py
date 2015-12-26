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

import wx.lib.newevent
import thread
import time

from common.exception import TaskInterruptedError

(FinishedEvent, EVT_TASK_FINISHED) = wx.lib.newevent.NewEvent()
(DurationChangeEvent, EVT_TASK_DURATION_CHANGED) = wx.lib.newevent.NewEvent()
(ProgressStartEvent, EVT_TASK_PROGRESS_START) = wx.lib.newevent.NewEvent()
(ProgressEvent, EVT_TASK_PROGRESS) = wx.lib.newevent.NewEvent()
(CancelEnableEvent, EVT_CANCEL_ABILITY_CHANGE) = wx.lib.newevent.NewEvent()
(LoggingEvent, EVT_TASK_LOG) = wx.lib.newevent.NewEvent()

TASK_END_NONE        = 0
TASK_END_SUCCESS     = 1
TASK_END_USER_ABORT  = 2
TASK_END_EXCEPTION   = 3

class ThreadedTask(object):
    """
    Implements a Threaded Task
    """

    _ = wx.GetTranslation

    def __init__(self):
        self.running_flag = False
        self.interrupt_flag = False
        self.is_interruptable = False
        self.status = _("Waiting...")
        self.count_done = 0
        self.start_time = 0
        self.result = (TASK_END_NONE, None)


    def start(self):
        self.interrupt_flag = False
        self.running_flag = True
        self.start_time = time.time()
        self.status = _("Started...")
        thread.start_new_thread(self.Run, ())


    def Run(self):
        """
        This is meant to be overridden by the task overriding this class. The
        overriding task must call task_started, task_progress and task_finished
        at various stages. It should also call check_for_interrupt() which raise
        an exception if the user wanted the process interrupted.
        """
        #self.task_started(duration)
        #self.task_progress("foo", completed_units)
        #self.task_finished()
        assert False

    def interrupt(self):
        if self.is_interruptable:
            self.interrupt_flag = True


    def is_running(self):
        return self.running_flag


    def check_for_interrupt(self):
        if self.is_interruptable and self.interrupt_flag:
            self.running_flag = False
            raise TaskInterruptedError(_("User abort"))


    def task_started(self, duration):
        self.duration = duration
        self.post_event(ProgressStartEvent(duration=duration))


    def enable_cancel(self, enable=True):
        self.is_interruptable = True
        self.post_event(CancelEnableEvent(enable=enable))


    def task_progress(self, msg, count_done=0, sequence=0, id=-1):
        self.status = msg
        self.count_done = count_done
        self.post_event(ProgressEvent(count=count_done, sequence=sequence, id=id))


    def task_log(self, msg, id=-1):
        self.status = msg
        self.post_event(LoggingEvent(msg=msg, id=id))


    def set_duration(self, duration):
        self.duration = duration
        self.post_event(DurationChangeEvent(duration=duration))


    def get_remaining_time(self):
        # TODO : Do running avergage or something
        elapsed = (time.time() - self.start_time)
        try:
            remaining = float(elapsed) * float(self.duration  - self.count_done) / float(self.count_done)
        except ZeroDivisionError:
            remaining = 1.0
        minutes = int(remaining / 60.0)
        seconds = int(remaining % 60.0)
        return _("%(minutes)i:%(seconds)02i") % {'minutes':minutes, 'seconds':seconds}


    def get_elapsed_time(self):
        elapsed = (time.time() - self.start_time)
        minutes = int(elapsed / 60.0)
        seconds = int(elapsed % 60.0)
        return _("%(minutes)i:%(seconds)02i") % {'minutes':minutes, 'seconds':seconds}


    def _task_done(self, result):
        self.running_flag = False
        self.result = result
        self.post_event(FinishedEvent())


    def task_finished(self):
        self._task_done((TASK_END_SUCCESS, None))


    def task_cancelled(self, reason):
        self._task_done(reason)


    def set_progress_dialog(self, dlg):
        self.dlg = dlg


    def post_event(self, event):
        if hasattr(self, "dlg") and self.dlg:
            wx.PostEvent(self.dlg, event)


    def get_result(self):
        return self.result


    def __str__(self):
        """ The progress dialog expects the task to describe its current state."""
        return self.status
