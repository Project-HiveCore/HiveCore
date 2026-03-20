import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ReadOnly

class InstrFifoTB:
    def __init__(self, dut):
        self.dut = dut
        self.log = cocotb.log
        cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    async def reset(self):
        """Applies active-low reset and zeroes all inputs."""
        self.dut.rstn.value = 0
        # self.dut.flush.value = 0
        self.dut.wr_en_0.value = 0
        self.dut.wr_en_1.value = 0
        self.dut.rd_en_0.value = 0
        self.dut.rd_en_1.value = 0
        self.dut.wr_data_0.value = 0
        self.dut.wr_data_1.value = 0

        await Timer(30, unit="ns")
        self.dut.rstn.value = 1
        await RisingEdge(self.dut.clk)
        self.log.info("DUT Reset Complete.")

    async def write(self, instr0=None, instr1=None):
        """
        Writes 1 or 2 instructions on the rising edge.
        Pass None to an argument to skip writing to that port.
        """
        self.dut.wr_en_0.value = 1 if instr0 is not None else 0
        self.dut.wr_en_1.value = 1 if instr1 is not None else 0
        
        if instr0 is not None: self.dut.wr_data_0.value = instr0
        if instr1 is not None: self.dut.wr_data_1.value = instr1

        await RisingEdge(self.dut.clk)

        # Clean up / Deassert signals
        self.dut.wr_en_0.value = 0
        self.dut.wr_en_1.value = 0

    async def read(self, read0=True, read1=True):
        """
        Asserts read enables to advance the FIFO pointers.
        Returns the data that was on the output ports *before* advancing.
        """
        # Ensure we sample the output signals at the end of the current cycle 
        # (simulating combinational logic read before the clock edge advances it)
        await RisingEdge(self.dut.clk)
        out0 = self.dut.rd_data_0.value
        out1 = self.dut.rd_data_1.value

        self.dut.rd_en_0.value = 1 if read0 else 0
        self.dut.rd_en_1.value = 1 if read1 else 0

        await RisingEdge(self.dut.clk)

        # Clean up / Deassert signals
        self.dut.rd_en_0.value = 0
        self.dut.rd_en_1.value = 0
        
        return out0, out1

    # async def trigger_flush(self):
    #     """Fires the flush signal for one clock cycle."""
    #     self.dut.flush.value = 1
    #     await RisingEdge(self.dut.clk)
    #     self.dut.flush.value = 0


# ==========================================
# TEST CASES
# ==========================================

@cocotb.test()
async def test_initial_state(dut):
    """Test 1: Verify flags right after reset."""
    tb = InstrFifoTB(dut)
    await tb.reset()

    # The ReadOnly trigger waits until all signal values have settled for this timestep
    await RisingEdge(dut.clk)
    
    assert dut.empty.value == 1, "FIFO should be empty after reset"
    assert dut.almost_empty.value == 0, "FIFO should not be almost empty (it is fully empty)"
    assert dut.full.value == 0, "FIFO should not be full"
    assert dut.almost_full.value == 0, "FIFO should not be almost full"

@cocotb.test()
async def test_basic_2wide_rw(dut):
    """Test 2: Write two instructions, check flags, then read them."""
    tb = InstrFifoTB(dut)
    await tb.reset()

    # Write two instructions (0xAAAA and 0xBBBB)
    await tb.write(instr0=0xAAAA, instr1=0xBBBB)
    
    await RisingEdge(dut.clk)
    assert dut.empty.value == 0, "FIFO should not be empty after write"

    # Read both back
    out0, out1 = await tb.read(read0=True, read1=True)
    
    # Verify the read data
    assert out0 == 0xAAAA, f"Expected 0xAAAA, got {hex(out0)}"
    assert out1 == 0xBBBB, f"Expected 0xBBBB, got {hex(out1)}"
    
    await RisingEdge(dut.clk)
    assert dut.empty.value == 1, "FIFO should be empty after reading everything"

# @cocotb.test()
# async def test_flush_behavior(dut):
#     """Test 3: Verify the flush signal clears the FIFO."""
#     tb = InstrFifoTB(dut)
#     await tb.reset()

#     # Write some data
#     await tb.write(instr0=0xDEAD, instr1=0xBEEF)
#     await RisingEdge(dut.clk)
#     assert dut.empty.value == 0, "FIFO should have data"

#     # Trigger a flush (e.g., misprediction)
#     await tb.trigger_flush()
#     await RisingEdge(dut.clk)

