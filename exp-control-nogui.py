#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright (C) 2015-2016  Simone Donadello
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#pylint: disable-msg=E1101

import sys, os

#change path
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

from libraries.system import System
PRG_NAME, PRG_VERSION = "EC - Experiment Control", "0.6.2"

def main(args):
    system = System()
    

if __name__ == "__main__":
    main(sys.argv)
