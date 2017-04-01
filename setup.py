#!/usr/bin/env python
# static_upnp responds to upnp search requests with statically configures responses.
# Copyright (C) 2016  NigelB
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from setuptools import setup, find_packages

setup(name='static_upnp',
      version='0.0.1',
      description='static_upnp responds to upnp search requests with statically configures responses.',
      author='NigelB',
      author_email='nigel.blair@gmail.com',
      packages=find_packages(),
      zip_safe=False,
      install_requires=["pyip", "schedule", "dnslib==0.9.7", "requests"],
      extras_require={"interfaces":"netifaces"},
      entry_points={
          "console_scripts": [
              "static_upnp = static_upnp.static:main",
          ]
      },
)
