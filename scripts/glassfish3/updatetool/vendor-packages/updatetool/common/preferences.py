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

import codecs
import types
import sys

import os.path
import ConfigParser
from common.exception import ConfigurationSaveError

import common.utils as utils

import __builtin__
if '_' not in __builtin__.__dict__:
    import gettext
    _ = gettext.gettext

# Current list of supported properties:
#
#  Preference Name              Type            Description
#  ---------------              ----            -----------
#  main:
#  preferences.version          String          Preferences version
#  optin.update.notification    True/False      Check for updatea allowed?
#  image_list                   String          List of known IPS images
#                                               separated by \n
#  _last_active_image           String          Private: Last open image in the GUI
#  ad.feed.url                  String          URL to ad pages.  Overrides
#                                               internal URL.
#
#  network:
#  proxy.required               True/False      A Proxy is required
#  proxy.ssl_use_http           True/False      Same Proxy for SSL.
#  proxy.auth                   True/False      Authentication required for Proxy.
#  proxy.host                   String          Host name of proxy
#  proxy.port                   Int             Port number of proxy
#  proxy.https.host             String          Host name of https proxy
#  proxy.https.port             Int             Port number of https proxy
#  proxy.no_proxy_list          String          Hosts/IPs/Domains that do
#                                               not require a proxy
#
#  notifier:
#  check_frequency              never/daily/weekly/monthly/testing
#                                               Establishes how often we
#                                               check for new updates
#  display_seconds                              When updates are available
#                                               indicates how long to display
#                                               the notification balloon.
#                               -1              Until user dismisses
#                                0              Don't display at all
#                               >0              # of seconds to display
#  check_at_start               True/False      Indicates if the notifier
#                                               should perform an initial
#                                               update check at launch.
#  _last_update_check_time      time            Private: last time an
#                                               update check was performed
#  _last_update_check_type      frequency       Private: The update
#                                               frequency that was in
#                                               affect during the last check.
#  _swu_restart_time            time            Private: Indicates the time
#                                               when the user chose to 
#                                               restart the notifier/SWU.
#  _reset_check_frequency       True/False      If freq has been reset.  See
#                                               UC issue 2179. 
#
#  Properties are loaded from defaults.cfg from a directory based on
#  wx.StandardPaths_Get().GetUserDataDir().
#  On Windows this is \Documents and Settings\Admin\Application Data\updatetool
#
#  The module defines DEFAULT_PROPS which contains defaults for
#  a subset of the properties.  These defaults will be used if not
#  overridden by the user's prop file.
#

INITFILE = "init.cfg"
MAX_RECENT_ITEMS = 100

# Dictionary: <section> => <property name> => (<property value>, <property type>, ['upper'])
# The last param 'upper' is optional and valid only for list types. If not specified, a lowercase
# conversion is performed automatically.
DEFAULT_PROPS = {
        "main": {
            "preferences.version": (
                "0.1", str,
                ),
            "image_list": (
                "", str,
                ),
            "_last_active_image": (
                "", str,
                ),
            "optin.update.notification": (
                "True", bool,
                ),
            "featured.feed.url": (
                "", "url",
                ),
            "ad.feed.url": (
                "", "url",
                ),
            "maximum_recent_items": (
                "3", lambda x: x == 'None' or (x.isdigit() and 1 <= int(x) <= MAX_RECENT_ITEMS),
                ),
            },
        "network": {
            "proxy.required": (
                "False", bool,
                ),
            "proxy.auth": (
                "False", bool,
                ),
            "proxy.ssl_use_http": (
                "False", bool,
                ),
            },
        "notifier" : {
            "check_frequency": (
                "weekly", ['daily', 'never', 'weekly', 'monthly', 'testing']
                ),
            "check_at_start": (
                "False", bool,
                ),
            "_last_update_check_time": (
                "0", float,
                ),
            "_last_update_check_type": (
                "weekly", ['daily', 'never', 'weekly', 'monthly', 'testing']
                ),
            "display_seconds": (
                "-1", int,
                ),
            "_swu_restart_time": (
                "0", float,
                ),
            },
        "logging" : {
                "file.path": (
                    "", str,
                    ),
                "file.max_bytes": (
                    "2621440", int,
                    ),
                "file.backup_count": (
                    "4", int,
                    ),
                "console.enable": (
                    "False", bool,
                    ),
                "log_level": (
                    "INFO",
                    ['INFO', 'CRITICAL', 'ERROR', 'WARNING', 'DEBUG', 'NOTSET'],
                    'upper'
                    ),
                },
        }


