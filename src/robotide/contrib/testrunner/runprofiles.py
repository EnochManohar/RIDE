# Copyright 2010 Orbitz WorldWide
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''runProfiles.py

This module contains profiles for running robot tests via the
runnerPlugin.

Each class that is a subclass as BaseProfile will appear in a
drop-down list within the plugin. The chosen profile will be used to
build up a command that will be passed in the tests to run as well as
any additional arguments.
'''

import wx
from wx.lib.filebrowsebutton import FileBrowseButton
import os

from robotide.widgets import Label


class BaseProfile(object):
    '''Base class for all test runner profiles

    At a minimum each profile must set the name attribute, which is
    how the profile will appear in the dropdown list.

    In case some settings are needed, provide default_settings class attribute
    with default values.

    This class (BaseProfile) will _not_ appear as one of the choices.
    Think of it as an abstract class, if Python 2.5 had such a thing.
    '''

    # this will be set to the plugin instance at runtime
    plugin = None
    default_settings = {}

    def __init__(self, plugin):
        '''plugin is required so that the profiles can save their settings'''
        self.plugin = plugin

    def get_toolbar(self, parent):
        '''Returns a panel with toolbar controls to be shown for this profile'''
        return wx.Panel(parent, wx.ID_ANY)

    def get_custom_args(self):
        '''Return a list of arguments unique to this profile.

        Returned arguments are in format accepted by Robot Framework's argument
        file.
        '''
        return []

    def get_command_prefix(self):
        '''Returns a command and any special arguments for this profile'''
        return ["pybot.bat" if os.name == "nt" else "pybot"]

    def set_setting(self, name, value):
        '''Sets a plugin setting

        setting is automatically prefixed with profile's name and it can be
        accessed with direct attribute access. See also __getattr__.
        '''
        self.plugin.save_setting(self._get_setting_name(name), value, delay=2)

    def __getattr__(self, name):
        """Provides attribute access to profile's settings

        If for example default_settings = {'setting1' = ""} is defined
        then setting1 value can be used like self.setting1
        set_setting is used to store the value.
        """
        try:
            return getattr(self.plugin, self._get_setting_name(name))
        except AttributeError:
            try:
                return getattr(self.plugin, name) #Support users old saved values
            except AttributeError:
                if self.default_settings.has_key(name):
                    return self.default_settings[name]
                raise

    def _get_setting_name(self, name):
        """Adds profile's name to the setting."""
        return "%s_%s" % (self.name.replace(' ', '_'), name)


class PybotProfile(BaseProfile):
    '''A runner profile which uses pybot

    It is assumed that pybot is on the path
    '''
    name = "pybot"
    default_settings = {"arguments": "",
                        "include_tags": "",
                        "exclude_tags": "",
                        "apply_include_tags": False,
                        "apply_exclude_tags": False}

    def __init__(self, plugin):
        BaseProfile.__init__(self, plugin)
        self._toolbar = None

    def get_command_prefix(self):
        '''Returns a command and any special arguments for this profile'''
        return [self.get_command()] + self.arguments.split()

    def get_command(self):
        return "pybot.bat" if os.name == "nt" else "pybot"

    def get_custom_args(self):
        args = []
        if self.apply_include_tags and self.include_tags:
            for include in self._get_tags_from_string(self.include_tags):
                args.append("--include=%s" % include)
        if self.apply_exclude_tags and self.exclude_tags:
            for exclude in self._get_tags_from_string(self.exclude_tags):
                args.append("--exclude=%s" % exclude)
        return args

    def _get_tags_from_string(self, tag_string):
        tags = []
        for tag in tag_string.split(","):
            tag = tag.strip().replace(' ', '')
            if len(tag) > 0:
                tags.append(tag)
        return tags

    def get_toolbar(self, parent):
        if self._toolbar is None:
            self._toolbar = self._get_toolbar(parent)
        return self._toolbar

    def _get_toolbar(self, parent):
        panel = wx.Panel(parent, wx.ID_ANY)
        sizer = wx.BoxSizer(wx.VERTICAL)
        for item in self.get_toolbar_items():
            sizer.Add(item(panel), 0, wx.ALL|wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def get_toolbar_items(self):
        return [self.ArgumentsPanel, self.TagsPanel]

    def ArgumentsPanel(self, parent):
        panel = wx.Panel(parent, wx.ID_ANY)
        label = Label(panel, label="Arguments: ")
        self._arguments = wx.TextCtrl(panel, wx.ID_ANY, size=(-1,-1),
                                     value=self.arguments)
        self._arguments.SetToolTipString("Arguments for the test run. Arguments are space separated list.")
        self._arguments.Bind(wx.EVT_TEXT, self.OnArgumentsChanged)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(label, 0, wx.ALL|wx.EXPAND)
        sizer.Add(self._arguments, 1, wx.ALL|wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def TagsPanel(self, parent):
        '''Create a panel to input include/exclude tags'''
        panel = wx.Panel(parent, wx.ID_ANY)
        include_cb = self._create_checkbox(panel, self.apply_include_tags,
                                           "Only run tests with these tags")
        exclude_cb = self._create_checkbox(panel, self.apply_exclude_tags,
                                           "Skip tests with these tags")
        self._include_tags = wx.TextCtrl(panel, wx.ID_ANY, size=(150,-1),
                                         value=self.include_tags)
        self._exclude_tags = wx.TextCtrl(panel, wx.ID_ANY, size=(150,-1),
                                         value=self.exclude_tags)

        panel.Bind(wx.EVT_CHECKBOX, self.OnIncludeCheckbox, include_cb)
        panel.Bind(wx.EVT_CHECKBOX, self.OnExcludeCheckbox, exclude_cb)
        self._include_tags.Bind(wx.EVT_TEXT, self.OnIncludeTagsChanged)
        self._exclude_tags.Bind(wx.EVT_TEXT, self.OnExcludeTagsChanged)

        panelsizer = wx.GridBagSizer(2,2)
        panelsizer.Add(include_cb, (0,0), flag=wx.EXPAND)
        panelsizer.Add(exclude_cb, (0,1), flag=wx.EXPAND)
        panelsizer.Add(self._include_tags, (1,0), flag=wx.EXPAND)
        panelsizer.Add(self._exclude_tags, (1,1), flag=wx.EXPAND)
        panelsizer.AddGrowableCol(0)
        panelsizer.AddGrowableCol(1)
        panel.SetSizerAndFit(panelsizer)
        return panel

    def _create_checkbox(self, parent, value, title):
        checkbox = wx.CheckBox(parent, wx.ID_ANY, title)
        checkbox.SetValue(value)
        return checkbox

    def OnArgumentsChanged(self, evt):
        self.set_setting("arguments", self._arguments.GetValue())

    def OnExcludeCheckbox(self, evt):
        self.set_setting("apply_exclude_tags", evt.IsChecked())

    def OnIncludeCheckbox(self, evt):
        self.set_setting("apply_include_tags", evt.IsChecked())

    def OnIncludeTagsChanged(self, evt):
        self.set_setting("include_tags", self._include_tags.GetValue())

    def OnExcludeTagsChanged(self, evt):
        self.set_setting("exclude_tags", self._exclude_tags.GetValue())


class CustomScriptProfile(PybotProfile):
    '''A runner profile which uses script given by the user'''

    name = "custom script"
    default_settings = dict(PybotProfile.default_settings, runner_script="")

    def get_command(self):
        return self.runner_script

    def get_toolbar_items(self):
        return [self.RunScriptPanel, self.ArgumentsPanel, self.TagsPanel]

    def RunScriptPanel(self, parent):
        panel = wx.Panel(parent, wx.ID_ANY)
        self._script = FileBrowseButton(panel, labelText="Script to run tests:",
                                        size=(-1, -1), fileMask="*",
                                        changeCallback=self.OnCustomScriptChanged)
        self._script.SetValue(self.runner_script)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._script, 0, wx.ALL|wx.EXPAND)
        panel.SetSizerAndFit(sizer)
        return panel

    def OnCustomScriptChanged(self, evt):
        self.set_setting("runner_script", self._script.GetValue())
