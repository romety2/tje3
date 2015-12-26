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

"""Utility functions used by all other modules"""

from common import info as INFO
from common.boot import safe_encode
from common.fsutils import fsdec

import os.path
import sys
import stat
import traceback
import ConfigParser
import urllib2
import re
import locale
import calendar
import time
import logging.handlers
import codecs
import array
import string

SIZE_UNITS = [
    ('YB' , 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024),
    ('ZB' , 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024),
    ('EB' , 1024 * 1024 * 1024 * 1024 * 1024 * 1024),
    ('PB' , 1024 * 1024 * 1024 * 1024 * 1024),
    ('TB' , 1024 * 1024 * 1024 * 1024),
    ('GB' , 1024 * 1024 * 1024),
    ('MB' , 1024 * 1024),
    ('KB' , 1024),
]

_config_dir = None
host_config_dir = ""
log_file_path = ""
logger = None
enable_tty_logger = False
use_debug_log_level = False

get_icon_cache = {}
get_image_cache = {}
get_scaled_image_cache = {}

import __builtin__
if '_' not in __builtin__.__dict__:
    import gettext
    _ = gettext.gettext

def trace(fn):
    """Decorate a function for debugging its usages with arguments"""

    from itertools import chain

    def wrapped(*args, **kwargs):
        name = fn.__name__
        print "%s(%s)" % (name, ", ".join(map(repr, chain(args, kwargs.values()))))
        wrapped.__doc__ = fn.__doc__
        wrapped.__module__ = fn.__module__
        wrapped.__name__ = fn.__name__
        wrapped.__dict__.update(fn.__dict__)
        return fn(*args, **kwargs)
    return wrapped


def benchmark(fn):
    """Decorate a function for printing the execution time"""
    def wrapped(*arg, **kwargs):
        start_time = time.time()
        res = fn(*arg, **kwargs)
        end_time = time.time()
        print '%s completed in %0.3f ms' % (fn.func_name, (end_time - start_time) * 1000.0)
        return res
    return wrapped


def format_trace():
    typ, val, tback = sys.exc_info()
    lst = traceback.format_tb(tback) + traceback.format_exception_only(typ, val)
    if 'wx' in sys.modules: # Report wx version only if it got imported sucessfully earlier
        try:
            import wx
        except:
            pass
        _wx_version = wx.VERSION_STRING
        _wx_platform = wx.Platform
    else:
        _wx_platform = _wx_version = u'UNKNOWN'
    _platform = _python_version = u'UNKNOWN'

    # This is most probaly already imported by something so should be pretty safe to import
    if 'platform' in sys.modules:
        try:
            import platform
        except:
            pass
        _platform = platform.platform()
        _python_version = platform.python_version()
    return safe_encode("Application ID: [%s]\nTimestamp     : [%s]\nwx Version    : [%s]\nwx Platform   : [%s]\nPython Version: [%s]\n"\
            "Platform      : [%s]\n\nTraceback (innermost last):\n%-20s %s" % (
                    INFO.APP_FULL_ID,
                    time.strftime(r'%Y-%m-%d %H:%M:%S %Z(%z)'),
                    _wx_version,
                    _wx_platform,
                    _python_version,
                    _platform,
                    safe_encode("".join(lst[:-1])),
                    safe_encode(lst[-1])
                    ))


def get_icon(name):
    """
    Returns icon from the image directory (possible cached)
    """
    import wx
    image_path = os.path.join(os.path.dirname(__file__), "..", "images", name)
    if image_path not in get_icon_cache:
        get_icon_cache[image_path] = wx.Icon(fsdec(image_path), wx.BITMAP_TYPE_ANY)
    return get_icon_cache[image_path]


def get_image(*name):
    """
    Returns image bitmap from the image directory (possible cached)
    """
    import wx
    image_path = os.path.join(os.path.dirname(__file__), "..", "images", *name)
    if image_path not in get_image_cache:
        get_image_cache[image_path] = wx.Image(fsdec(image_path), wx.BITMAP_TYPE_ANY).ConvertToBitmap()
    return get_image_cache[image_path]