#     assert dut.empty.value == 1, "FIFO should be entirely empty after a flush"

import random
from collections import deque
from cocotb.triggers import RisingEdge, ReadOnly

# ==========================================
#       Basic Functionality & Reset
# ==========================================

@cocotb.test()
async def test_single_wide_rw(dut):
    """Write 1 instruction, check flags, read 1 instruction."""
    tb = InstrFifoTB(dut)
    await tb.reset()

    # Write only to port 0
    await tb.write(instr0=0x1111, instr1=None)
    
    await RisingEdge(dut.clk)
    assert dut.empty.value == 0, "FIFO should not be empty"
    assert dut.almost_empty.value == 1, "FIFO should be almost empty (1 item)"

    # Read only from port 0
    out0, out1 = await tb.read(read0=True, read1=False)
    
    assert out0 == 0x1111, f"Expected 0x1111, got {hex(out0)}"
    
    await RisingEdge(dut.clk)
    assert dut.empty.value == 1, "FIFO should be empty again"


# ==========================================
#     Flag Logic & Boundary Transitions
# ==========================================

@cocotb.test()
async def test_fill_to_full_and_drain(dut):
    """Fills FIFO completely to verify full/almost_full, then drains to verify empty/almost_empty."""
    tb = InstrFifoTB(dut)
    await tb.reset()

    depth = 0
    # Fill 1 by 1 so we don't accidentally skip the almost_full flag (which implies exactly 1 slot left)
    while True:
        await RisingEdge(dut.clk)
        if dut.almost_full.value == 1:
            # Exactly 1 space left. One more write should trigger full.
            await tb.write(instr0=0xEEEE, instr1=None)
            depth += 1
            break
        elif dut.full.value == 1:
            assert False, "FIFO went to full without hitting almost_full first!"
        
        await tb.write(instr0=0xAAAA, instr1=None)
        depth += 1

    await RisingEdge(dut.clk)
    assert dut.full.value == 1, "FIFO should be full"
    
    # Now drain it 1 by 1
    items_read = 0
    while True:
        await RisingEdge(dut.clk)
        if dut.almost_empty.value == 1:
            # Exactly 1 item left. One more read should trigger empty.
            await tb.read(read0=True, read1=False)
            items_read += 1
            break
        elif dut.empty.value == 1:
            assert False, "FIFO went empty without hitting almost_empty first!"
            
        await tb.read(read0=True, read1=False)
        items_read += 1

    await RisingEdge(dut.clk)
    assert dut.empty.value == 1, "FIFO should be empty"
    assert depth == items_read, f"Wrote {depth} items but read {items_read} items!"


# ==========================================
#    Unaligned Access & Pointer Wrapping
# ==========================================

@cocotb.test()
async def test_write_2_read_1(dut):
    """Continuously writes 2, reads 1 to test internal pointer wrapping."""
    tb = InstrFifoTB(dut)
    await tb.reset()

    # Write 2, Read 1 (Net +1 per loop). Do this until almost full.
    counter = 1
    while True:
        await RisingEdge(dut.clk)
        if dut.almost_full.value == 1 or dut.full.value == 1:
            break
            
        await tb.write(instr0=counter, instr1=counter+1)
        await tb.read(read0=True, read1=False)
        counter += 2


@cocotb.test()
async def test_write_1_read_2(dut):
    """Continuously writes 1, then reads 2 to test sequential fetching across cycles."""
    tb = InstrFifoTB(dut)
    await tb.reset()

    # Write 8 items individually
    for i in range(8):
        await tb.write(instr0=0x100+i, instr1=None)
        
    # Read them back 2 at a time
    for i in range(4):
        out0, out1 = await tb.read(read0=True, read1=True)
        expected0 = 0x100 + (i*2)
        expected1 = 0x100 + (i*2) + 1
        assert out0 == expected0, f"Expected {hex(expected0)}, got {hex(out0)}"
        assert out1 == expected1, f"Expected {hex(expected1)}, got {hex(out1)}"


# ==========================================
#       Constraints & Error Handling
# ==========================================

@cocotb.test()
async def test_write_overflow_protection(dut):
    """Forces a write to a full FIFO and ensures valid data isn't corrupted."""
    tb = InstrFifoTB(dut)
    await tb.reset()

    # Fill FIFO
    while True:
        await RisingEdge(dut.clk)
        if dut.full.value == 1: break
        # Write 1 by 1 until full
        await tb.write(instr0=0xFACE, instr1=None)

    # Force a write while full (Should be ignored by FIFO)
    await tb.write(instr0=0xBAD0, instr1=0xBAD1)
    
    # Read the first item, verify it is NOT the ignored write
    out0, out1 = await tb.read(read0=True, read1=False)
    assert out0 == 0xFACE, f"FIFO overwritten! Expected 0xFACE, got {hex(out0)}"

