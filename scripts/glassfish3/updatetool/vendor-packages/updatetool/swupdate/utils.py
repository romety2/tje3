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

from common.boot import safe_decode
import os
import httplib
import common.utils as utl
from common.fsutils import fsenc
from common import ips
from pkg.client.api_errors import CatalogRefreshException, InvalidDepotResponseException


def create_image(path, title, desc, pubs, opname="image-create"):
    """
    Create a new pkg(5) based image using the supplied parameters.  Catches
    all exceptions.
    pubs is a list of publishers where each publisher is a tuple:
       (Name, Origin (url), Preferred (bool), ssl_key, ssl_cert, Disabled (bool)    Returns None on success
            msg on failure
    """


    _encode_publishers(pubs)

    preferred_pub_name, preferred_pub_url, \
    preferred_ssl_key, preferred_ssl_cert = \
            [(x, y, k, c) for x, y, z, k, c, dummy_a in pubs if z][0]


    path = os.path.expanduser(path)

    try:
        ips.create_image(fsenc(path), title, preferred_pub_name,
                         preferred_pub_url, ssl_key=preferred_ssl_key,
                         ssl_cert=preferred_ssl_cert, opname=opname)
    except OSError, e:
        msg = _("Can not create image.\n\nReason: %s") % e.args[1]
        return msg
    except RuntimeError, failures:
        (remote, error_strs) = ips.extract_catalog_retrieval_errors(failures)
        if error_strs:
            emsg = u"\n\n".join(safe_decode(x) for x in error_strs)
            if remote:
                msg = ("Can not create image. Please make sure the remote " \
                       "repository is accessible.\n\n%s") % emsg
            else:
                msg = _("Could not create image.\n\n%s") % emsg
        else:
            msg = _("Runtime error creating image.")
            utl.logger.error("Runtime error creating image.")
            utl.logger.error(utl.format_trace())
        return msg
    except httplib.HTTPException, msg:
        msg = _("Can not create image.\n\nReason: %s") % msg
        return msg
    except InvalidDepotResponseException, msg:
        msg = _("Can not create image.\n\nReason: %s") % msg
        return msg
    except CatalogRefreshException:
        msg = _("Can not create image.\n\nReason: Unable to download the image catalog.")
        ips.set_image_title(path, title, opname=opname)
        return msg
    except:
        msg = _("Error creating image.\nSee log file for additional details.")
        utl.logger.error("Generic exception while creating image.")
        utl.logger.error(utl.format_trace())
        return msg

    ips.set_image_description(fsenc(path), desc, opname=opname)
    ret, res = ips.set_publishers(fsenc(path), pubs, opname=opname)

    if not ret:
        utl.logger.error("Could not assign all publishers to the image: " + path)
        utl.logger.error(utl.format_trace())


    return None


def _encode_publishers(pubs):
    '''
    Make sure publisher name (prefix) is filesystem encoded
    '''
    for p in pubs:
        p[0] = fsenc(p[0])
