import logging
import cocotb
from cocotb.triggers import *
from cocotb.clock import Clock
from cocotb.types import *

async def reset_dut(rstn, duration_ns):
    rstn.value = 0
    await Timer(duration_ns, "ns")
    rstn.value = 1
    cocotb.log.debug("Reset complete")

async def reset_inputs(dut):
    dut.wr_en_0.value     = 0
    dut.wr_en_1.value     = 0
    dut.wr_data_0.value   = 0
    dut.wr_data_1.value   = 0
    dut.rd_en_0.value     = 0
    dut.rd_en_1.value     = 0

@cocotb.test()
async def wr_until_full(dut):
    # Create a clock
    clk = Clock(dut.clk, 10, "ns")
    clk.start()

    # Reset the DUT
    rstn = dut.rstn
    await reset_dut(rstn, 30)
    await reset_inputs(dut)
    await RisingEdge(dut.clk)

    # Write 0xA to all slots in the FIFO
    dut.wr_data_0.value = LogicArray(0xA, Range((dut.DATA_WIDTH.value.to_unsigned() - 1), 'downto', 0))
    for i in range(dut.DEPTH.value):
        dut.wr_en_0.value = not dut.full.value
        await RisingEdge(dut.clk)
    dut.wr_en_0.value = 0
    await RisingEdge(dut.clk)

    # Check the outputs
    assert dut.full.value         == 1
    assert dut.almost_full.value  == 0
    assert dut.almost_empty.value == 0
    assert dut.empty.value        == 0
    for i in range(dut.DEPTH.value):
        assert dut.fifo_mem.mem.value == LogicArray(0x0000000A_0000000A_0000000A_0000000A_0000000A_0000000A_0000000A_0000000A, Range(dut.DEPTH.value.to_unsigned() * dut.DATA_WIDTH.value.to_unsigned() - 1, 'downto', 0))
