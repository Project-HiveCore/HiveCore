import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


class InstrQMemTB:
    def __init__(self, dut):
        self.dut = dut
        self.log = cocotb.log

        self.depth = self._param_int("DEPTH", 8)
        self.data_width = self._param_int("DATA_WIDTH", 32)
        self.wr_ports = self._param_int("WR_PORTS", 4)
        self.rd_ports = self._param_int("RD_PORTS", 4)

        self.addr_width = max(1, (self.depth - 1).bit_length())
        self.data_mask = (1 << self.data_width) - 1

        cocotb.start_soon(Clock(self.dut.clk, 10, unit="ns").start())

    def _param_int(self, name: str, default: int) -> int:
        try:
            return int(getattr(self.dut, name).value)
        except Exception:
            return default

    def _mask_data(self, value: int) -> int:
        return value & self.data_mask

    def _set_all_writes_idle(self):
        for p in range(self.wr_ports):
            self.dut.wr_en[p].value = 0
            self.dut.wr_addr[p].value = 0
            self.dut.wr_data[p].value = 0

    def _set_all_reads_idle(self):
        for p in range(self.rd_ports):
            self.dut.rd_addr[p].value = 0

    async def initialize(self):
        self._set_all_writes_idle()
        self._set_all_reads_idle()
        await RisingEdge(self.dut.clk)

    async def clear_memory(self):
        """Clear every location by writing zeros through write port 0."""
        self._set_all_writes_idle()
        for addr in range(self.depth):
            self.dut.wr_en[0].value = 1
            self.dut.wr_addr[0].value = addr
            self.dut.wr_data[0].value = 0
            await RisingEdge(self.dut.clk)
        self._set_all_writes_idle()
        await RisingEdge(self.dut.clk)

    async def apply_writes_one_cycle(self, writes):
        """
        Apply writes for one cycle.
        writes: iterable of (port, addr, data)
        """
        self._set_all_writes_idle()
        for port, addr, data in writes:
            assert 0 <= port < self.wr_ports, f"Invalid write port {port}"
            assert 0 <= addr < self.depth, f"Invalid write addr {addr}"
            self.dut.wr_en[port].value = 1
            self.dut.wr_addr[port].value = addr
            self.dut.wr_data[port].value = self._mask_data(data)

        await RisingEdge(self.dut.clk)
        await Timer(1, unit="step")
        self._set_all_writes_idle()

    async def set_read_addresses(self, addr_by_port):
        for p in range(self.rd_ports):
            self.dut.rd_addr[p].value = int(addr_by_port.get(p, 0))

        # Let combinational read outputs settle in current timestep
        await Timer(1, unit="step")

    async def assert_rd_matches(self, expected_by_port):
        for p, exp in expected_by_port.items():
            got = int(self.dut.rd_data[p].value)
            exp = self._mask_data(exp)
            assert got == exp, f"rd_data[{p}] mismatch: expected 0x{exp:x}, got 0x{got:x}"

    async def assert_mem_matches(self, model):
        flat_mem = int(self.dut.mem.value)
        for addr, exp in enumerate(model):
            got = (flat_mem >> (addr * self.data_width)) & self.data_mask
            exp = self._mask_data(exp)
            assert got == exp, f"mem[{addr}] mismatch: expected 0x{exp:x}, got 0x{got:x}"


def apply_writes_to_model(model, writes, data_mask):
    """
    Mirrors DUT behavior for one clock edge.
    If multiple write ports target same address in same cycle, data is OR-reduced.
    """
    by_addr_or = {}
    for _port, addr, data in writes:
        by_addr_or[addr] = by_addr_or.get(addr, 0) | (int(data) & data_mask)

    for addr, merged in by_addr_or.items():
        model[addr] = merged & data_mask


@cocotb.test()
async def test_01_clear_and_zero_readback_all_ports(dut):
    tb = InstrQMemTB(dut)
    await tb.initialize()
    await tb.clear_memory()

    model = [0 for _ in range(tb.depth)]
    await tb.assert_mem_matches(model)

    # Read zeros on all ports from different addresses
    addrs = {p: (p % tb.depth) for p in range(tb.rd_ports)}
    await tb.set_read_addresses(addrs)
    await tb.assert_rd_matches({p: 0 for p in range(tb.rd_ports)})


