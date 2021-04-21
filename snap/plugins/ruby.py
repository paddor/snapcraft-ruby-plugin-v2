"""
This ruby plugin is useful for building ruby based parts.
"""

import os
import re
import logging

from typing import Any, Dict, List, Set
from snapcraft.plugins.v2 import PluginV2


class PluginImpl(PluginV2):
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "ruby-flavor": {
                    "type": "string",
                    "default": "ruby",
                },
                "ruby-version": {
                    "type": "string",
                    "default": "3.0.1",
                    "pattern": r"^\d+\.\d+(\.\d+)?$",
                },
                "use-bundler": {
                    "type": "boolean",
                    "default": False,
                },
                "use-jemalloc": {
                    "type": "boolean",
                    "default": False,
                },
            },
            "required": ["source"],
        }

    def get_build_snaps(self) -> Set[str]:
        return set()

    def get_build_packages(self) -> Set[str]:
        packages = {"curl", "jq"}

        if self.options.use_jemalloc:
            packages.add("libjemalloc-dev")

        return packages

    def get_build_environment(self) -> Dict[str, str]:
        return {
            "PATH": "${SNAPCRAFT_PART_INSTALL}/bin:${PATH}",
            "LD_LIBRARY_PATH": "${SNAPCRAFT_PART_INSTALL}/lib:${LD_LIBRARY_PATH}", # for finding ruby.so
        }

    def _configure_opts(self) -> List[str]:
        # TODO: options for other Ruby flavors
        configure_opts = [
            "--without-baseruby",
            "--enable-load-relative",
            "--enable-shared",
            "--disable-install-doc",
            ]

        if self.options.use_jemalloc:
            configure_opts.append("--with-jemalloc")

        return configure_opts

    def _get_install_commands(self) -> List[str]:
        commands = []
        commands.append("ruby_install_url=$(curl -L --proto '=https' --tlsv1.2 'https://api.github.com/repos/postmodern/ruby-install/tags' | jq -r '.[0].tarball_url')")
        commands.append("curl -L --proto '=https' --tlsv1.2 $ruby_install_url | tar xz")
        commands.append("postmodern-ruby-install-*/bin/ruby-install -i ${{SNAPCRAFT_PART_INSTALL}} --package-manager apt -j${{SNAPCRAFT_PARALLEL_BUILD_COUNT}} {}-{} -- {}".format(
            self.options.ruby_flavor,
            self.options.ruby_version,
            ' '.join(self._configure_opts())))

        # NOTE: Update bundler. Avoid conflicts/prompts about replacing bundler
        #       executables by removing them first.
        commands.append("rm -f ${SNAPCRAFT_PART_INSTALL}/bin/{bundle,bundler}")
        commands.append("gem install --env-shebang --no-document bundler")

        if self.options.use_bundler:
            commands.append("bundle")

        # TODO: support options.gems

        return commands

    def get_build_commands(self) -> List[str]:
        commands = []
        commands.extend(self._get_install_commands())
        return commands
