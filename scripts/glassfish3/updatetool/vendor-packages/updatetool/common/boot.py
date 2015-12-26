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


if False:
    import gettext
    _ = gettext.gettext

import info as INFO
import gettext
import sys
import os.path
import locale
from common.fsutils import FSENC

uc_error_set = False
uc_error_msg = ""
uc_error_code = 0
UPDATETOOL_LOCALE = None
__msg_catalog = None

def safe_encode(base_str):
    assert isinstance(base_str, basestring)

    uobj = None
    if isinstance(base_str, unicode):
        uobj = base_str
    else:
        try:
            # Be opportunistic first
            uobj = unicode(base_str, 'utf-8')
        except:
            try:
                uobj = unicode(base_str, FSENC)
            except:
                try:
                    uobj = unicode(base_str, 'utf-8', 'replace')
                except:
                    return repr(uobj)
    return uobj.encode('latin1', 'replace')


def safe_decode(astr):
    assert isinstance(astr, basestring)

    if isinstance(astr, unicode):
        return astr

    try:
        return astr.decode('utf-8')
    except:
        try:
            return astr.decode('utf-8', 'replace')
        except:
            try:
                return astr.decode('utf-8', 'ignore')
            except:
                return astr


# This function is used to generate an error message and exit the application.
# If this is a non-Windows platform (where we have access to stdout/stderr)
# we can generate the error message immediately and exit.  If this is Windows
# then we must generate a dialog and present the error message after WX has
# been initialized.
def uc_error(msg, exit_code):
    """
    This function is used to generate an error message and exit the application.
    If this is a non-Windows platform (where we have access to stdout/stderr)
    we can generate the error message immediately and exit.  If this is Windows
    then we must generate a dialog and present the error message after WX has
    been initialized.
    """

    global uc_error_set
    global uc_error_msg
    global uc_error_code

    # Once an error has been set don't set any more messages.
    if uc_error_set:
        return
    else:
        uc_error_set = True         # the global gets picked up later

    # If this is the Windows platform we don't have stderr/out available.
    # We must present the error message in a dialog after WX has been
    # initialized. For the Mac we are running as a .app and stderr/out goes
    # to system.log, so we use a dialog in this case too.
    #
    if 'wx' in sys.modules and (sys.modules['wx'].Platform == "__WXMSW__" or sys.modules['wx'].Platform == "__WXMAC__" ):
        uc_error_msg = msg          # the global gets picked up later
        uc_error_code = exit_code   # the global gets picked up later
    else:
        if sys.stderr.encoding is None:
            if sys.stdout.encoding is None:
                print >> sys.stderr, msg
            else:
                print >> sys.stderr, msg.encode(sys.stdout.encoding)
        else:
            print >> sys.stderr, msg.encode(sys.stderr.encoding)
        sys.exit(exit_code)

def _set_unix_locale_vars(to_locale):
    # Erase all other locale variables except LANG to get the right behavior
    # from WX in C and other locales. This may get us some undesired behavior
    # when user is mixing these settings but we treat that as an extreme corner
    # case
    for envx in ['LC_ALL', 'LANG', 'LC_CTYPE', 'LC_NUMERIC', 'LC_TIME', 'LC_COLLATE', 'LC_MONETARY', 'LC_MESSAGES', 'LC_ALL']:
        if envx in os.environ:
            del os.environ[envx]
    os.environ['LANG'] = to_locale
    # If LC_ALL is different from LANG (C vs. some bad setting, it causes issues)
    os.environ['LC_ALL'] = to_locale
    return to_locale

# This needs to be done before wx gets imported
def get_locale_dir():
    if 'UPDATETOOL_LOCALEDIR' not in os.environ:
        os.environ['UPDATETOOL_LOCALEDIR'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "locale")
    return os.environ['UPDATETOOL_LOCALEDIR']

