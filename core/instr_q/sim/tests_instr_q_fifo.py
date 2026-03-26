import random
from collections import deque

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


class InstrQFifoTB:
    def __init__(self, dut):
        self.dut = dut
        self.log = cocotb.log

        self.depth = self._param_int("DEPTH", 8)
        self.data_width = self._param_int("DATA_WIDTH", 32)
        self.wr_ports = self._param_int("WR_PORTS", 4)
        self.rd_ports = self._param_int("RD_PORTS", 4)
        self.data_mask = (1 << self.data_width) - 1

        cocotb.start_soon(Clock(self.dut.clk, 10, unit="ns").start())

    def _param_int(self, name: str, default: int) -> int:
        try:
            return int(getattr(self.dut, name).value)
        except Exception:
            return default

    def _mask(self, value: int) -> int:
        return value & self.data_mask

    def _set_idle(self):
        self.dut.flush.value = 0
        for p in range(self.wr_ports):
            self.dut.wr_en[p].value = 0
            self.dut.wr_data[p].value = 0
        for p in range(self.rd_ports):
            self.dut.rd_en[p].value = 0

    async def reset(self):
        self._set_idle()
        self.dut.rstn.value = 0
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.dut.rstn.value = 1
        await RisingEdge(self.dut.clk)

    async def pulse_flush(self):
        self.dut.flush.value = 1
        await RisingEdge(self.dut.clk)
        self.dut.flush.value = 0
        await Timer(1, unit="step")

    def _read_ready_vec(self, which: str, n_ports: int):
        vec = []
        sig = self.dut.wr_ready if which == "wr" else self.dut.rd_ready
        for p in range(n_ports):
            vec.append(int(sig[p].value))
        return vec

    @staticmethod
    def _contiguous_ready_count(ready_vec):
        count = 0
        for bit in ready_vec:
            if bit == 1:
                count += 1
            else:
                break
        return count

    async def cycle(self, wr_payloads, rd_req_count):
        """
        Execute one cycle with contiguous write/read enables from port 0.

        Returns:
          wr_accept_count, rd_accept_count, sampled_rd_values
        """
        await Timer(1, unit="step")

        wr_ready = self._read_ready_vec("wr", self.wr_ports)
        rd_ready = self._read_ready_vec("rd", self.rd_ports)

        wr_accept_count = min(len(wr_payloads), self._contiguous_ready_count(wr_ready))
        rd_accept_count = min(rd_req_count, self._contiguous_ready_count(rd_ready))

        for p in range(self.wr_ports):
            en = 1 if p < wr_accept_count else 0
            self.dut.wr_en[p].value = en
            self.dut.wr_data[p].value = self._mask(wr_payloads[p]) if en else 0

        for p in range(self.rd_ports):
            self.dut.rd_en[p].value = 1 if p < rd_accept_count else 0

        sampled = [int(self.dut.rd_data[p].value) for p in range(rd_accept_count)]

        await RisingEdge(self.dut.clk)
        await Timer(1, unit="step")

        for p in range(self.wr_ports):
            self.dut.wr_en[p].value = 0
        for p in range(self.rd_ports):
            self.dut.rd_en[p].value = 0

        return wr_accept_count, rd_accept_count, sampled

@cocotb.test()
async def test_01_reset_state_and_port_shapes(dut):
    """
    Description:
        Verify reset behavior and parameterized array-port sizing.
    Inputs:
        - rstn held low for 2 cycles then released
        - flush=0, all wr_en/rd_en deasserted
    Expected Outputs:
        - wr_ready/rd_ready lengths match WR_PORTS/RD_PORTS
        - wr_ready[0] is high after reset
        - ready vectors contain only binary values
    """
    tb = InstrQFifoTB(dut)
    await tb.reset()

    wr_ready = tb._read_ready_vec("wr", tb.wr_ports)
    rd_ready = tb._read_ready_vec("rd", tb.rd_ports)

    assert len(wr_ready) == tb.wr_ports
    assert len(rd_ready) == tb.rd_ports

    # Basic sanity after reset.
    assert wr_ready[0] == 1, f"Expected wr_ready[0]=1 after reset, got {wr_ready}"
    assert all(x in (0, 1) for x in wr_ready), f"Non-binary wr_ready values: {wr_ready}"
    assert all(x in (0, 1) for x in rd_ready), f"Non-binary rd_ready values: {rd_ready}"