def get_image_png(*name):
    """
    Returns image bitmap from the image directory (possible cached) where the image
    is known to be a PNG.
    """
    import wx
    image_path = os.path.join(os.path.dirname(__file__), "..", "images", *name)
    if image_path not in get_image_cache:
        get_image_cache[image_path] = wx.Image(fsdec(image_path), wx.BITMAP_TYPE_PNG)
    return get_image_cache[image_path]


def get_scaled_image(name, width, height):
    """
    Returns scaled image bitmap from the image directory (possible cached)
    """
    import wx
    image_path = os.path.join(os.path.dirname(__file__), "..", "images", name)
    img = wx.Image(fsdec(image_path), wx.BITMAP_TYPE_ANY)
    img.Rescale(width, height)
    tup = (image_path, width, height)
    if tup not in get_scaled_image_cache:
        get_scaled_image_cache[tup] = img.ConvertToBitmap()
    return get_scaled_image_cache[tup]


def create_checkbox_bitmap(window, flag=0, size=(16, 16)):
    """
    Returns a bitmap of the checkbox control.
    flag must be either wx.CONTROL_CHECKED to get the checked image
    or 0 to get the unchecked image
    """
    import wx
    global _cached_checkbox

    bmp = wx.EmptyBitmap(*size)
    dc = wx.MemoryDC(bmp)
    dc.Clear()
    wx.RendererNative.Get().DrawCheckBox(window, dc,
                                         (0, 0, size[0], size[1]), flag)
    dc.SelectObject(wx.NullBitmap)
    return bmp


def create_radiobutton_bitmap(window, flag=0, size=(16, 16)):
    """
    Returns a bitmap of the checkbox control.
    flag must be either wx.CONTROL_CHECKED to get the checked image
    or 0 to get the unchecked image
    """
    import wx
    bmp = wx.EmptyBitmap(*size)
    dc = wx.MemoryDC(bmp)
    dc.Clear()
    wx.RendererNative.Get().DrawRadioButton(window, dc,
                                         (0, 0, size[0], size[1]), flag)

    # Bug 859: On Windows, when using the "Classic" theme the radio
    # button does not render (may be a WX bug). So we check for that
    # case and use a checkbox instead
    if wx.Platform == "__WXMSW__" and bitmap_is_blank(dc, size):
        wx.RendererNative.Get().DrawCheckBox(window, dc,
                                         (0, 0, size[0], size[1]), flag)
    dc.SelectObject(wx.NullBitmap)
    return bmp


def bitmap_is_blank(dc, size):
    """
    Check to see if a bitmap is blank, where blank means consisting of
    pixels of all the same color. This routine is expensive.
    """
    # Pick a pixel, any pixel
    pixel = dc.GetPixel(0, 0)

    # See if all pixels in the bitmap match that pixel
    for x in range(0, size[0] - 1):
        for y in range(0, size[1] -1):
            if dc.GetPixel(x, y) != pixel:
                return False
    return True


def make_bold(label):
    import wx
    font = label.GetFont()
    font.SetWeight(wx.FONTWEIGHT_BOLD)
    label.SetFont(font)


def make_subtle_bold(label):
    import wx
    font = label.GetFont()
    font.SetWeight(wx.FONTWEIGHT_BOLD)
    label.SetFont(font)
    label.SetForegroundColour(wx.Colour(70, 70, 70))


def make_bigger(label, points = 2):
    font = label.GetFont()
    point_size = font.GetPointSize()
    font.SetPointSize(point_size + points)
    label.SetFont(font)


def get_line_height(window):
    """
    Returns the height of a text line for the default font for the
    specified window.
    """
    import wx
    dc = wx.ClientDC(window)
    (w, h) = dc.GetTextExtent("Xy")
    del dc
    return h