@cocotb.test()
async def test_read_underflow_protection(dut):
    """Forces a read on an empty FIFO, then verifies subsequent writes still work."""
    tb = InstrFifoTB(dut)
    await tb.reset()

    await RisingEdge(dut.clk)
    assert dut.empty.value == 1

    # Force a read while empty (Should output junk, but NOT break internal pointers)
    await tb.read(read0=True, read1=True)

    # Write valid data and read it back to ensure pointers are still aligned
    await tb.write(instr0=0xCAFE, instr1=0xBABE)
    out0, out1 = await tb.read(read0=True, read1=True)
    
    assert out0 == 0xCAFE, f"Underflow broke pointers! Expected 0xCAFE, got {hex(out0)}"
    assert out1 == 0xBABE, f"Underflow broke pointers! Expected 0xBABE, got {hex(out1)}"


# ==========================================
#        Advanced / Stress Testing
# ==========================================

@cocotb.test()
async def test_simultaneous_rw(dut):
    """Asserts both write and read enables simultaneously."""
    tb = InstrFifoTB(dut)
    await tb.reset()

    # Pre-fill with 2 items so we can read and write at the same time
    await tb.write(instr0=0x1111, instr1=0x2222)

    # Perform simultaneous RW for 5 cycles manually
    for i in range(5):
        # Setup inputs
        dut.wr_en_0.value = 1
        dut.wr_en_1.value = 1
        dut.wr_data_0.value = 0x3333 + i
        dut.wr_data_1.value = 0x4444 + i
        
        dut.rd_en_0.value = 1
        dut.rd_en_1.value = 1

        await RisingEdge(dut.clk)

    # Clean up signals
    dut.wr_en_0.value = 0
    dut.wr_en_1.value = 0
    dut.rd_en_0.value = 0
    dut.rd_en_1.value = 0
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_randomized_stress_with_golden_model(dut):
    """Randomly writes/reads 0-2 items per cycle and checks against a Python deque."""
    tb = InstrFifoTB(dut)
    await tb.reset()

    golden_q = deque()
    data_counter = 0

    for _ in range(500): # Run for 500 clock cycles
        await RisingEdge(dut.clk)
        
        # Decide how many to write based on flags
        write_count = 0
        if dut.full.value == 0:
            if dut.almost_full.value == 1:
                write_count = random.choice([0, 1]) # Only 1 space left
            else:
                write_count = random.choice([0, 1, 2])
        
        # Decide how many to read based on flags
        read_count = 0
        if dut.empty.value == 0:
            if dut.almost_empty.value == 1:
                read_count = random.choice([0, 1]) # Only 1 item available
            else:
                read_count = random.choice([0, 1, 2])

        # Setup Write Signals
        dut.wr_en_0.value = 1 if write_count >= 1 else 0
        dut.wr_en_1.value = 1 if write_count == 2 else 0
        if write_count >= 1:
            dut.wr_data_0.value = data_counter
            golden_q.append(data_counter)
            data_counter += 1
        if write_count == 2:
            dut.wr_data_1.value = data_counter
            golden_q.append(data_counter)
            data_counter += 1

        # Setup Read Signals
        dut.rd_en_0.value = 1 if read_count >= 1 else 0
        dut.rd_en_1.value = 1 if read_count == 2 else 0

        # Before clock edge, grab the read data if we are reading
        out0_val = int(dut.rd_data_0.value) if dut.rd_data_0.value.is_resolvable else 0
        out1_val = int(dut.rd_data_1.value) if dut.rd_data_1.value.is_resolvable else 0

        # Advance Clock
        await RisingEdge(dut.clk)

        # Verify reads against golden model
        if read_count >= 1:
            expected0 = golden_q.popleft()
            assert out0_val == expected0, f"Mismatch out0! Expected {expected0}, got {out0_val}"
        if read_count == 2:
            expected1 = golden_q.popleft()
            assert out1_val == expected1, f"Mismatch out1! Expected {expected1}, got {out1_val}"

        # Clean up signals for next loop iteration
        dut.wr_en_0.value = 0
        dut.wr_en_1.value = 0
        dut.rd_en_0.value = 0
        dut.rd_en_1.value = 0