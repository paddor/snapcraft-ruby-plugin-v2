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
        packages = {"gcc", "curl", "make", "zlib1g-dev", "libssl-dev", "libreadline-dev"}

        if self.options.use_jemalloc:
            packages.add("libjemalloc-dev")

        return packages

    def get_build_environment(self) -> Dict[str, str]:
        return {
            "PATH": "${SNAPCRAFT_PART_INSTALL}/bin:${PATH}",
            "RUBYLIB": "${SNAPCRAFT_PART_INSTALL}/lib/ruby/snap:/root/parts/my-snap-test/install/lib/ruby/snap/x86_64-linux/", # TODO: support any arch
            "LD_LIBRARY_PATH": "${SNAPCRAFT_PART_INSTALL}/lib:${LD_LIBRARY_PATH}",
        }
            # "GEM_HOME": "${SNAPCRAFT_PART_INSTALL}/lib/ruby/gems/snap",
            # "GEM_PATH": "${SNAPCRAFT_PART_INSTALL}/lib/ruby/gems/snap",

    def _get_download_command(self) -> str:
        ruby_version = self.options.ruby_version
        feature_pattern = re.compile(r"^(\d+\.\d+)\..*$")
        feature_version = feature_pattern.sub(r"\1", ruby_version)
        url = "https://cache.ruby-lang.org/pub/ruby/{}/ruby-{}.tar.xz".format(
            feature_version,
            ruby_version
        )
        command = f"curl --proto '=https' --tlsv1.2 -C - -f {url} > ${{SNAPCRAFT_PART_SRC}}/ruby.tar.gz"

        return command


    def _configure_opts(self) -> List[str]:
        configure_opts = [
            "--without-baseruby",
            "--enable-shared",
            "--prefix=/",
            "--with-ruby-version=snap",
            "--disable-install-doc",
            "--with-vendordir=no",
            "--with-sitedir=no",
            ]

        if self.options.use_jemalloc:
            configure_opts.append("--with-jemalloc")

        return configure_opts

    def _get_install_commands(self) -> List[str]:
        commands = []
        commands.append("tar xf ${SNAPCRAFT_PART_SRC}/ruby.tar.gz")
        commands.append("pushd ruby-*")
        commands.append("./configure {}".format(' '.join(self._configure_opts())))
        commands.append("make -j${SNAPCRAFT_PARALLEL_BUILD_COUNT}")
        commands.append("make install DESTDIR=${SNAPCRAFT_PART_INSTALL}")
        commands.append("popd")
        commands.append("sed -i -e 's,^#!.*ruby,#!/usr/bin/env ruby,' ${SNAPCRAFT_PART_INSTALL}/bin/*")
        commands.append("mv ${SNAPCRAFT_PART_INSTALL}/bin/{ruby,ruby.bare}")
        commands.append("cp ${SNAPCRAFT_PART_SRC}/ruby ${SNAPCRAFT_PART_INSTALL}/bin/")
        commands.append("gem install --env-shebang bundler")

        # TODO: add commands that create wrapper script which supports any arch,
        #       or remove need for wrapper script entirely.

        if self.options.use_bundler:
            commands.append("bundle")

        # TODO: support options.gems

        return commands

    def get_build_commands(self) -> List[str]:
        commands = []
        commands.append(self._get_download_command())
        commands.extend(self._get_install_commands())
        return commands
