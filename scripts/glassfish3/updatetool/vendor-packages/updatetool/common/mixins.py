#!/usr/bin/env python
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

class KeywordArgsMixin(object):
    """
    A mixin to ease the parsing and handling of keyword arguments.
    """
    def __init__(self):
        pass


    def kwset(self, dikt, kword, default=None, required=False):
        if required and kword not in dikt:
            raise Exception(kword + " is a required keyword argument for " + str(self.__class__))
        selfvar = '_' + kword
        if kword in dikt:
            self.__dict__[selfvar] = dikt[kword]
            del dikt[kword]
        else:
            self.__dict__[selfvar] = default
        del selfvar

if __name__ == '__main__':
    class WantsFoo(KeywordArgsMixin):
        def __init__(self, *args, **kwargs):
            KeywordArgsMixin.__init__(self)

            # Easy
            self.kwset(kwargs, 'foo', required=True)

        def hello(self):
            print self._foo

    a = WantsFoo(foo='Hello world!')
    a.hello()

    try:
        b = WantsFoo()
        print "Test Failed"
    except: # It wanted a foo we didn't supply
        print "Test passed"
