# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright (C) 2020 Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""This flutter plugin is useful for building flutter based parts.

This plugin uses the common plugin keywords as well as those for "sources".
For more information check the 'plugins' topic for the former and the
'sources' topic for the latter.

Additionally, this plugin uses the following plugin-specific keywords:

    - flutter-channel
      (string, default: "stable")
      Which Flutter channel to use for the build
    - flutter-revision
      (string, default: None)
      Which Flutter revision to use for the build
    - flutter-target
      (string, default: lib/main.dart)
      The main entry-point file of the application
"""

from textwrap import dedent
from typing import Any, Dict, List, Set
import os

from snapcraft.file_utils import link_or_copy_tree
from snapcraft.plugins.v1 import PluginV1


class FlutterPlugin(PluginV1):
    @classmethod
    def schema(cls):
        schema = super().schema()
        schema["properties"]["flutter-channel"] = {
            "type": "string",
            "enum": ["stable", "beta", "dev", "master"],
        }
        schema["properties"]["flutter-target"] = {
            "type": "string",
            "default": "lib/main.dart",
        }
        schema["properties"]["flutter-revision"] = {
            "type": "string",
            "default": None,
        }
        schema["required"] = ["source"]

        return schema

    @classmethod
    def get_pull_properties(cls):
        return ["flutter-channel", "flutter-revision"]

    @classmethod
    def get_build_properties(cls):
        return ["flutter-target"]

    def __init__(self, name, options, project):
        super().__init__(name, options, project)

        if project._get_build_base() not in ("core", "core16", "core18"):
            raise errors.PluginBaseError(
                part_name=self.name, base=project._get_build_base()
            )

        self.build_snaps.extend(["flutter/latest/edge"])

    def build(self):
        super().build()
        channel_cmd = [
            "flutter",
            "channel",
            self.options.flutter_channel
        ]
        config_cmd = [
            "flutter",
            "config",
            "--enable-linux-desktop"
        ]
        upgrade_cmd = [
            "flutter",
            "upgrade"
        ]
        doctor_cmd = [
            "flutter",
            "doctor"
        ]
        revision_cmd = [
            "yes",
            "|",
            "flutter",
            "version",
            self.options.flutter_revision
        ]
        pub_get_cmd = [
            "flutter",
            "pub",
            "get"
        ]
        build_cmd = [
            "flutter",
            "build",
            "linux",
            "--release",
            "-v",
            "-t",
            self.options.flutter_target
        ]
        mkdir_cmd = [
            "mkdir",
            "-p",
            self.installdir + "/bin"
        ]

        commands = [channel_cmd, config_cmd, upgrade_cmd]
        if self.options.flutter_revision:
            commands.append(revision_cmd)
        commands.extend([doctor_cmd, pub_get_cmd, build_cmd, mkdir_cmd])

        # build and install
        for cmd in commands:
            self.run(cmd, env=self._build_env(), cwd=self.builddir)

        # Now move everything over to the plugin's installdir
        link_or_copy_tree(self.builddir + "/build/linux/release/bundle", self.installdir + "/bin/")


    def _build_env(self):
        env = os.environ.copy()
        return env

    @property  # type: ignore
    def stage_packages(self):
        return super().stage_packages + self.plugin_stage_packages
