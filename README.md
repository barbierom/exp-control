# Experiment Control BEC TN

Software interface for the FPGA-based digital control system, used in the atomic physics experiment of the ultracold gases laboratory at the University of Trento (BEC research group).


## Install (Debian/Ubuntu)

Install `python2.7`, `numpy`, and `pyqt4`:
```
sudo apt-get install python-numpy python-qt4
```

Install FTDI support (use an updated version for `pylibftdi`):
```
sudo apt-get install libftdi-dev
sudo pip install pylibftdi
```

Create or edit the `udev` rules in `/etc/udev/rules.d/99-libftdi.rules` with the usb permissions for the communication with the FPGA:
```
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6010", GROUP="dialout", MODE="0660"
```

Add the current `username` to the `dialout` group:
```
sudo useradd -G dialout username
```

Clone the repository:
```
git clone https://github.com/simondona/exp-control-bec-tn.git
```

If needed set the `exp-control.py` as executable:
```
chmod +x exp-control.py
```


## Usage

Use always the `master` branch (`old-stable` just if something important is not working, while `develop` is just for testing unstable code). For changing the branch:
```
git checkout master
```

From the `master` branch, launch the GUI program:
```
./exp-control.py
```
(or with `python exp-control.py`).

The system kernel can also be initialized for running stand-alone without the GUI, e.g. from a python script:
```
from libraries.system import System
s = System()
s.init_fpga_list()
s.set_program("test")
s.send_program_and_run()
```


### User data

Files that should be modified by users (or GUI) are contained in `data/`.
Generally this directory is ignored from updates, if needed converters will update it. **Don't touch other files**, unless you do not want to push them on the repository. The directory `test/` is also ignored for local custom code if needed.



## Updates

Before and after updating from the remote repository, use `git status` to check the current status.

This should work:
```
git pull
```
In case of reported conflicts modify the files in order to resolve them.

In case of local modifies that must me preserved, use this sequence:
```
git stash
git pull
git stash pop
```

The roadmap of future versions can be found in the wiki: https://github.com/simondona/exp-control-bec-tn/wiki


## Licence

```
Experiment Control BEC TN
Copyright (C) 2015  Simone Donadello

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```
