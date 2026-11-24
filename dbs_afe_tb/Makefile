# cocotb + Icarus.  make            -> protocol + neural tests on the behavioral frame model
#                   make AFE_SECONDS=2 -> longer recording
# Works with cocotb 1.x (MODULE) and 2.x (COCOTB_TEST_MODULES).
SIM ?= icarus
TOPLEVEL_LANG = verilog
# LEVEL=0 (default): spec-level frame model.   LEVEL=2: the real afe_dig gate netlist + ideal comparators (hdl/afe_dig_wrap.v)
#   make LEVEL=2 AFE_SECONDS=0.1 [PNL=../AFE/dig/final/afe_dig.pnl.v] [PDK_VERILOG=<dir with gf180mcu_fd_sc_mcu7t5v0.v>]
LEVEL ?= 0
ifeq ($(LEVEL),2)
PNL ?= $(PWD)/../AFE/dig/final/afe_dig.pnl.v
PDK_VERILOG ?= $(PDK_ROOT)/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/verilog
VERILOG_SOURCES = $(PWD)/hdl/afe_dig_wrap.v $(PNL) $(PDK_VERILOG)/gf180mcu_fd_sc_mcu7t5v0.v
COMPILE_ARGS += -DFUNCTIONAL -DUNIT_DELAY -I$(PDK_VERILOG)
COCOTB_TOPLEVEL = afe_dig_wrap
TOPLEVEL = afe_dig_wrap
else
VERILOG_SOURCES = $(PWD)/hdl/afe_frame_model.v
COCOTB_TOPLEVEL = afe_frame_model
TOPLEVEL = afe_frame_model
endif
COCOTB_TEST_MODULES = test_frames,test_neural
MODULE = test_frames,test_neural
export PYTHONPATH := $(PWD)/tb:$(PWD)/python:$(PYTHONPATH)
COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps
# cocotb's Icarus makefile needs iverilog on PATH (or ICARUS_BIN_DIR set); fail early with a clear message.
ifneq ($(MAKECMDGOALS),selfcheck)
ifeq ($(SIM),icarus)
ifeq ($(shell which iverilog 2>/dev/null),)
ifeq ($(ICARUS_BIN_DIR),)
$(error iverilog not found on PATH. Find it with 'find / -name iverilog -type f 2>/dev/null', then run: make ICARUS_BIN_DIR=<its directory>  (or put that directory on PATH))
endif
endif
endif
endif
include $(shell cocotb-config --makefiles)/Makefile.sim

selfcheck:
	python3 -I python/selfcheck.py