class Preferences(ConfigParser.SafeConfigParser):

    def __init__(self, config_file_path):
        ConfigParser.SafeConfigParser.__init__(self)
        self._config_path = config_file_path

        self.load_config()


    def load_config(self):
        """
        Load user's perferences and combine them with the defaults.
        """
        _user_props = None

        if os.path.exists(self._config_path):
            # Configuration exists

            try:
                # Load user's props into a ConfigParser
                prefs_file = codecs.open(self._config_path, "r", 'utf-8')
                _user_props = ConfigParser.ConfigParser()
                _user_props.readfp(prefs_file)
                prefs_file.close()
            except IOError, e:
                # Can't load user's props so we'll just load the defaults.
                _user_props = None
                utils.logger.error("Could not load preferences file: %s. IOError: %s", self._config_path, str(e))

        # If an init.cfg file exists (created by the bootstrapper) we merge
        # it with the user's props.  If no user props exists then the init.cfg
        # becomes the user's props.  After the merge the init.cfg is removed.
        _user_props, merged = self.merge_init_props(_user_props, INITFILE)

        self.load_defaults()

        # If the user's props were loaded then combine them with the defaults
        if _user_props:
            for section in _user_props.sections():
                # 393: Add section if we don't know about it already
                if not self.has_section(section):
                    self.add_section(section.encode('ascii'))
                for key, value in _user_props.items(section):
                    self.set_prop(section.encode('ascii'), key.encode('ascii'), value)

        if merged:
            self.save_config()


    def save_image_list(self):
        """
        Save image list to prefs directory.  This is used as part of
        the notifier lifecycle management.
        """

        try:
            if not os.path.exists(os.path.dirname(self._config_path)):
                #XXX: What excpetions could this throw?
                os.makedirs(self._config_path)

            image_list_path = os.path.join(os.path.dirname(self._config_path),
                                                                "imagelist.cfg")

            # Test to see if the GUI knows about any images.  If it does
            # then save that list to the imagelist.cfg file.  If there
            # are not images known to the GUI and the imagelist exists,
            # remove it.
            if self.has_option('main', 'image_list'):
                image_list_file = open(image_list_path, "w")
                image_list_file.write(self.get('main', 'image_list'))
                image_list_file.close()
            elif os.path.exists(image_list_path):
                try:
                    os.remove(image_list_path)
                except:
                    # It is not critical if we fail to remove the empty image
                    # list.
                    pass

        except IOError, e:
            raise ConfigurationSaveError, _("Can not save image list to path '%(file_path)s'.  Errno: '%(number)d'") % {'file_path': image_list_path, 'number':e[0]}


    def save_config(self):
        #Does the config directory exist?
        if os.path.exists(self._config_path):
            #It exists but it is not a file.  We can't use it.
            if not os.path.isfile(self._config_path):
                raise ConfigurationSaveError, _("Can not save user preferences. The path '%s' is not a file") % self._config_path

        the_dir = os.path.dirname(self._config_path)
        if not os.path.exists(os.path.dirname(the_dir)):
            #XXX: What excpetions could this throw?
            os.makedirs(the_dir)

        try:
            prefs_file = open(self._config_path, "w")
            prefs_file.write("######## \n")
            prefs_file.write("# Update Tool/Update Tool Desktop Notifier Configuration File\n")
            prefs_file.write("#\n")
            prefs_file.write("# Warning: Do not edit this file.  Changes to this file may be lost.\n")
            prefs_file.write("######## \n")
            self.write(prefs_file)
            prefs_file.close()
            # Provide some minimal security since we store proxy password
            try:
                os.chmod(self._config_path, 0600)
            except:
                utils.logger.warn("Could not modify preferences file permission")
        except IOError, e:
            utils.logger.warn(str(e))
            raise ConfigurationSaveError, _("Can not save user preferences to path '%(file_path)s'.  Errno: '%(number)d'") % {'file_path':self._config_path, 'number':e[0]}

        self.save_image_list()


    def merge_init_props(self, _user_props, init_file):

        # Check to see if an init file exists
        init_path =  os.path.join(
                         os.path.dirname(self._config_path),
                         init_file)

        if os.path.exists(init_path):
            # Init exists

            try:
                # Load init's props into a ConfigParser
                init_file = codecs.open(init_path, "r", "utf-8")
                _init_props = ConfigParser.ConfigParser()
                _init_props.readfp(init_file)
                init_file.close()
            except IOError, e:
                # Can't load init props
                utils.logger.error("Could not load preferences file: %s. IOError: %s", init_path, str(e))
                return _user_props, False
        else:
            # Init props don't exists - just return the user props
            return _user_props, False


        # If the _user_props don't exist then return the init props
        if not _user_props:
            # We remove the date prop if it exists.
            try:
                _init_props.remove_option("main", "date")
            except: # (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
                pass

            # Once we have merged the props we remove the init file.
            remove_file(init_path)

            # If the user has opt'ed out of update notification (via the
            # bootstrapper or installer then we set the default check_freq
            # to never.
            if _init_props.has_option('main', 'optin.update.notification'):
                try:
                    if not _init_props.getboolean('main', 'optin.update.notification'):
                        add_option(_init_props, 'notifier', 'check_frequency', 'never')
                except ValueError:
                    add_option(_init_props, 'notifier',
                                                    'check_frequency', 'never')
            return _init_props, True

        # Both the init.cfg and user props (defaults.cfg) exist.  Perform a
        # merge of the two.
        user_image_list = []
        image_list_str = u""

        # For the image_list we want to append the path from the init.cfg
        # file if it doesn't already exist in the defaults.cfg image list.
        # This case needs to be executed if the list exists in both the
        # defaults.cfg and init.cfg files.
        if _user_props.has_option('main', 'image_list') and \
                _init_props.has_option('main', 'image_list'):
            user_image_list = utils.to_unicode(
                          _user_props.get('main', 'image_list')).splitlines()

            # If count returns 0 then we need to add the init.cfg image_list
            # to the merged image_list.  If count return > 1 then the path
            # already exists in the list so there is nothing to do.
            init_image_path = utils.to_unicode(
                          _init_props.get('main', 'image_list')).strip()
            if user_image_list.count(init_image_path) == 0:
                user_image_list.append(init_image_path)

        # Perform a generic overwrite.  Any init.cfg props overwrite existing
        # defaults.cfg props.
        for section in _init_props.sections():
            if not _user_props.has_section(section):
                _user_props.add_section(section)
            for key, value in _init_props.items(section):
                if key != "date":
                    _user_props.set(section, key,
                            utils.to_unicode(value, 'utf-8').encode('utf-8'))

        # Now we apply the image_list if init.cfg had a value that needed to
        # be append to an existing image list.
        for image in user_image_list:
            image_list_str = image_list_str + utils.to_unicode(image, 'utf-8') + u"\n"

        if image_list_str != u"":
            _user_props.set("main", "image_list", image_list_str.encode('utf-8'))

        # Deal with converting opt in prefs to correct check_freq.
        if _init_props.has_option('main', 'optin.update.notification'):

            # If the user has opt'ed in in the current init.cfg and the user's
            # current check_frequency is never we set it to the defaults of
            # weekly.
            if _init_props.getboolean('main', 'optin.update.notification') and \
                    _user_props.get('notifier', 'check_frequency') == 'never':
                add_option(_user_props, 'notifier', 'check_frequency', 'weekly')

            # If the user has opt'ed out of update checks in the current
            # init.cfg then set the check_freq to never.
            if not _init_props.getboolean('main', 'optin.update.notification'):
                add_option(_user_props, 'notifier', 'check_frequency', 'never')

        # Once we have merged the props we remove the init file.
        remove_file(init_path)
        return _user_props, True


    def load_defaults(self):
        """
        Load the ConfigParser with the tool's defaults.  These will later
        be overwritten by any user specifc preferences.
        """
        for section, props in DEFAULT_PROPS.iteritems():
            if not self.has_section(section):
                self.add_section(section)

            for k, v in props.iteritems():
                self.set(section, k, utils.to_unicode(v[0]).encode('utf-8'))


    def validate_prop(self, section, key, value):
        #print >> sys.stderr, section, key, type(value), repr(value)

        bool_values = ['true', 'false', 'yes', 'no']
        tmp_value = u""
        try:
            default_type = DEFAULT_PROPS[section][key][1]
        except KeyError:
            default_type = str

        if default_type == bool:
            if value.lower() in bool_values:
                tmp_value = value.lower()
            else:
                tmp_value = DEFAULT_PROPS[section][key][0]
        elif default_type == float:
            try:
                tmp_value = str(float(value))
            except ValueError:
                tmp_value = DEFAULT_PROPS[section][key][0]
        elif default_type == int:
            try:
                tmp_value = str(int(value))
            except ValueError:
                tmp_value = DEFAULT_PROPS[section][key][0]
        elif isinstance(default_type, list):
            if len(DEFAULT_PROPS[section][key]) > 2:
                if DEFAULT_PROPS[section][key][2] == 'upper':
                    value = value.upper()
                else:
                    value = value.lower()
            if value in default_type:
                tmp_value = value
            else:
                tmp_value = DEFAULT_PROPS[section][key][0]
        elif default_type == str:
            tmp_value = value
        elif default_type == "url":
            tmp_value = value
        elif type(default_type) == types.FunctionType:
            if default_type(value):
                tmp_value = value
            else:
                tmp_value = DEFAULT_PROPS[section][key][0]
        else:
            tmp_value = value
        return tmp_value


    def set_prop(self, section, key, value):
        value = self.validate_prop(section, key, value)
        ConfigParser.SafeConfigParser.set(self, section, key, utils.to_unicode(value).encode('utf-8'))


def get_default(section, item, default=None):
    try:
        return DEFAULT_PROPS[section][item][0]
    except KeyError:
        return default


def add_option(config, section, option, value):

    if not config.has_section(section):
        config.add_section(utils.to_unicode(section).encode('utf-8'))

    config.set(section, option, utils.to_unicode(value).encode('utf-8'))


def remove_file(path):

    if path:
        if os.path.exists(path):
            try:
                os.unlink(path)
            except:
                # XXX: Silently fail until we decide how to handle this error
                pass

