# Description

`instr_q_fifo` is a synchronous FIFO for the instruction queue with a parameterizable number of write ports, read ports, entries, and data width.

The interface is based on:

- per-port write readiness: `wr_ready[WR_PORTS]`
- per-port read readiness: `rd_ready[RD_PORTS]`
- write-side error reporting: `wr_error`
- read-side error reporting: `rd_error`

Writes and reads are expected to be **contiguous from port 0 upward**. Port 0 always corresponds to the oldest readable entry on the read side and the next writable slot on the write side.

# Functions

## Reset and Flush Behavior

- On the next rising edge of `clk`, if `rstn` is low or `flush` is high:
  - `wr_ptr[i]` resets to `i`
  - `rd_ptr[i]` resets to `i`
- This returns the FIFO to an empty state:
  - all  `rd_ready` signals deassert
  - all  `wr_ready` signals assert
- FIFO memory contents are **not** cleared during reset/flush. Pointer reset alone controls visible FIFO state.

## Parameters and Internal Pointer Rules

- `DEPTH` must be a power of 2 in `{2, 4, 8, 16, 32, 64, 128, 256}`
- `RD_PORTS <= DEPTH`
- `WR_PORTS <= DEPTH`
- Internal read/write pointers are `$clog2(DEPTH) + 1` bits wide
- The extra MSB is a wrap/augment bit used to distinguish full vs empty when addresses match
- The FIFO operates as a circular buffer

## Write Side Rules

- `wr_ready[i]` indicates that write port `i` may be used in the current cycle
- A write request must be contiguous from port 0 upward:
  - valid: `wr_en[0]`
  - valid: `wr_en[0]` and `wr_en[1]`
  - invalid: `wr_en[1]` asserted while `wr_en[0]` is deasserted
- If any enabled write targets a port where `wr_ready[i] == 0`, a write overflow occurs
- Any non-contiguous write enable pattern also causes a write-side error
- `wr_error` asserts for either:
  - non-contiguous write enables
  - too many writes for the available FIFO space
- On `wr_error`:
  - write pointers do not advance
  - memory writes are blocked

## Read Side Rules

- `rd_ready[i]` indicates that read port `i` has valid FIFO data available in the current cycle
- A read request must be contiguous from port 0 upward:
  - valid: `rd_en[0]`
  - valid: `rd_en[0]` and `rd_en[1]`
  - invalid: `rd_en[1]` asserted while `rd_en[0]` is deasserted
- If any enabled read targets a port where `rd_ready[i] == 0`, a read underflow occurs
- Any non-contiguous read enable pattern also causes a read-side error
- `rd_error` asserts for either:
  - non-contiguous read enables
  - too many reads for the available FIFO contents
- On `rd_error`:
  - read pointers do not advance
  - output data is not valid and behavior is undefined

## Pointer Update Behavior

For either side, if the enables are contiguous and there is no side-specific error:

- no enables asserted -> pointers stay the same
- enables asserted through port `N` -> pointers advance by `N + 1`

Examples:

- `wr_en[0] = 1` only -> write side pointers advance by 1
- `wr_en[0] = 1`, `wr_en[1] = 1`, `wr_en[2] = 1` -> write side pointers advance by 3
- same rule applies to `rd_en`

## Timing

- `wr_en` and `wr_data` must be valid before the rising edge of `clk`
- `rd_en` must be valid before the rising edge of `clk`
- `rd_data[i]` is driven from the FIFO memory at the current read pointer address for port `i`
- Consumers should only treat `rd_data[i]` as valid when the corresponding read is intended and `rd_ready[i]` is asserted
  - The data for any read is valid until the next rising edge of `clk`

# IO Ports/Parameters

| Parameter      | Description                                            |
| -------------- | ------------------------------------------------------ |
| `RD_PORTS`   | Number of independent read ports                       |
| `WR_PORTS`   | Number of independent write ports                      |
| `DEPTH`      | Number of FIFO entries; must be a supported power of 2 |
| `DATA_WIDTH` | Width of each FIFO entry                               |

| Input Port            | Logic Level | Description                                        |
| --------------------- | ----------- | -------------------------------------------------- |
| `clk`               | n/a         | Shared clock for both FIFO sides                   |
| `rstn`              | Low         | Active-low synchronous reset                       |
| `flush`             | High        | Synchronous FIFO flush; resets internal pointers   |
| `wr_en[WR_PORTS]`   | High        | Contiguous write enables starting at port 0        |
| `wr_data[WR_PORTS]` | n/a         | Write data for each enabled port, in program order |
| `rd_en[RD_PORTS]`   | High        | Contiguous read enables starting at port 0         |

| Output Port            | Logic Level | Description                                          |
| ---------------------- | ----------- | ---------------------------------------------------- |
| `wr_ready[WR_PORTS]` | High        | Indicates which write ports may be used this cycle   |
| `wr_error`           | High        | Write-side error: non-contiguous enables or overflow |
| `rd_ready[RD_PORTS]` | High        | Indicates which read ports have valid data available |
| `rd_data[RD_PORTS]`  | n/a         | Read data for each read port                         |
| `rd_error`           | High        | Read-side error: non-contiguous enables or underflow |

## Usage

Upstream/downstream logic should:

- only assert enables on ports where the corresponding `*_ready` signal is high
- only assert enables contiguously from port 0 upward
- treat `wr_error` and `rd_error` as invalid transaction indicators for that cycle