def init_app_locale():
    global UPDATETOOL_LOCALE, __msg_catalog

    # Note : 1. Presently it needs to be updated to support more languages
    # Note : 2. Change OnHelp code manually when this is changed as that
    #           does not use this
    # non-utf8 name, messages dir name
    LANG_SUPPORT = {
        'en_US': 'en',
        'de_DE': 'de',
        'es_ES': 'es',
        'fr_FR': 'fr',
        'ja_JP': 'ja',
        'zh_CN': 'zh_CN',
        'zh_TW': 'zh_TW',
        'ko_KR': 'ko_KR',
        'pt_BR': 'pt_BR',
    }

    localedir = get_locale_dir()
    UPDATETOOL_LOCALE = None
    _tried_fallback = False
    try:
        locale_set = locale.setlocale(locale.LC_ALL, '')
        try:
            loc, enc = locale.getdefaultlocale(envvars=('LC_ALL', 'LC_CTYPE', 'LANG', 'LANGUAGE'))
        except ValueError:
            loc = None
            enc = None

        if sys.platform in ['win32']:
            if loc == None and enc == None:
                # TODO: On windows console output is useless but once we have a solution...
                print >> sys.stderr, 'Locale could not be determined. Attempting to use English locale.'
                _tried_fallback = True
                locale.setlocale(locale.LC_ALL, 'en')
                UPDATETOOL_LOCALE = 'en'
                gettext.translation(INFO.CMD_NAME, localedir, languages=[], fallback=True).install(unicode=True)
            else:
                for suploc in LANG_SUPPORT:
                    if loc == suploc or loc == LANG_SUPPORT[suploc]:
                        UPDATETOOL_LOCALE = LANG_SUPPORT[suploc]
                        gettext.translation(INFO.CMD_NAME, localedir, languages=[loc], fallback=True).install(unicode=True)
                        break
            # Windows doesn't do env variables for locale settings
            if not UPDATETOOL_LOCALE:
                # TODO: On windows console output is useless but once we have a solution...
                print >> sys.stderr, 'Locale "%s" with encoding "%s" is not supported.' % (loc, enc)
                print >> sys.stderr, 'Attempting to use English locale.'
                _tried_fallback = True
                locale.setlocale(locale.LC_ALL, 'en')
                UPDATETOOL_LOCALE = 'en'
                gettext.translation(INFO.CMD_NAME, localedir, languages=[], fallback=True).install(unicode=True)
        else:
            UPDATETOOL_LOCALE = None
            if locale_set in ['C', 'POSIX', 'en', 'en_US']:
                UPDATETOOL_LOCALE = _set_unix_locale_vars('en_US.UTF-8')
                gettext.translation(INFO.CMD_NAME, localedir, languages=[], fallback=True).install(unicode=True)
            else:
                for suploc in LANG_SUPPORT:
                    if locale_set == suploc + '.UTF-8':
                        UPDATETOOL_LOCALE = LANG_SUPPORT[suploc]
                        gettext.translation(INFO.CMD_NAME, localedir, languages=[UPDATETOOL_LOCALE], fallback=True).install(unicode=True)
                        break
            if UPDATETOOL_LOCALE is None:
                if loc == None and enc == None:
                    print >> sys.stderr, 'Locale could not be determined. Attempting to use English locale.'
                    _tried_fallback = True
                    UPDATETOOL_LOCALE = _set_unix_locale_vars('en_US.UTF-8')
                    gettext.translation(INFO.CMD_NAME, localedir, languages=[], fallback=True).install(unicode=True)
                elif loc in ['C', 'POSIX', 'en', 'en_US']:
                    # hope for the best since our messages are in english
                    UPDATETOOL_LOCALE = _set_unix_locale_vars('en_US.UTF-8')
                    gettext.translation(INFO.CMD_NAME, localedir, languages=[], fallback=True).install(unicode=True)
                elif enc in ['UTF-8',
                        'UTF8', # python 2.5.1 and newer return this
                        'utf' # python 2.4.4 returns this
                        ]:
                    for suploc in LANG_SUPPORT:
                        if loc == suploc:
                            UPDATETOOL_LOCALE = _set_unix_locale_vars(loc + '.' + 'UTF-8')
                            supdir = LANG_SUPPORT[suploc]
                            gettext.translation(INFO.CMD_NAME, localedir, languages=[supdir], fallback=True).install(unicode=True)
                            break
                    else:
                        # a UTF-8 lang we don't have messages for
                        print >> sys.stderr, '%s does not support running in "%s.%s" locale.' % (INFO.APP_NAME, loc, enc)
                        print >> sys.stderr, 'Attempting to use English locale.'
                        _tried_fallback = True
                        UPDATETOOL_LOCALE = _set_unix_locale_vars('en_US.UTF-8')
                        gettext.translation(INFO.CMD_NAME, localedir, languages=[], fallback=True).install(unicode=True)
                else:
                    # an unsupported lang
                    print >> sys.stderr, '%s does not support running in "%s" encoding for "%s" locale.' % (INFO.APP_NAME, enc, loc)
                    print >> sys.stderr, 'Please set your environment to "%s.UTF-8" and try again.' % (loc)
                    print >> sys.stderr, 'Attempting to use English locale.'
                    _tried_fallback = True
                    UPDATETOOL_LOCALE = _set_unix_locale_vars('en_US.UTF-8')
                    gettext.translation(INFO.CMD_NAME, localedir, languages=[], fallback=True).install(unicode=True)
    except:
        typ, val, tback = sys.exc_info()
        if str(typ) == "locale.Error":
            if not _tried_fallback:
                try:
                    UPDATETOOL_LOCALE = _set_unix_locale_vars('C')
                    gettext.translation(INFO.CMD_NAME, localedir, languages=[], fallback=True).install(unicode=True)
                except:
                    typ, val, tback = sys.exc_info()
                    if str(typ) == "locale.Error" or str(val).startswith('unknown locale'):
                        uc_error("Neither the current locale nor the default could be used.", 1)
                    else:
                        import traceback
                        lst = traceback.format_tb(tback) + traceback.format_exception_only(typ, val)
                        uc_error("Unhandled error: Please report this to %s dev team\n\n%s\n%s\n%-20s %s" % (INFO.APP_NAME, typ, val, "".join(lst[:-1]), lst[-1]), 1)
            else:
                uc_error("Neither the current locale nor the default could be used.", 1)
        else:
            import traceback
            lst = traceback.format_tb(tback) + traceback.format_exception_only(typ, val)
            uc_error("Unhandled error: Please report this to %s dev team\n\n%s\n%s\n%-20s %s" % (INFO.APP_NAME, typ, val, "".join(lst[:-1]), lst[-1]), 1)

    _ = gettext.gettext
    try:
        # XXX : This still fails badly with segfault on bad locales
        import wx
    except:
        typ, val, tback = sys.exc_info()
        if str(typ) == "locale.Error":
            if sys.platform not in ['win32'] and os.environ['LANG'] != 'C':
                UPDATETOOL_LOCALE = _set_unix_locale_vars('C')
                try:
                    import wx
                except:
                    # NOL10N
                    uc_error("The current locale is not supported and we could not fallback to english locale.", 1)
            else:
                # NOL10N
                uc_error("The current locale is not supported and we could not fallback to english locale.", 1)
        else:
            import traceback
            lst = traceback.format_tb(tback) + traceback.format_exception_only(typ, val)
            msgx = _("WX import error.  Verify the WX widgets are in the PYTHONPATH.\nThe following can be reported "\
                    "to %(email)s.\n\nTraceback " \
                    "(innermost last):\n%(tracefirst)-20s %(tracerest)s") % {'email':INFO.REPORT_TO, 'tracefirst': "".join(lst[:-1]), 'tracerest': lst[-1]}
            uc_error(msgx, 1)

    _ = wx.GetTranslation

    if 'unicode' not in wx.PlatformInfo:
        # Can't L10n the next line
        uc_error("You need a unicode build of wxPython to run this application.\nInstalled version: %s\n" % wx.version, 1);

    if wx.Platform == "__WXMAC__": # Issue 767
        wx.SetDefaultPyEncoding("utf-8")

    # HACK : Make plural forms work
    try:
        p = gettext.find(INFO.CMD_NAME, localedir=localedir, languages=[UPDATETOOL_LOCALE])
        if p and os.path.exists(p):
            f = open(p, "rb")
            __msg_catalog = gettext.GNUTranslations(f)
            f.close()
    except:
        pass

def n_(s, p, n):
    global __msg_catalog

    if __msg_catalog is not None:
        return __msg_catalog.ngettext(s, p, n)
    else:
        return gettext.ngettext(s, p, n)

def check_ips():
    try:
        # Check that IPS is installed correctly first
        import common.ips
    except ImportError:
        typ, val, tback = sys.exc_info()
        import traceback
        lst = traceback.format_tb(tback) + traceback.format_exception_only(typ, val)
        msg = _("IPS pkg command is not installed. Please make sure that the client libraries are on the PYTHONPATH " \
                "before executing.\nThe following can be reported to %(email)s.\n\nTraceback " \
                    "(innermost last):\n%(tracefirst)-20s %(tracerest)s") % {'email':INFO.REPORT_TO, 'tracefirst': "".join(lst[:-1]), 'tracerest': lst[-1]}
        uc_error(msg, 1)