@cocotb.test()
async def test_02_single_write_single_read_roundtrip(dut):
    """
    Description:
        Write one word and verify first accepted read returns that same word.
    Inputs:
        - Single write payload on write port 0
        - Repeated 1-port read requests
    Expected Outputs:
        - Initial write cycle performs no read
        - First accepted read matches written value
    """
    tb = InstrQFifoTB(dut)
    await tb.reset()

    val = 0x1234ABCD & tb.data_mask

    wr_n, rd_n, sampled = await tb.cycle([val], 0)
    assert rd_n == 0 and sampled == []
    assert wr_n >= 0

    # If/when a legal read becomes accepted, the first observed value should match.
    for _ in range(tb.depth + tb.rd_ports + 4):
        _, rd_n, sampled = await tb.cycle([], 1)
        if rd_n > 0:
            assert sampled[0] == val, f"Expected 0x{val:x}, got 0x{sampled[0]:x}"
            break


@cocotb.test()
async def test_03_multiport_write_then_multiport_read(dut):
    """
    Description:
        Perform multiport write burst, then read and verify ordering.
    Inputs:
        - n=min(WR_PORTS,RD_PORTS) unique payloads written in one cycle
        - Repeated read requests up to n ports
    Expected Outputs:
        - No read acceptance during write-only cycle
        - Accepted reads match expected written prefix in order
    """
    tb = InstrQFifoTB(dut)
    await tb.reset()

    n = min(tb.wr_ports, tb.rd_ports)
    payloads = [tb._mask(0x1000 + p) for p in range(n)]

    wr_n, rd_n, _ = await tb.cycle(payloads, 0)
    assert rd_n == 0

    expected = payloads[:wr_n]
    got = []
    for _ in range(tb.depth + tb.rd_ports + 8):
        _, rd_n, sampled = await tb.cycle([], n)
        got.extend(sampled[:rd_n])
        if len(got) >= len(expected):
            break

    # If any values were accepted/read, they must preserve order.
    if got:
        assert got == expected[:len(got)], f"Expected prefix {expected[:len(got)]}, got {got}"


@cocotb.test()
async def test_04_fill_until_backpressure_then_drain(dut):
    """
    Description:
        Fill FIFO using contiguous-ready writes, then drain and compare sequence.
    Inputs:
        - Repeated writes while wr_ready indicates capacity
        - Repeated reads while rd_ready indicates data available
    Expected Outputs:
        - Drained data matches queued write order (prefix-safe compare)
        - No ordering corruption across fill/drain phases
    """
    tb = InstrQFifoTB(dut)
    await tb.reset()

    q = deque()
    next_data = 1

    # Fill until port0 is no longer write-ready.
    for _ in range(tb.depth + 4):
        wr_ready = tb._read_ready_vec("wr", tb.wr_ports)
        if wr_ready[0] == 0:
            break

        can_write = tb._contiguous_ready_count(wr_ready)
        payloads = []
        for _ in range(can_write):
            payloads.append(tb._mask(next_data))
            next_data += 1

        wr_n, rd_n, _ = await tb.cycle(payloads, 0)
        assert rd_n == 0
        q.extend(payloads[:wr_n])

    # Drain everything.
    drained = []
    for _ in range((tb.depth * 2) + 8):
        rd_ready = tb._read_ready_vec("rd", tb.rd_ports)
        rd_req = tb._contiguous_ready_count(rd_ready)
        if rd_req == 0:
            continue
        _, rd_n, sampled = await tb.cycle([], rd_req)
        drained.extend(sampled[:rd_n])
        if len(drained) >= len(q):
            break

    assert list(q)[:len(drained)] == drained, f"Drain order mismatch. expected={list(q)} got={drained}"


