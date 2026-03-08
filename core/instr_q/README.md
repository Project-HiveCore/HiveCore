# Description

# Functions

* At reset assertion or upon assertion of the flush signal
  * the port0 read and write pointer
  * flops should asynchronously update to address 0
  * the port1 read and write pointer flops should asynchronously update to address 1
  * When the pointers are reset, we should see the full and almost_full flags deassert, the empty flag should be asserted, and the almost_empty flag should be deasserted.
  * It is not necessary to flush the contents of the FIFO memory as the pointers control the data flow and outbound empty and full flags.
* The FIFO tracks read and write pointers (addresses into the internal memory). These are not exposed to the user but updated according to the read and write enable signals.
  * About the pointers:
    * updated at the rising edge of the clock
    * log2(FIFO_DEPTH)
      + 1 wide addresses
    * FIFO_DEPTH needs to be a power of 2 for the address calculations to be correct
    * An extra MSB bit is added to the address and allows us to determine when the FIFO is full vs empty.
      * empty and full occur when wr/rd pointers are equal, so we need to have another bit to know if we have looped back
  * FIFO is a circular memory
  * Write Side Flags and Usage Rules
    * The full flag is asserted only when there are no slots available to write
    * The almost_full flag is asserted only when there is 1 slot free to
      write
    * wr0_en **must not** be asserted when when full is asserted
    * wr1_en **must not** be asserted when full OR almost_full is asserted
  * Read Side Flags and Usage Rules
    * The empty flag is asserted only when there is no data to read
    * The almost_empty flag is asserted only when there is 1 piece of data
    * rd0_en **must not** be asserted when empty is asserted
    * rd1_en **must not** be asserted when empty OR almost_empty is asserted
  * Write pointer update conditions (assuming no [almost_]full flags are asserted)
    * neither wrX_en signals are asserted --> write pointers stays the same
    * wr0_en asserted, wr1_en not asserted --> write pointer += 1
    * both wrX_en signals asserted --> write pointer += 2
    * wr1_en asserted, wr0_en not asserted --> NOT VALID; write pointers stay the same
      * Will be ignored as we would be writing non-contiguous memory locations breaking program flow
  * Read pointer conditions (assuming no [almost_]empty flags are asserted)
    * neither rdX_en signals are asserted --> read pointer stays the same
    * rd0_en asserted, rd1_en not asserted --> read pointer += 1
    * both rdX_en signals asserted --> read pointer += 2
    * rd1_en asserted, rd0_en not asserted --> NOT VALID; read pointers stay the same
      * Will be ignored as we would be reading non-contiguous memory locations
* Timing
  * The write data and write enable signals must be asserted and stable before the next rising clock edge
  * The read enable signal must be asserted before the next rising clock edge, and the receiver must have captured the data on that rising edge or data will be lost
* Empty and Full Logic
  * Empty:

# IOPorts/Parameters

| Parameters | Description                                                                    |
| ---------- | ------------------------------------------------------------------------------ |
| FIFO_DEPTH | Number of data entires in the FIFO.                                            |
| DATA_WIDTH | Size of the data (can be replaced with a struct representing the data instead) |

| Input Port | Logic Level | Description                                                  |
| ---------- | ----------- | ------------------------------------------------------------ |
| resetn     | Low         | Power-on reset                                               |
| flush      | High        | Flag to flush the FIFO (eg. on misprediction)                |
| clk        | n/a         | Clocksignal for both read and write sides                    |
| instr0_in  | n/a         | Firstinstruction to write (in program order)                 |
| instr1_in  | n/a         | Secondinstruction to write (in program order)                |
| wr0_en     | High        | Indicates the producer intends to write to port/pointer 0    |
| wr1_en     | High        | Indicates the producer intends to write to port/pointer 1    |
| rd0_en     | High        | Indicates the consumer is reading the data at port/pointer 0 |
| rd1_en     | High        | Indicates the consumer is reading the data at port/pointer 1 |

*NOTE*: Asserting wr0/1_en when full or almost full flags are set will cause the FIFO to ignore the write possibly causing data loss for the producer. Asserting rd0/1_en when empty or almost_empty flags are set will not cause data loss or error in the FIFO, but undefined/junk data will be present on the read data lines which can cause errors for the consumer. Check **Functions** section for more details.

| Output			Port | **Logic Level** | **Description**                             |
| ------------- | --------------------- | ------------------------------------------------- |
| instr0_out    | n/a                   | Data for the first instruction to be read         |
| instr1_out    | n/a                   | Data for the second instruction to be read        |
| empty         | High                  | Indicates the FIFO has no readable data           |
| almost_empty  | High                  | Indicates the FIFO has 1 readable data at slot 0  |
| full          | High                  | Indicates the FIFO has no writable space          |
| almost_full   | High                  | Indicates the FIFO has 1 writable space at slot 0 |