def shift_checkbox_bitmap(window, bitmap, shift_n, flag):
    """
    Updates the passed bitmap with a checkbox image that is shifted
    up by shift_n pixels. The checked state of the checkbox is
    specified by flag which can be wx.CONTROL_CHECKED or 0
    """
    import wx
    # We render the checkbox in a larger bitmap, then blit it
    # into the original bitmap shifted up
    width = bitmap.GetWidth()
    height = bitmap.GetHeight()
    size = (width, height + shift_n)
    tmp_bmp = create_checkbox_bitmap(window, flag, size)
    tmp_dc = wx.MemoryDC(tmp_bmp)

    dc  = wx.MemoryDC(bitmap)
    dc.Blit(0, 0, width, height, tmp_dc, 0, shift_n)
    tmp_dc.SelectObject(wx.NullBitmap)
    dc.SelectObject(wx.NullBitmap)
    return bitmap

def is_integer_string(s):
    try:
        int(s)
        return True
    except:
        pass
    return False

def readable_size(bytes):
    """
    Converts size in bytes to human readable size.

    It tries to convert to a locale appropriate representation. Otherwise it
    falls back to a safer representation without unicode representation issues.
    """

    if bytes < 0:
        neg = -1
    else:
        neg = 1
    absbytes = abs(bytes)
    for unit in SIZE_UNITS:
        if absbytes >= unit[1]:
            try:
                return "%s %s" % (locale.format(u"%0.1f",  neg * float(absbytes)/float(unit[1]), True), unit[0])
            except UnicodeDecodeError:
                # The locale support had issues. Return something safe and universal
                return "%0.1f %s" % (neg * float(absbytes)/float(unit[1]), unit[0])
    try:
        return "%s B" % locale.format(u"%d",  bytes, True)
    except UnicodeDecodeError:
        # The locale support had issues. Return something safe and universal
        return "%d B" % bytes


def get_config_parser(cpath):
    """Creates and returns ConfigParser.SafeConfigParser()"""
    try:
        conf_parser = ConfigParser.ConfigParser()
        prefs_file = codecs.open(cpath, "r", 'utf-8')
        conf_parser.readfp(prefs_file)
        prefs_file.close()
        return conf_parser
    except:
        return None


def to_unicode(obj, encoding=None):
    """Use as early as possible e.g. just after reading from file"""
    if isinstance(obj, basestring) and not isinstance(obj, unicode):
        try:
            if encoding is None:
                enc = 'utf-8'
            else:
                enc = encoding
            return unicode(obj, enc)
        except:
            logger.warn("Could not encode '%s'" % `obj`)
    return obj


def natural_sort(lst):
    return sorted(lst, key=lambda strng: [map(int, part[1::2]) for part in re.split(r'(\d+)', strng)])


def display_about(parent):
    import wx
    from wx.lib.wordwrap import wordwrap

    description = wordwrap(_(
        "\n%(APP_NAME)s is a multi-platform, network repository based tool "
        "that helps you manage software installations layered on top of your existing "
        "operating system.  The tool enables you to easily add, update and remove "
        "components.  The built-in desktop notification feature helps keep "
        "you aware of available updates."

        "\n\n%(APP_NAME)s leverages the Image Packaging System (IPS) technology "
        "from OpenSolaris.org to provide an efficient and robust means of "
        "managing software installations."

        "\n\nUse is subject to license terms.") % {'APP_NAME':INFO.APP_NAME},
        350, wx.ClientDC(parent))

    about = wx.AboutDialogInfo()
    about.SetName(INFO.APP_NAME)
    about.SetVersion("%(VERSION)s %(RELEASE_NAME)s (Build %(MILESTONE)s.%(REVISION)s)" % {
    'VERSION':INFO.VERSION, 'RELEASE_NAME':INFO.RELEASE_NAME, 'MILESTONE':INFO.MILESTONE, 'REVISION': INFO.REVISION})
    about.SetDescription(description)
    about.SetIcon(get_icon("application-update-tool-48x48.png"))
    about.SetWebSite(INFO.WEBSITE_URL)
    about.SetCopyright(INFO.COPYRIGHT)

    wx.AboutBox(about)


