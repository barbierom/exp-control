#!/usr/bin/python
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

import pylibftdi, threading

import libraries.parser as lib_parser
import libraries.syscommands as lib_syscommand
import libraries.command as lib_command
import libraries.syslist as lib_syslist
import libraries.instruction as lib_instruction
import libraries.fpga as lib_fpga
import libraries.action as lib_action
import libraries.program as lib_program
import libraries.ramp as lib_ramp
from libraries import init_boards, init_actions, init_programs
import os, sys

#change path
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

class System(object):
    _time_base = 10e6
    _time_multiplier = 1e-3
    time_formats = dict(time="%.4f", time_rel="%+.4f")

    def __init__(self, external_trigger=False):
        print "Experiment Control"
        print "https://github.com/simondona/exp-control-bec-tn"
        print "author: Simone Donadello - license: GNU GPL v3"
        print

        self.fpga_list = []
        self.main_program = None
        self.external_trigger = bool(external_trigger)
        self.init_boards()
        self.init_actions()
        self.variables = dict()
        self.cmd_thread = lib_syscommand.SysCommand(self)
        self.parser = lib_parser.Parser(self)

    def init_boards(self):
        #first load boards
        self.board_list = lib_syslist.BoardList(system=self)
        init_boards.board_list_init(self.board_list)

    def init_actions(self):
        #then load actions and programs
        self.action_list = lib_syslist.ActionList(system=self)
        init_actions.action_list_init(self.action_list)
        init_programs.program_list_init(self.action_list)

    def init_fpga_list(self):
        new_list = pylibftdi.Driver().list_devices()
        self.fpga_list = []
        for n_id, name in enumerate(new_list):
            if name[1] == "DLP-FPGA":
                self.fpga_list.append(lib_fpga.Fpga(device_index=n_id))
        print "found " + str(len(self.fpga_list)) + " FPGAs connected"

    def print_fpga_commands(self):
        for cmd in self._get_program_commands():
            print cmd.get_hex()

    def get_fpga_status(self):
        status = []
        for fpga_id in self.fpga_list:
            status.append(fpga_id.get_status())
        return status

    def set_program(self, prg_name=None):
        if prg_name is None and self.main_program is not None:
            prg_name = self.main_program.name
        self.main_program = self.action_list.get(prg_name)
        if self.main_program is not None:
            print "loaded program '%s'"%self.main_program.name
        else:
            print "WARNING: loaded None program"

    def stop_sys_commands(self):
        self.cmd_thread.stop()

    def run_sys_commands(self):
        if self.main_program is not None:
            thread = threading.Thread(target=self.cmd_thread.start)
            thread.daemon = True
            self.cmd_thread.set_thread(thread)
            thread.start()
        else:
            print "ERROR: any program loaded in the system"

    def sys_commands_running(self):
        return self.cmd_thread.running

    def get_time(self, time):
        return float(time)/self._time_base/self._time_multiplier

    def set_time(self, time):
        return int(self._time_base*self._time_multiplier*float(time))

    def get_program_time(self, prg_name=None, *args, **kwargs):
        if prg_name is None:
            program = self.main_program
        else:
            program = self.action_list.get(prg_name, *args, **kwargs)
            if isinstance(program, lib_ramp.Ramp):
                program = program.get_prg()
        if isinstance(program, lib_program.Program):
            instrs_prg = program.get_all_instructions()
            if len(instrs_prg) > 0:
                return instrs_prg[-1].time_clock
            else:
                return 0
        else:
            print "WARNING: any program loaded"
            return 0

    def check_instructions(self):
        if isinstance(self.main_program, lib_program.Program):
            instructions = self.main_program.get_all_instructions()

            problems = []
            valid = True
            first_density_error = False
            if len(instructions) >= 2:
                if len(instructions) >= 2**14:
                    valid = False
                    problems += instructions[2**14:]
                    print "ERROR: too many instructions " + str(len(instructions)) + " in the program (maximum is 16k)"

                fifo_size = 2*(2**11)
                prev_instr = instructions[0]
                prev_dds_instr = None
                for n_instr, instr in enumerate(instructions):
                    if n_instr > 0:
                        time_delta = self._get_instr_time_diff(prev_instr, instr)
                        if time_delta < 4:
                            problems.append(instr)
                            valid = False
                            print "ERROR: too short time between actions '" + prev_instr.action.name + "' and '" + instr.action.name + "' at time " + str(self.get_time(instr.time_clock)) + " (minimum is 4 clock cicles)"
                        if time_delta > 2**32:
                            valid = False
                            problems.append(instr)
                            print "ERROR: too long time between actions '" + prev_instr.action.name + "' and '" + instr.action.name + "' at time " + str(self.get_time(instr.time_clock)) + " (maximum is about 429s)"
                        prev_instr = instr

                    if len(instructions) >= fifo_size \
                            and n_instr in range(len(instructions) - fifo_size) \
                            and not first_density_error:
                        time_delta = self._get_instr_time_diff(instructions[n_instr],
                                                               instructions[fifo_size+n_instr])
                        if time_delta < fifo_size*20:
                            valid = False
                            problems += instructions[n_instr:fifo_size+n_instr]
                            first_density_error = True
                            print "ERROR: too dense operations starting at time " + str(self.get_time(instructions[n_instr].time_clock)) + " (a rate of 20 clock cicles per action can be sustained when the FIFO is empty)"

                    if isinstance(instr.action, lib_action.DdsAction) \
                                            and prev_dds_instr is not None:
                        if instr.time_clock - prev_dds_instr.time_clock < 0.035 \
                                and instr.action.board == prev_dds_instr.action.board:
                            valid = False
                            problems.append(instr)
                            print "ERROR: DDS actions '" + prev_dds_instr.action.name + "' and '" + instr.action.name + "' at time " + str(self.get_time(instr.time_clock)) + " are too close (a DDS action takes 35us to complete)"
                        prev_dds_instr = None
                    if isinstance(instr.action, lib_action.DdsAction):
                        prev_dds_instr = instr

            return valid, problems
        else:
            return False, []

    def send_program_and_run(self):
        result = False
        if isinstance(self.main_program, lib_program.Program):
            instructions = self._get_program_commands()
            print "running the current program"
            for fpga_id in self.fpga_list:
                valid = fpga_id.send_program_and_run(instructions)
                result = result or valid
        else:
            print "WARNING: any program loaded"
        return result

    def _run_program(self):
        if isinstance(self.main_program, lib_program.Program):
            instrs_prg = self.main_program.get_all_instructions()
            valid, problems = self.check_instructions()
            if not valid:
                for probl in problems:
                    probl.parents[-1].get(probl.uuid).enable = False
            valid, problems = self.check_instructions()

            instrs_fpga = []
            prev_instr = lib_instruction.Instruction(0, lib_action.Action(self, "temp"))
            for curr_instr in instrs_prg:
                if curr_instr not in problems:
                    time_delta = self._get_instr_time_diff(prev_instr, curr_instr)
                    new_instr = lib_instruction.FpgaInstruction(time_delta, curr_instr)
                    instrs_fpga.append(new_instr)

                    prev_instr = curr_instr
                else:
                    print "WARNING: action \"%s\" at time %f wont be executed"%(curr_instr.action.name, self.get_time(curr_instr.time_clock))

            end_instr = lib_instruction.FpgaInstruction(0, action=lib_action.EndAction(self))
            instrs_fpga.append(end_instr)

            return instrs_fpga
        else:
            return []

    def _get_program_commands(self):
        if isinstance(self.main_program, lib_program.Program):
            instructions = self._run_program()

            cmd_list = []
            if self.external_trigger:
                cmd_list.append(lib_command.ExtTriggerOnCommand())
            else:
                cmd_list.append(lib_command.ExtTriggerOffCommand())

            for instr_num, instr in enumerate(instructions):
                cmd_list.append(lib_command.LoadCommand(memory=instr_num,
                                                        command=instr.action.command_bits,
                                                        time=instr.time_clock,
                                                        address=instr.action.board.address,
                                                        data=instr.data))

            cmd_list.append(lib_command.LoadDoneCommand())

            return cmd_list
        else:
            return []

    def _get_instr_time_diff(self, prev_instr, curr_instr):
        if isinstance(prev_instr, lib_instruction.Instruction) and \
                    isinstance(curr_instr, lib_instruction.Instruction):
            delta_t = int(curr_instr.time_clock - prev_instr.time_clock)
            return max(0, delta_t)
        else:
            print "WARNING: wrong call to time interval function, two \"%s\" must be given"%(str(lib_instruction.Instruction))
            return None
