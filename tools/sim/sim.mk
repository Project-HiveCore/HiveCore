# =====================================
# 	Sim targets common to all modules
# =====================================

# View a generated waveform
wave:
	@if [ -z "$(VIEW)" ]; then \
		echo "Usage: make wave VIEW=<name>"; \
		exit 1; \
	fi
	@if [ ! -f sim_build/waves/$(VIEW).wlf ]; then \
		echo "Waveform file 'sim_build/waves/$(VIEW).wlf' not found."; \
		echo "Run 'make wave VIEW=<name>' with a valid VIEW to view the waveform."; \
		exit 1; \
	fi
	vsim -view sim_build/waves/$(VIEW).wlf -do wave.do

# Remove all sim generated files and directories
clean:
	rm -rf sim_build .pytest_cache __pycache__
	rm -rf $(TOOLS_DIR)/__pycache__ $(PROJ_ROOT)/.pytest_cache
	rm -f results.xml *.ini vsim.wlf transcript *.log

# Run lint on all design files in this module's src directory
lint:
	verible-verilog-lint ../src/*