def set_net_proxy(config):
    try:
        if config.getboolean('network', 'proxy.required'):
            host = config.get('network', 'proxy.host')
            port = config.get('network', 'proxy.port')
            if config.has_option('network', 'proxy.https.host') and \
               config.has_option('network','proxy.https.port'):
                https_host = config.get('network', 'proxy.https.host')
                https_port = config.get('network', 'proxy.https.port')
            else:
                https_host = ""
                https_port = ""
            if config.getboolean('network', 'proxy.auth'):
                if config.has_option('network', 'proxy.username') and \
                   config.has_option('network','proxy.password'):
                    user = config.get('network', 'proxy.username')
                    passwd = config.get('network', 'proxy.password')
                    proxy = 'http://%s:%s@%s:%s' % (user, passwd, host, port)
                    if https_host and https_port:
                        proxy_https = 'https://%s:%s@%s:%s' % (user, passwd, https_host, https_port)
                elif os.getenv("HTTP_PROXY_USERNAME") and \
                   os.getenv("HTTP_PROXY_PASSWORD"):
                    user = os.getenv("HTTP_PROXY_USERNAME")
                    passwd = os.getenv("HTTP_PROXY_PASSWORD")
                    proxy = 'http://%s:%s@%s:%s' % (user, passwd, host, port)
                    if https_host and https_port:
                        proxy_https = 'https://%s:%s@%s:%s' % (user, passwd, https_host, https_port)
                else:
                    proxy = 'http://%s:%s' % (host, port) # Use as a temporary measure
                    if https_host and https_port:
                        proxy_https = 'https://%s:%s' % (https_host, https_port) # Use as a temporary measure
                    logger.warning(_("Incomplete proxy configuraion in preferences. Proxy user name or password is missing."))
            else:
                proxy = 'http://%s:%s' % (host, port)
                if https_host and https_port:
                    proxy_https = 'https://%s:%s' % (https_host, https_port) # Use as a temporary measure
            os.environ['HTTP_PROXY'] = os.environ['http_proxy'] =  proxy
            os.environ['FTP_PROXY'] = os.environ['ftp_proxy'] =  proxy
            if https_host and https_port:
                os.environ['HTTPS_PROXY'] = os.environ['https_proxy'] =  proxy_https
            if config.has_option('network', 'proxy.no_proxy_list'):
                os.environ['no_proxy'] = os.environ['NO_PROXY'] =  config.get('network', 'proxy.no_proxy_list')
            else:
                # put localhost in no_proxy if it isn't already set to preserve old pkg(5) behavior
                if not 'no_proxy' in os.environ:
                    if 'NO_PROXY' in os.environ:
                        os.environ['no_proxy'] = os.environ['NO_PROXY']
                    else:
                        os.environ['no_proxy'] = os.environ['NO_PROXY'] = 'localhost,127.0.0.0/8'
                os.environ['NO_PROXY'] = os.environ['no_proxy']
            # urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler({'http' : proxy})))
            urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler()))
        else:
            for setting in ['http_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'https_proxy', 'ftp_proxy', 'FTP_PROXY', 'NO_PROXY', 'no_proxy']:
                if setting in os.environ:
                    del os.environ[setting]

            urllib2.install_opener(urllib2.build_opener())
    except:
        # TODO: Have proper handling of this
        logger.error(format_trace())
        logger.error(_("Proxy could not be configured. Please report to development team at %(REPORT_TO)s") % {
            'REPORT_TO':INFO.REPORT_TO})
        urllib2.install_opener(urllib2.build_opener())


def method_name():
    """
    Returns the current method name
    """
    return sys._getframe(1).f_code.co_name


def calling_method_name():
    """
    Returns the calling methods name
    """
    return sys._getframe(2).f_code.co_name


def create_logger(config, log_path=""):
    global log_file_path
    global logger

    try:
        if log_path == "":
            log_file_path = config.get('logging', 'file.path')
        else:
            log_file_path = log_path

        if log_file_path == "":
            log_file_path = os.path.join(host_config_dir, "updatetool.log")
        try:
            max_bytes = config.getint('logging', 'file.max_bytes')
        except:
            max_bytes = 5 * 1024 * 1024
        try:
            backup_count = config.getint('logging', 'file.backup_count')
        except:
            backup_count = 7

        try:
            console_enable = config.getboolean('logging', 'console.enable')
        except:
            console_enable = False

        levels = {
            'CRITICAL' : logging.CRITICAL,
            'ERROR'    : logging.ERROR,
            'WARNING'  : logging.WARNING,
            'INFO'     : logging.INFO,
            'DEBUG'    : logging.DEBUG,
            'NOTSET'   : logging.NOTSET
        }

        try:
            log_level = levels[config.get('logging', 'log_level')]
        except:
            log_level = logging.INFO

        # Override these values with what came in via the command line
        if enable_tty_logger == True:
            console_enable = True
        if use_debug_log_level == True:
            log_level = logging.DEBUG

        logger = _create_logger(console_enable = console_enable,
                         log_level = log_level,
                         path = log_file_path,
                         max_bytes = max_bytes,
                         backup_count = backup_count)

    except Exception, e:
        # Failure creating logger. Use the basic logger as a falllback
        logging.basicConfig()
        logger = logging.getLogger('')
        logger.setLevel(logging.INFO)
        logger.error("Could not create logger: %s. Using basic configuration.", e)

    return logger


def _create_logger(console_enable=False,
                 log_level=logging.INFO,
                 path="log.txt",
                 max_bytes=10 * 1024 * 1024,
                 backup_count=7):

    # Top level logger will pass everything to the handlers. Handlers
    # will then throttle to log level
    formatter=logging.Formatter('%(asctime)s %(levelname)-7.7s %(message)s', '%Y-%m-%d %H:%M:%S')

    rootlogger = logging.getLogger('')
    rootlogger.setLevel(logging.NOTSET)

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(formatter)
    if console_enable:
        rootlogger.addHandler(console)

    # Logfile handler
    try:
        logfile = logging.handlers.RotatingFileHandler(path, mode='a',
                            maxBytes=max_bytes, backupCount=backup_count)
        logfile.setLevel(log_level)
        logfile.setFormatter(formatter)
        rootlogger.addHandler(logfile)
    except Exception, e:
        # Couldn't create logfile handler. Ensure output goes someplace
        if not console_enable: # if not already added
            rootlogger.addHandler(console)
        rootlogger.error("Could not create log file handler: %s. Sending ouput to console.", e)

    return rootlogger


def disable_keyboard_interrupt():
    """
    Sets the response to a SIGINT (keyboard interrupt) to ignore.
    """
    import signal
    return signal.signal(signal.SIGINT,signal.SIG_IGN)


def enable_keyboard_interrupt():
    """
    Sets the response to a SIGINT (keyboard interrupt) to the
    default (raise KeyboardInterrupt).
    """
    import signal
    return signal.signal(signal.SIGINT, signal.default_int_handler)


def get_config_dir():
    """
    Returns the config directory.  If the UID is 0 then we force the config
    dir to be relative to ~root.  See issue 729 for details.
    """

    import os
    import wx

    # Cache _config_dir value in a global
    global _config_dir

    if _config_dir is not None:
        return _config_dir

    if wx.Platform == "__WXMSW__" or os.geteuid() != 0:
        _config_dir = os.path.join(wx.StandardPaths_Get().GetUserDataDir())
    else:
        import pwd
        if wx.Platform != "__WXMAC__":
            _config_dir = os.path.join(pwd.getpwuid(os.geteuid())[5], "." + wx.GetApp().GetAppName())
        else:
            _config_dir = os.path.join(pwd.getpwuid(os.geteuid())[5], "/Library/Application Support/" + wx.GetApp().GetAppName())

    return _config_dir


def log_system_information():
    import platform
    logger.info("==================================================")
    info="%(APP_NAME)s %(VERSION)s (Build %(MILESTONE)s.%(REVISION)s)" % {
            'APP_NAME':INFO.APP_NAME, 'VERSION':INFO.VERSION, 'MILESTONE':INFO.MILESTONE, 'REVISION':INFO.REVISION }
    logger.info(info)
    logger.info(platform.platform())
    wxversion="(unknown)"
    if 'wx' in sys.modules:
        import wx
        wxversion=wx.VERSION_STRING
    info="Python %s wxPython %s" % (platform.python_version(), wxversion)
    logger.info(info)
    logger.info("Log file location: %s", log_file_path)
    return


def format_version(version):
    """
    Helper method to avoid weird G11n related to string interpolation
    issues by concatenating the strings instead
    """
    if version.branch:
        return str(version.release) + "-" + str(version.branch)
    else:
        return str(version.release)


def parse_bool(s):
    """
    Convert a string representation of a boolean into a Boolean.
    "T", "t", "1", "true", and any mixed-cap variant of "true" are True
    Any other string value is False

    If s happens to be the Boolean True of False then that value is simply
    returned.
    """
    if s is True or s is False:
        return s
    s = str(s).strip().lower()
    return s in ['true', 't', '1']


def expand_path_tokens(path):
    '''
    Expand any tokens in path and return the resulting path.
    Currently the only token supported is:
        {HOME}
    which is expanded to the user's home directory
    '''
    if path is None or len(path) <= 0:
        return path

    if path.find("{HOME}") > -1:
        home = get_home()
        if home is None:
            logger.warning(_("Unable to expand %s: Could not determine user's home directory." % path))
            home = "."
        path = path.replace("{HOME}", home)

    return os.path.realpath(path)


def get_home():
    # BUG : This does not work on Windows systems where the user has changed
    # the home location via the
    #
    #  HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders\Personal
    #
    # key. HOMEPATH does not reflect this change. This needs to be replaced with code
    # equivalent to
    #
    # regtool get '\HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders\Personal'
    #
    import wx
    if wx.Platform == "__WXMSW__":
        path = os.path.join(os.environ.get("HOMEDRIVE"),
                            os.environ.get("HOMEPATH"))
        return path
    else:
        return os.environ.get("HOME")


def toggle_debug_child_focus(w, ignoreme=[]):
    """
    Use toggle_debug_child_focus(self)
    """
    import wx

    if ignoreme:
        ignoreme.pop()
        w.Unbind(wx.EVT_CHILD_FOCUS)
    else:
        ignoreme.append(1)
        def OnChildFocus(event):
            logger.debug(event.GetWindow())
            event.Skip()

        w.Bind(wx.EVT_CHILD_FOCUS, OnChildFocus)


def protect_unicode(str, guard=":"):
    '''
    WARNING! This method may added characters to the passed string,
    so use it only on free form strings intended for consumption by
    humans (like titles, descriptions, etc). Do not use if for
    anything with a structured syntax (paths)

    With some python runtimes string.strip() is overly agressive
    at stripping what it thinks is unicode whitespace from a UTF-8
    encoded string. This can then lead to UTF-8 decode errors when
    the string is decoded. We've run into this when loading data
    from property files. For details see:

    https://updatecenter2.dev.java.net/issues/show_bug.cgi?id=1458

    This method checks to see if the string, when encoded in UTF-8,
    ends in a whitespace that contains non-ASCII. If it does it will
    append a ":" so string.strip() won't corrupt the string. Yes, this
    is a gross hack.
    '''

    if str is None or len(str) == 0:
        return str

    # Convert string to UTF-8
    ustr = str.encode("utf-8")

    # In some situations string.strip() behaves as though "\xa0" and
    # "\x85" are whitespace. Unfortunately string.whitespace does not
    # reliably reflect this, so we assume the worse
    whitespace = string.whitespace + "\xa0\x85"

    # If last byte is not considered whitespace then all is good
    if ustr[-1] not in whitespace:
        return str

    # Convert string into an array of bytes
    a = array.array('B')
    a.fromstring(ustr)

    # Convert whitespace string into bytes so we can easily compare
    whitespace_bytes = array.array('B')
    whitespace_bytes.fromstring(whitespace)

    # The string ends in whitespace. If any of that trailing whitespace
    # is non-ascii then we need to protect. Scan string byte array backwards
    r = range(len(a))
    r.reverse()
    n = 0
    for i in r:
        if a[i] in whitespace_bytes:
            if a[i] < 128:
                # ASCII whitespace, keep scanning
                n = n + 1
                continue
            else:
                # Non-ASCII whitespace, need to protect. Append a guard char
                # we go ahead and trim trailing ascii whitespace here.
                if n > 0:
                    return str[0:-n] + guard
                else:
                    return str + guard
        else:
            # Non whitespace byte. Done with scan.
            break

    # None of the trailing white space is non-ascii so just return string
    return str


def find_names(obj):
    import gc, sys

    frame = sys._getframe()
    for frame in iter(lambda: frame.f_back, None):
        frame.f_locals

    result = []
    for referer in gc.get_referrers(obj):
        if isinstance(referer, dict):
            for k, v in referer.iteritems():
                if v is obj:
                    result.append(k)
    return result


def rotate_file(p, max_size=5 * 1024 * 1024, backup_count=1):
    """
    Optimistically rotates a fize based on specified max size and backup count.
    Based on python's RotatingFileHandler.
    """
    try:
        if backup_count > 0 and os.path.exists(p) and os.stat(p)[stat.ST_SIZE] > max_size:
            for i in range(backup_count -1, 0, -1):
                sfn = "%s.%d" % (p, i)
                dfn = "%s.%d" % (p, i + 1)
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = p + ".1"
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(p, dfn)
    except Exception, e:
        pass


def time_to_timestamp(t):
        """convert seconds since epoch to %Y%m%dT%H%M%SZ format"""
        return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(t))


