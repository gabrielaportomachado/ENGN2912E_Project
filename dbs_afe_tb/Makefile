# cocotb + Icarus.  make            -> protocol + neural tests on the behavioral frame model
#                   make AFE_SECONDS=2 -> longer recording
# Works with cocotb 1.x (MODULE) and 2.x (COCOTB_TEST_MODULES).
SIM ?= icarus
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(PWD)/hdl/afe_frame_model.v
COCOTB_TOPLEVEL = afe_frame_model
TOPLEVEL = afe_frame_model
COCOTB_TEST_MODULES = test_frames,test_neural
MODULE = test_frames,test_neural
export PYTHONPATH := $(PWD)/tb:$(PWD)/python:$(PYTHONPATH)
COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps
include $(shell cocotb-config --makefiles)/Makefile.sim

selfcheck:
	python3 -I python/selfcheck.py