@cocotb.test()
async def test_02_single_port_full_depth_write_read(dut):
    tb = InstrQMemTB(dut)
    await tb.initialize()
    await tb.clear_memory()

    model = [0 for _ in range(tb.depth)]

    for addr in range(tb.depth):
        data = ((addr + 1) * 0x11111111) & tb.data_mask
        writes = [(0, addr, data)]
        apply_writes_to_model(model, writes, tb.data_mask)
        await tb.apply_writes_one_cycle(writes)

        await tb.set_read_addresses({0: addr})
        await tb.assert_rd_matches({0: model[addr]})

    await tb.assert_mem_matches(model)


@cocotb.test()
async def test_03_all_write_ports_unique_addresses_same_cycle(dut):
    tb = InstrQMemTB(dut)
    await tb.initialize()
    await tb.clear_memory()

    model = [0 for _ in range(tb.depth)]

    # Each write port writes a unique address in one cycle
    writes = []
    for p in range(tb.wr_ports):
        addr = p % tb.depth
        data = (0x10 + p) * 0x01010101
        writes.append((p, addr, data))

    apply_writes_to_model(model, writes, tb.data_mask)
    await tb.apply_writes_one_cycle(writes)
    await tb.assert_mem_matches(model)

    # Read back on all read ports
    read_addrs = {p: (p % tb.depth) for p in range(tb.rd_ports)}
    await tb.set_read_addresses(read_addrs)
    await tb.assert_rd_matches({p: model[read_addrs[p]] for p in range(tb.rd_ports)})


@cocotb.test()
async def test_04_subset_write_ports_sparse_pattern(dut):
    tb = InstrQMemTB(dut)
    await tb.initialize()
    await tb.clear_memory()

    model = [0 for _ in range(tb.depth)]
    active_ports = [p for p in range(tb.wr_ports) if p % 2 == 1]

    for cyc in range(6):
        writes = []
        for p in active_ports:
            addr = (cyc + (2 * p)) % tb.depth
            data = (0x55AA0000 | (cyc << 8) | p)
            writes.append((p, addr, data))

        apply_writes_to_model(model, writes, tb.data_mask)
        await tb.apply_writes_one_cycle(writes)
        await tb.assert_mem_matches(model)


@cocotb.test()
async def test_05_all_read_ports_different_addresses(dut):
    tb = InstrQMemTB(dut)
    await tb.initialize()
    await tb.clear_memory()

    model = [0 for _ in range(tb.depth)]

    # Prefill memory deterministically
    for addr in range(tb.depth):
        data = ((addr * 0x12345) ^ 0xA5A5A5A5) & tb.data_mask
        writes = [(0, addr, data)]
        apply_writes_to_model(model, writes, tb.data_mask)
        await tb.apply_writes_one_cycle(writes)

    for base in range(tb.depth):
        read_addrs = {p: (base + p) % tb.depth for p in range(tb.rd_ports)}
        await tb.set_read_addresses(read_addrs)
        await tb.assert_rd_matches({p: model[read_addrs[p]] for p in range(tb.rd_ports)})


@cocotb.test()
async def test_06_subset_read_ports_and_address_mixes(dut):
    tb = InstrQMemTB(dut)
    await tb.initialize()
    await tb.clear_memory()

    model = [0 for _ in range(tb.depth)]

    # Fill memory
    for addr in range(tb.depth):
        data = ((addr + 3) * 0x01020304) & tb.data_mask
        writes = [(0, addr, data)]
        apply_writes_to_model(model, writes, tb.data_mask)
        await tb.apply_writes_one_cycle(writes)

    # Mixed read addresses
    for step in range(8):
        read_addrs = {p: (step + 2 * p) % tb.depth for p in range(tb.rd_ports)}
        await tb.set_read_addresses(read_addrs)

        await tb.assert_rd_matches({p: model[read_addrs[p]] for p in range(tb.rd_ports)})


@cocotb.test()
async def test_07_simultaneous_rw_disjoint_address_sets(dut):
    tb = InstrQMemTB(dut)
    await tb.initialize()
    await tb.clear_memory()

    model = [0 for _ in range(tb.depth)]

    # Initial fill with known values
    for addr in range(tb.depth):
        data = (0x1000 + addr) & tb.data_mask
        writes = [(0, addr, data)]
        apply_writes_to_model(model, writes, tb.data_mask)
        await tb.apply_writes_one_cycle(writes)

    # Read old values while writing new values to disjoint addresses
    write_addrs = list(range(0, tb.depth, 2))
    read_addrs = list(range(1, tb.depth, 2))

    mapped_reads = {p: read_addrs[p % len(read_addrs)] for p in range(tb.rd_ports)}
    await tb.set_read_addresses(mapped_reads)
    await tb.assert_rd_matches({p: model[mapped_reads[p]] for p in range(tb.rd_ports)})

    writes = []
    for p in range(tb.wr_ports):
        addr = write_addrs[p % len(write_addrs)]
        data = (0xDEAD0000 | (p << 8) | addr)
        writes.append((p, addr, data))

    apply_writes_to_model(model, writes, tb.data_mask)
    await tb.apply_writes_one_cycle(writes)

    # Verify written locations changed and read set still correct
    await tb.assert_mem_matches(model)
    await tb.set_read_addresses(mapped_reads)
    await tb.assert_rd_matches({p: model[mapped_reads[p]] for p in range(tb.rd_ports)})