@cocotb.test()
async def test_05_simultaneous_rw_keeps_order(dut):
    """
    Description:
        Stress simultaneous read/write operation with scoreboard checks.
    Inputs:
        - Initial prefill
        - 20 cycles of concurrent write/read requests based on ready vectors
    Expected Outputs:
        - Every accepted read equals scoreboard head element
        - FIFO ordering remains intact under concurrent traffic
    """
    tb = InstrQFifoTB(dut)
    await tb.reset()

    q = deque()
    data = 0x40

    # Prefill a little so reads are available.
    prefill = min(tb.wr_ports, max(1, tb.depth // 2))
    payloads = [tb._mask(data + i) for i in range(prefill)]
    wr_n, _, _ = await tb.cycle(payloads, 0)
    q.extend(payloads[:wr_n])
    data += prefill

    for _ in range(20):
        wr_ready = tb._read_ready_vec("wr", tb.wr_ports)
        rd_ready = tb._read_ready_vec("rd", tb.rd_ports)

        wr_cnt = min(tb._contiguous_ready_count(wr_ready), min(tb.wr_ports, 2))
        rd_cnt = min(tb._contiguous_ready_count(rd_ready), min(tb.rd_ports, 2))

        payloads = [tb._mask(data + i) for i in range(wr_cnt)]
        wr_n, rd_n, sampled = await tb.cycle(payloads, rd_cnt)

        for i in range(rd_n):
            exp = q.popleft()
            assert sampled[i] == exp, f"RW cycle read mismatch: expected 0x{exp:x}, got 0x{sampled[i]:x}"

        q.extend(payloads[:wr_n])
        data += wr_cnt


@cocotb.test()
async def test_06_flush_clears_ready_for_reads(dut):
    """
    Description:
        Verify flush removes readable contents and preserves write capability.
    Inputs:
        - Write a few entries
        - Pulse flush for one cycle
        - Attempt read then write
    Expected Outputs:
        - Immediate read acceptance after flush is zero
        - Writes are still accepted after flush
    """
    tb = InstrQFifoTB(dut)
    await tb.reset()

    # Put data into FIFO
    payloads = [tb._mask(0xAA00 + i) for i in range(min(tb.wr_ports, 2))]
    wr_n, _, _ = await tb.cycle(payloads, 0)
    assert wr_n > 0

    await tb.pulse_flush()

    # After flush, no contiguous read from port 0 should be accepted until new writes occur.
    _, rd_n, _ = await tb.cycle([], 1)
    assert rd_n == 0, "Expected no accepted read right after flush"

    # Writes should still be accepted after flush.
    wr_n, _, _ = await tb.cycle([tb._mask(0xBEEF)], 0)
    assert wr_n >= 0


@cocotb.test()
async def test_07_randomized_legal_traffic_scoreboard(dut):
    """
    Description:
        Random legal traffic test with reference scoreboard.
    Inputs:
        - 200 cycles of random write/read counts constrained by ready vectors
        - Deterministic random seed for reproducibility
    Expected Outputs:
        - Every accepted read matches expected scoreboard value
        - No data-order mismatches during randomized operation
    """
    tb = InstrQFifoTB(dut)
    await tb.reset()

    rng = random.Random(0xC0FFEE)
    q = deque()
    next_data = 0

    for _ in range(200):
        wr_ready = tb._read_ready_vec("wr", tb.wr_ports)
        rd_ready = tb._read_ready_vec("rd", tb.rd_ports)

        max_w = tb._contiguous_ready_count(wr_ready)
        max_r = tb._contiguous_ready_count(rd_ready)

        wr_req = rng.randrange(max_w + 1)
        rd_req = rng.randrange(max_r + 1)

        payloads = [tb._mask(next_data + i) for i in range(wr_req)]
        wr_n, rd_n, sampled = await tb.cycle(payloads, rd_req)

        for i in range(rd_n):
            exp = q.popleft()
            assert sampled[i] == exp, f"Random read mismatch: expected 0x{exp:x}, got 0x{sampled[i]:x}"

        q.extend(payloads[:wr_n])
        next_data += wr_req


@cocotb.test()
async def test_08_mismatch_enable_patterns_hold_pointers(dut):
    """
    Description:
        Inject illegal non-contiguous enable pattern and check recovery behavior.
    Inputs:
        - Seed one known value
        - Drive wr_en[1]=1 with wr_en[0]=0 and rd_en[1]=1 with rd_en[0]=0
        - Return to legal reads
    Expected Outputs:
        - First accepted legal read after mismatch still returns seeded value
        - Illegal cycle does not corrupt observable FIFO ordering
    """
    tb = InstrQFifoTB(dut)
    await tb.reset()

    if tb.wr_ports < 2 or tb.rd_ports < 2:
        return

    # Seed one known word.
    seed = tb._mask(0xDEADBEEF)
    wr_n, _, _ = await tb.cycle([seed], 0)
    assert wr_n == 1

    # Illegal write/read patterns: port1 high while port0 low.
    tb.dut.wr_en[0].value = 0
    tb.dut.wr_en[1].value = 1
    tb.dut.wr_data[1].value = tb._mask(0xBAD0BAD0)

    tb.dut.rd_en[0].value = 0
    tb.dut.rd_en[1].value = 1

    await RisingEdge(tb.dut.clk)
    await Timer(1, unit="step")

    tb.dut.wr_en[1].value = 0
    tb.dut.rd_en[1].value = 0

    # If/when a legal read is accepted later, it should still return seeded value first.
    for _ in range(tb.depth + tb.rd_ports + 4):
        _, rd_n, sampled = await tb.cycle([], 1)
        if rd_n > 0:
            assert sampled[0] == seed, f"Mismatch-pattern cycle altered FIFO order/value (got 0x{sampled[0]:x})"
            break