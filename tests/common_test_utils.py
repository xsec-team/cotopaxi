# -*- coding: utf-8 -*-
"""Common test functions."""
#
#    Copyright (C) 2020 Samsung Electronics. All Rights Reserved.
#       Author: Jakub Botwicz (Samsung R&D Poland)
#
#    This file is part of Cotopaxi.
#
#    Cotopaxi is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 2 of the License, or
#    (at your option) any later version.
#
#    Cotopaxi is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Cotopaxi.  If not, see <http://www.gnu.org/licenses/>.
#

import configparser
import os
import socket
import sys
import time
import traceback
import timeout_decorator
import yaml

from cotopaxi.common_utils import get_local_ip
from cotopaxi.cotopaxi_tester import check_caps

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


def scrap_output(func, data):
    output = ""
    sys.stdout.flush()
    saved_stdout, sys.stdout = sys.stdout, StringIO()
    sys.stderr.flush()
    saved_stderr, sys.stderr = sys.stderr, StringIO()
    try:
        func(data)
    except (SystemExit, Exception) as exception:
        output += str(traceback.extract_stack()) + "\n"
        output += repr(exception) + "\n"
    finally:
        output += sys.stdout.getvalue().strip() + "\n"
        output += sys.stderr.getvalue().strip() + "\n"
        sys.stdout = saved_stdout
        sys.stderr = saved_stderr
    return output


def load_test_servers():
    print ("Loading config for test servers")
    config = configparser.ConfigParser()
    config.read(os.path.dirname(__file__) + "/test_config.ini")
    test_server_ip = config["COMMON"]["DEFAULT_IP"]
    if test_server_ip is None or test_server_ip == "1.1.1.1" or test_server_ip == "":
        exit(
            "\n\nPlease provide address of test server(s) in "
            "cotopaxi/tests/test_config.ini to perform remote tests!\n\n"
        )
    return config


def load_test_servers_list():
    print ("Loading list of test servers from YAML")
    with open(os.path.dirname(__file__) + "/test_servers.yaml", "r") as stream:
        test_servers = yaml.safe_load(stream)
        return test_servers
    return None


def poke_tcp_server(server_port):
    for i in range(2):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            sock.connect(("127.0.0.1", server_port))
            sock.send("123")
            sock.close()
        except (socket.timeout, socket.error):
            time.sleep(0.1)


class CotopaxiToolTester(object):
    config = load_test_servers()
    test_servers = load_test_servers_list()
    print ("Loaded test servers")
    local_ip = get_local_ip()

    def __init__(self, *args, **kwargs):
        self.main = None

    @classmethod
    def setUpClass(cls):
        try:
            scrap_output(check_caps(), [])
        except SystemExit:
            exit(
                "This test suite requires admin permissions on network interfaces.\n"
                "On Linux and Unix run it with sudo, use root account (UID=0) "
                "or add CAP_NET_ADMIN, CAP_NET_RAW manually!\n"
                "On Windows run as Administrator."
            )

    @timeout_decorator.timeout(5)
    def test_main_help(self):
        output = scrap_output(self.main, ["-h"])
        self.assertIn("optional arguments", output)
        self.assertIn("show this help message and exit", output)


class CotopaxiToolServerTester(CotopaxiToolTester):
    def __init__(self, *args, **kwargs):
        CotopaxiToolTester.__init__(self, *args, **kwargs)
        self.main = None


class CotopaxiToolClientTester(CotopaxiToolTester):
    def __init__(self, *args, **kwargs):
        CotopaxiToolTester.__init__(self, *args, **kwargs)
        self.main = None