@cocotb.test()
async def test_08_read_write_same_address_cycle_boundary(dut):
    tb = InstrQMemTB(dut)
    await tb.initialize()
    await tb.clear_memory()

    model = [0 for _ in range(tb.depth)]
    target_addr = min(2, tb.depth - 1)

    # Set initial value
    initial_data = 0x12345678 & tb.data_mask
    writes = [(0, target_addr, initial_data)]
    apply_writes_to_model(model, writes, tb.data_mask)
    await tb.apply_writes_one_cycle(writes)

    # Observe old value before edge
    await tb.set_read_addresses({0: target_addr})
    await tb.assert_rd_matches({0: model[target_addr]})

    # Drive a write to same address, then sample after edge
    new_data = 0xCAFEBABE & tb.data_mask
    tb._set_all_writes_idle()
    tb.dut.wr_en[0].value = 1
    tb.dut.wr_addr[0].value = target_addr
    tb.dut.wr_data[0].value = new_data

    await RisingEdge(tb.dut.clk)
    await Timer(1, unit="step")

    model[target_addr] = new_data

    # Combinational output should now reflect new memory content
    await tb.set_read_addresses({0: target_addr})
    await tb.assert_rd_matches({0: model[target_addr]})
    await tb.assert_mem_matches(model)


@cocotb.test()
async def test_09_multiwriter_same_address_or_merge(dut):
    tb = InstrQMemTB(dut)
    await tb.initialize()
    await tb.clear_memory()

    model = [0 for _ in range(tb.depth)]
    addr = min(1, tb.depth - 1)

    # Multiple write ports target same address in same cycle
    writes = []
    patterns = [0x0000000F, 0x000000F0, 0x00000F00, 0x0000F000, 0x00F00000]
    for p in range(tb.wr_ports):
        data = patterns[p % len(patterns)]
        writes.append((p, addr, data))

    apply_writes_to_model(model, writes, tb.data_mask)
    await tb.apply_writes_one_cycle(writes)

    await tb.assert_mem_matches(model)
    await tb.set_read_addresses({0: addr})
    await tb.assert_rd_matches({0: model[addr]})


@cocotb.test()
async def test_10_randomized_multiport_scoreboard(dut):
    tb = InstrQMemTB(dut)
    await tb.initialize()
    await tb.clear_memory()

    seed = 0x1A2B3C4D
    rng = random.Random(seed)

    model = [0 for _ in range(tb.depth)]

    for cycle in range(60):
        # Random read addresses
        read_addrs = {p: rng.randrange(tb.depth) for p in range(tb.rd_ports)}
        await tb.set_read_addresses(read_addrs)

        # Read should always reflect current model at address (combinational)
        await tb.assert_rd_matches({p: model[read_addrs[p]] for p in range(tb.rd_ports)})

        # Random write set for this cycle
        writes = []
        for p in range(tb.wr_ports):
            if rng.random() < 0.7:
                addr = rng.randrange(tb.depth)
                data = rng.getrandbits(tb.data_width)
                writes.append((p, addr, data))

        apply_writes_to_model(model, writes, tb.data_mask)
        await tb.apply_writes_one_cycle(writes)

        # Spot checks each cycle + full memory check periodically
        if tb.depth > 0:
            sample_addr = rng.randrange(tb.depth)
            flat_mem = int(tb.dut.mem.value)
            got = (flat_mem >> (sample_addr * tb.data_width)) & tb.data_mask
            exp = model[sample_addr]
            assert got == exp, (
                f"cycle {cycle}: mem[{sample_addr}] mismatch: expected 0x{exp:x}, got 0x{got:x}"
            )

        if cycle % 10 == 0:
            await tb.assert_mem_matches(model)

    await tb.assert_mem_matches(model)