def timestamp_to_time(ts):
        """convert %Y%m%dT%H%M%SZ format to seconds since epoch"""
        return calendar.timegm(time.strptime(ts, "%Y%m%dT%H%M%SZ"))


def is_v0_image(apath):
    """  
    Returns whether a path apath is a v0 format image. Checks for the presence of

        apath/.org.opensolaris,pkg

    and absence of

        apath/.org.opensolaris,pkg/publisher

    directory as the sole criteria.

    @param apath: fsenc(unicode)'ed path.
    @rtype: C{str}  

    @return: True or False
    """  
    try:
        spath = apath.strip()

        if os.path.exists(spath) and \
                os.path.isdir(os.path.join(spath, ".org.opensolaris,pkg")) and \
		not os.path.exists(os.path.join(spath, ".org.opensolaris,pkg", "publisher")):
            return True
    except:
        logger.error(format_trace())
          
    return False
 
 
def is_v1_image(apath):
    """
    Returns whether a path apath is a v1 format image. Checks for presence of
      
        apath/.org.opensolaris,pkg/publisher
 
    directory as the sole criteria.
 
    @param apath: fsenc(unicode)'ed path.
    @rtype: C{str}
 
    @return: True or False
    """
    try:
        spath = apath.strip()
 
        if os.path.exists(spath) and os.path.isdir(os.path.join(spath, ".org.opensolaris,pkg", "publisher")):
            return True
    except:
        logger.error(format_trace())
          
    return False


def get_version():
    """
    Locates and load the version string from the version file located
    in the image directory.
    """
 
    # We use a couple of different methods to find the version file.
    try:
        # Relative to this file.
        version_path = os.path.join(
                         os.path.dirname(__file__), "..", "..", "..",
                         "lib", "version")
 
        if not os.path.exists(version_path):
            # Relative to the python runtime
            version_path = os.path.join(
                         os.path.dirname(sys.executable), "..", "..", "..",
                         "updatetool", "lib", "version")
 
            if not os.path.exists(version_path):
                return '0'
 
        f = open(version_path, "r")
        version = f.readline()
        f.close()
 
        if version == "":
            return '0'
 
        return version.strip()
 
    except IOError, e:
        utils.logger.error("IOError opening %s. Errno: %s", version_path, str(e[0]))
 
    return '0'
