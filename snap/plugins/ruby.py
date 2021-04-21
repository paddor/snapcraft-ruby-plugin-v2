"""
This ruby plugin is useful for building ruby based parts.
"""

import os
import re
import logging

from textwrap import dedent
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
                    "pattern": r"^\d+\.\d+\.\d+$",
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
            "LD_LIBRARY_PATH": "${SNAPCRAFT_PART_INSTALL}/lib:${LD_LIBRARY_PATH}", # for finding ruby.so
        }

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
            "--enable-load-relative",
            "--enable-shared",
            "--prefix=${SNAPCRAFT_PART_INSTALL}",
            "--disable-install-doc",
            ]

        if self.options.use_jemalloc:
            configure_opts.append("--with-jemalloc")

        return configure_opts

    def _get_install_commands(self) -> List[str]:
        commands = []
        commands.append("tar xf ${SNAPCRAFT_PART_SRC}/ruby.tar.gz")
        commands.append("pushd ruby-{}".format(self.options.ruby_version))
        commands.append("./configure {}".format(' '.join(self._configure_opts())))
        commands.append("make -j${SNAPCRAFT_PARALLEL_BUILD_COUNT}")
        commands.append("make install")
        commands.append("popd")

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
        commands.append(self._get_download_command())
        commands.extend(self._get_install_commands())
        return commands
