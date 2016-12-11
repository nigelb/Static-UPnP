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

import logging
import os
import sys
import signal
from argparse import ArgumentParser

from static_upnp.upnp_reciever import UPnPServiceResponder


class StaticService:
    def __init__(self, params, port, OK=None, NOTIFY=None, services=None):
        self.params = params
        self.port = port
        self.services = services
        self.OK = OK
        self.NOTIFY = NOTIFY


def main():
    argParse = ArgumentParser(description="static_upnp will announce and respond to upnp search requests for the statically configured devices.")
    argParse.add_argument("--config-dir",metavar="<config_dir>", dest="config_dir", action="store", help="The location of the config directory.")
    args = argParse.parse_args()

    try:
        args.config_dir = os.path.abspath(args.config_dir)
        sys.path.append(args.config_dir)
        import StaticUPnP_StaticServices
        import StaticUPnP_Permissions
        # import UPnPRelay_Paths

    except (AttributeError, ImportError) as e:
        print ("Could not find configuration in %s, specify with --config-dir option."%(args.config_dir))
        argParse.print_help()
        return

    #Setup up the logging
    FORMAT = '%(asctime)-15s %(levelname)-7s %(name)s %(filename)s:%(funcName)s:%(lineno)d - %(message)s'
    # FORMAT = '%(asctime)-15s %(levelname)-7s %(name)s File "%(pathname)s", line %(lineno)d, in %(funcName)s - %(message)s'


    logging.basicConfig(format=FORMAT,level=logging.DEBUG)
    logger = logging.getLogger("Main")
    upnp = UPnPServiceResponder(
            services=StaticUPnP_StaticServices.services,
    )

    def signal_handler(signal, frame):
        upnp.shutdown()

    signal.signal(signal.SIGINT, signal_handler)

    upnp.run()

if __name__ == "__main__":
    main()