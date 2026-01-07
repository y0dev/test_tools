----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 
-- Design Name: AXI Read/Write Slave Module (Full AXI4)
-- Module Name: axi_read_write_slave_full_v1_0_S00_AXI - Behavioral
-- Project Name: Xilinx MPSoC Vivado Project
-- Target Devices: Xilinx Zynq-7000 / Zynq UltraScale+ MPSoC
-- Tool Versions: Vivado 2018.3 or later
-- Description: 
--   AXI4-Full slave interface that allows software to read and write data
--   to memory-mapped registers and Block RAM in the programmable logic.
--   This module implements burst transaction support, allowing multiple
--   data transfers per transaction with configurable address increment
--   modes (fixed, incremental, wrapping).
-- 
-- Dependencies: 
-- 
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
--   This module implements an AXI4-Full slave with:
--   - Burst transaction support (up to 256 beats)
--   - Fixed, incremental, and wrapping address modes
--   - Block RAM for user data storage
--   - Register bank for control/status
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

----------------------------------------------------------------------------------
-- ENTITY: axi_read_write_slave_full_v1_0_S00_AXI
-- 
-- PURPOSE: This entity implements an AXI4-Full slave interface that allows
--          software running on the ARM processors in the PS (Processing System)
--          to perform burst read and write transactions to memory in the PL
--          (Programmable Logic). Unlike AXI4-Lite, AXI4-Full supports burst
--          transactions, allowing multiple data transfers per transaction.
--
-- AXI4-FULL OVERVIEW:
--   AXI4-Full is a complete AXI protocol with:
--   - Burst transaction support (multiple data transfers per address)
--   - Variable data widths (8, 16, 32, 64, 128, 256, 512, or 1024 bits)
--   - Burst types: Fixed, Incremental, Wrapping
--   - ID-based transaction ordering
--   - QoS and region support
--   - Uses VALID/READY handshaking on all channels
--
-- WRITE TRANSACTION FLOW (Burst):
--   1. Write Address Channel: Master sends address (AWADDR), burst length (AWLEN),
--      burst size (AWSIZE), burst type (AWBURST), and AWVALID
--   2. Write Data Channel: Master sends multiple data beats (WDATA), one per clock
--      cycle, with WLAST asserted on the final beat, and WVALID for each beat
--   3. Write Response Channel: Slave responds with BRESP when all data beats are
--      received and processed
--
-- READ TRANSACTION FLOW (Burst):
--   1. Read Address Channel: Master sends address (ARADDR), burst length (ARLEN),
--      burst size (ARSIZE), burst type (ARBURST), and ARVALID
--   2. Read Data Channel: Slave responds with multiple data beats (RDATA), one
--      per clock cycle, with RLAST asserted on the final beat, and RVALID for
--      each beat
--
-- BURST TYPES:
--   - FIXED ("00"): Address remains constant for all beats (same location)
--   - INCR ("01"): Address increments by burst size for each beat
--   - WRAP ("10"): Address wraps at a boundary (useful for cache line fills)
--
-- BURST LENGTH:
--   - AWLEN/ARLEN: 8-bit value (0-255), but AXI4 allows 1-256 beats
--   - Burst length = AWLEN + 1 (e.g., AWLEN=0 means 1 beat, AWLEN=255 means 256 beats)
----------------------------------------------------------------------------------
entity axi_read_write_slave_full_v1_0_S00_AXI is
    generic (
        -- Users to add parameters here

        -- User parameters ends
        -- Do not modify the parameters beyond this line

        -- Width of ID for for write address, write data, read address and read data
        -- Used for transaction ordering and tracking multiple outstanding transactions
        C_S_AXI_ID_WIDTH      : integer := 1;
        -- Width of S_AXI data bus (typically 32, 64, or 128 bits)
        -- Must be 8, 16, 32, 64, 128, 256, 512, or 1024
        C_S_AXI_DATA_WIDTH    : integer := 32;
        -- Width of S_AXI address bus
        -- Determines the maximum addressable memory space
        C_S_AXI_ADDR_WIDTH    : integer := 6;
        -- Width of optional user defined signal in write address channel
        -- Not commonly used, typically set to 0
        C_S_AXI_AWUSER_WIDTH  : integer := 0;
        -- Width of optional user defined signal in read address channel
        -- Not commonly used, typically set to 0
        C_S_AXI_ARUSER_WIDTH  : integer := 0;
        -- Width of optional user defined signal in write data channel
        -- Not commonly used, typically set to 0
        C_S_AXI_WUSER_WIDTH   : integer := 0;
        -- Width of optional user defined signal in read data channel
        -- Not commonly used, typically set to 0
        C_S_AXI_RUSER_WIDTH   : integer := 0;
        -- Width of optional user defined signal in write response channel
        -- Not commonly used, typically set to 0
        C_S_AXI_BUSER_WIDTH   : integer := 0
    );
    port (
        -- Users to add ports here

        -- User ports ends
        -- Do not modify the ports beyond this line

        --------------------------------------------------------------------------
        -- AXI4-Full Global Signals
        --------------------------------------------------------------------------
        -- Global Clock Signal - All AXI signals are synchronous to this clock
        S_AXI_ACLK    : in std_logic;
        -- Global Reset Signal. This Signal is Active LOW
        -- When asserted, all state machines and registers are reset
        S_AXI_ARESETN : in std_logic;

        --------------------------------------------------------------------------
        -- AXI4-Full Write Address Channel (AW Channel)
        -- Master drives: AWID, AWADDR, AWLEN, AWSIZE, AWBURST, AWLOCK, AWCACHE,
        --                AWPROT, AWQOS, AWREGION, AWUSER, AWVALID
        -- Slave drives: AWREADY
        --------------------------------------------------------------------------
        -- Write Address ID - Used for transaction ordering
        S_AXI_AWID    : in std_logic_vector(C_S_AXI_ID_WIDTH-1 downto 0);
        -- Write address (byte address) - Starting address for the burst
        S_AXI_AWADDR  : in std_logic_vector(C_S_AXI_ADDR_WIDTH-1 downto 0);
        -- Burst length. The burst length gives the exact number of transfers in a burst
        -- Burst length = AWLEN + 1 (AWLEN=0 means 1 transfer, AWLEN=255 means 256 transfers)
        S_AXI_AWLEN   : in std_logic_vector(7 downto 0);
        -- Burst size. This signal indicates the size of each transfer in the burst
        -- "000"=1 byte, "001"=2 bytes, "010"=4 bytes, "011"=8 bytes, etc.
        S_AXI_AWSIZE  : in std_logic_vector(2 downto 0);
        -- Burst type. The burst type and the size information,
        -- determine how the address for each transfer within the burst is calculated.
        -- "00"=FIXED, "01"=INCR, "10"=WRAP, "11"=reserved
        S_AXI_AWBURST : in std_logic_vector(1 downto 0);
        -- Lock type. Provides additional information about the
        -- atomic characteristics of the transfer.
        -- '0'=Normal access, '1'=Exclusive access
        S_AXI_AWLOCK  : in std_logic;
        -- Memory type. This signal indicates how transactions
        -- are required to progress through a system.
        -- Used for cache attributes: bufferable, cacheable, write-through, etc.
        S_AXI_AWCACHE : in std_logic_vector(3 downto 0);
        -- Protection type. This signal indicates the privilege
        -- and security level of the transaction, and whether
        -- the transaction is a data access or an instruction access.
        S_AXI_AWPROT  : in std_logic_vector(2 downto 0);
        -- Quality of Service, QoS identifier sent for each
        -- write transaction.
        -- Used for transaction priority and bandwidth allocation
        S_AXI_AWQOS   : in std_logic_vector(3 downto 0);
        -- Region identifier. Permits a single physical interface
        -- on a slave to be used for multiple logical interfaces.
        S_AXI_AWREGION : in std_logic_vector(3 downto 0);
        -- Optional User-defined signal in the write address channel.
        S_AXI_AWUSER  : in std_logic_vector(C_S_AXI_AWUSER_WIDTH-1 downto 0);
        -- Write address valid. This signal indicates that
        -- the channel is signaling valid write address and
        -- control information.
        S_AXI_AWVALID : in std_logic;
        -- Write address ready. This signal indicates that
        -- the slave is ready to accept an address and associated
        -- control signals.
        S_AXI_AWREADY : out std_logic;

        --------------------------------------------------------------------------
        -- AXI4-Full Write Data Channel (W Channel)
        -- Master drives: WDATA, WSTRB, WLAST, WUSER, WVALID
        -- Slave drives: WREADY
        --------------------------------------------------------------------------
        -- Write Data - Data to be written (one beat per clock cycle in burst)
        S_AXI_WDATA   : in std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
        -- Write strobes. This signal indicates which byte
        -- lanes hold valid data. There is one write strobe
        -- bit for each eight bits of the write data bus.
        -- For 32-bit data: WSTRB[3:0] controls bytes [31:24], [23:16], [15:8], [7:0]
        S_AXI_WSTRB   : in std_logic_vector((C_S_AXI_DATA_WIDTH/8)-1 downto 0);
        -- Write last. This signal indicates the last transfer
        -- in a write burst. Must be asserted on the final data beat.
        S_AXI_WLAST   : in std_logic;
        -- Optional User-defined signal in the write data channel.
        S_AXI_WUSER   : in std_logic_vector(C_S_AXI_WUSER_WIDTH-1 downto 0);
        -- Write valid. This signal indicates that valid write
        -- data and strobes are available.
        -- Asserted for each data beat in the burst
        S_AXI_WVALID  : in std_logic;
        -- Write ready. This signal indicates that the slave
        -- can accept the write data.
        -- Slave asserts when ready to accept the current data beat
        S_AXI_WREADY  : out std_logic;

        --------------------------------------------------------------------------
        -- AXI4-Full Write Response Channel (B Channel)
        -- Master drives: BREADY
        -- Slave drives: BID, BRESP, BUSER, BVALID
        --------------------------------------------------------------------------
        -- Response ID tag. This signal is the ID tag of the
        -- write response. Must match the AWID from the address channel.
        S_AXI_BID     : out std_logic_vector(C_S_AXI_ID_WIDTH-1 downto 0);
        -- Write response. This signal indicates the status
        -- of the write transaction.
        -- "00"=OKAY (success), "01"=EXOKAY (exclusive okay),
        -- "10"=SLVERR (slave error), "11"=DECERR (decode error)
        S_AXI_BRESP   : out std_logic_vector(1 downto 0);
        -- Optional User-defined signal in the write response channel.
        S_AXI_BUSER   : out std_logic_vector(C_S_AXI_BUSER_WIDTH-1 downto 0);
        -- Write response valid. This signal indicates that the
        -- channel is signaling a valid write response.
        -- Asserted after all data beats are received and processed
        S_AXI_BVALID  : out std_logic;
        -- Response ready. This signal indicates that the master
        -- can accept a write response.
        S_AXI_BREADY  : in std_logic;

        --------------------------------------------------------------------------
        -- AXI4-Full Read Address Channel (AR Channel)
        -- Master drives: ARID, ARADDR, ARLEN, ARSIZE, ARBURST, ARLOCK, ARCACHE,
        --                ARPROT, ARQOS, ARREGION, ARUSER, ARVALID
        -- Slave drives: ARREADY
        --------------------------------------------------------------------------
        -- Read address ID - Used for transaction ordering
        S_AXI_ARID    : in std_logic_vector(C_S_AXI_ID_WIDTH-1 downto 0);
        -- Read address. This signal indicates the initial
        -- address of a read burst transaction.
        S_AXI_ARADDR  : in std_logic_vector(C_S_AXI_ADDR_WIDTH-1 downto 0);
        -- Burst length. The burst length gives the exact number of transfers in a burst
        -- Burst length = ARLEN + 1
        S_AXI_ARLEN   : in std_logic_vector(7 downto 0);
        -- Burst size. This signal indicates the size of each transfer in the burst
        S_AXI_ARSIZE  : in std_logic_vector(2 downto 0);
        -- Burst type. The burst type and the size information,
        -- determine how the address for each transfer within the burst is calculated.
        S_AXI_ARBURST : in std_logic_vector(1 downto 0);
        -- Lock type. Provides additional information about the
        -- atomic characteristics of the transfer.
        S_AXI_ARLOCK  : in std_logic;
        -- Memory type. This signal indicates how transactions
        -- are required to progress through a system.
        S_AXI_ARCACHE : in std_logic_vector(3 downto 0);
        -- Protection type. This signal indicates the privilege
        -- and security level of the transaction, and whether
        -- the transaction is a data access or an instruction access.
        S_AXI_ARPROT  : in std_logic_vector(2 downto 0);
        -- Quality of Service, QoS identifier sent for each
        -- read transaction.
        S_AXI_ARQOS   : in std_logic_vector(3 downto 0);
        -- Region identifier. Permits a single physical interface
        -- on a slave to be used for multiple logical interfaces.
        S_AXI_ARREGION : in std_logic_vector(3 downto 0);
        -- Optional User-defined signal in the read address channel.
        S_AXI_ARUSER  : in std_logic_vector(C_S_AXI_ARUSER_WIDTH-1 downto 0);
        -- Read address valid. This signal indicates that
        -- the channel is signaling valid read address and
        -- control information.
        S_AXI_ARVALID : in std_logic;
        -- Read address ready. This signal indicates that
        -- the slave is ready to accept an address and associated
        -- control signals.
        S_AXI_ARREADY : out std_logic;

        --------------------------------------------------------------------------
        -- AXI4-Full Read Data Channel (R Channel)
        -- Master drives: RREADY
        -- Slave drives: RID, RDATA, RRESP, RLAST, RUSER, RVALID
        --------------------------------------------------------------------------
        -- Read ID tag. This signal is the identification tag
        -- for the read data group of signals generated by the slave.
        -- Must match the ARID from the address channel.
        S_AXI_RID     : out std_logic_vector(C_S_AXI_ID_WIDTH-1 downto 0);
        -- Read Data - Data read from memory (one beat per clock cycle in burst)
        S_AXI_RDATA   : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
        -- Read response. This signal indicates the status of
        -- the read transfer.
        -- "00"=OKAY, "01"=EXOKAY, "10"=SLVERR, "11"=DECERR
        S_AXI_RRESP   : out std_logic_vector(1 downto 0);
        -- Read last. This signal indicates the last transfer
        -- in a read burst. Must be asserted on the final data beat.
        S_AXI_RLAST   : out std_logic;
        -- Optional User-defined signal in the read address channel.
        S_AXI_RUSER   : out std_logic_vector(C_S_AXI_RUSER_WIDTH-1 downto 0);
        -- Read valid. This signal indicates that the channel
        -- is signaling the required read data.
        -- Asserted for each data beat in the burst
        S_AXI_RVALID  : out std_logic;
        -- Read ready. This signal indicates that the master can
        -- accept the read data and response information.
        S_AXI_RREADY  : in std_logic
    );
end axi_read_write_slave_full_v1_0_S00_AXI;

----------------------------------------------------------------------------------
-- ARCHITECTURE: arch_imp
-- 
-- IMPLEMENTATION OVERVIEW:
--   This architecture implements the AXI4-Full slave protocol through multiple
--   synchronous processes, each handling a specific part of the protocol:
--   1. Write State Machine - Handles write address and data channel coordination
--   2. Read State Machine - Handles read address and data channel coordination
--   3. Write Address Increment Logic - Calculates address for each burst beat
--   4. Read Address Increment Logic - Calculates address for each burst beat
--   5. Memory Generation - Block RAM for user data storage
--
-- KEY DIFFERENCES FROM AXI4-LITE:
--   - Supports burst transactions (multiple data transfers per address)
--   - Must track burst length and current beat number
--   - Must handle address increment/wrap for each beat
--   - Must assert WLAST/RLAST on final beat
--   - State machines coordinate address and data channels across multiple beats
--
-- ADDRESS DECODING:
--   - ADDR_LSB = 2 (addresses are byte-aligned, but we use 4-byte word boundaries)
--   - OPT_MEM_ADDR_BITS = 3 (supports 2^3 = 8 memory locations)
--   - Address mapping depends on user logic requirements
--
-- BURST TRANSACTION HANDLING:
--   - Burst length counter (awlen_cntr/arlen_cntr) tracks current beat number
--   - Address is incremented/wrapped based on burst type for each beat
--   - WLAST/RLAST is asserted when counter reaches final beat
--   - State machines ensure proper handshaking across all beats
----------------------------------------------------------------------------------
architecture arch_imp of axi_read_write_slave_full_v1_0_S00_AXI is

    --------------------------------------------------------------------------
    -- Internal AXI4-Full Interface Signals
    -- These are internal copies of the AXI interface signals for processing
    --------------------------------------------------------------------------
    -- Write Address Channel Internal Signals
    signal axi_awaddr  : std_logic_vector(C_S_AXI_ADDR_WIDTH-1 downto 0);  -- Latched write address (incremented during burst)
    signal axi_awready : std_logic;  -- Internal write address ready signal
    signal axi_wready  : std_logic;  -- Internal write data ready signal
    
    -- Write Response Channel Internal Signals
    signal axi_bid     : std_logic_vector(C_S_AXI_ID_WIDTH-1 downto 0);  -- Internal write response ID
    signal axi_bresp   : std_logic_vector(1 downto 0);  -- Internal write response
    signal axi_buser   : std_logic_vector(C_S_AXI_BUSER_WIDTH-1 downto 0);  -- Internal write response user
    signal axi_bvalid  : std_logic;  -- Internal write response valid
    
    -- Read Address Channel Internal Signals
    signal axi_araddr  : std_logic_vector(C_S_AXI_ADDR_WIDTH-1 downto 0);  -- Latched read address (incremented during burst)
    signal axi_arready : std_logic;  -- Internal read address ready signal
    
    -- Read Data Channel Internal Signals
    signal axi_rid     : std_logic_vector(C_S_AXI_ID_WIDTH-1 downto 0);  -- Internal read response ID
    signal axi_rresp   : std_logic_vector(1 downto 0);  -- Internal read response
    signal axi_rlast   : std_logic;  -- Internal read last signal (asserted on final beat)
    signal axi_ruser   : std_logic_vector(C_S_AXI_RUSER_WIDTH-1 downto 0);  -- Internal read response user
    signal axi_rvalid  : std_logic;  -- Internal read data valid

    --------------------------------------------------------------------------
    -- Burst Transaction Control Signals
    -- Used for managing multi-beat burst transactions
    --------------------------------------------------------------------------
    -- Wrapping enable signals - determine when address wraps at boundary
    -- aw_wrap_en determines wrap boundary and enables wrapping for write bursts
    signal aw_wrap_en : std_logic;
    -- ar_wrap_en determines wrap boundary and enables wrapping for read bursts
    signal ar_wrap_en : std_logic;
    
    -- Wrap size calculation - size of transfer in bytes for wrap boundary detection
    -- aw_wrap_size is the size of the write transfer, the
    -- write address wraps to a lower address if upper address limit is reached
    signal aw_wrap_size : integer;
    -- ar_wrap_size is the size of the read transfer, the
    -- read address wraps to a lower address if upper address limit is reached
    signal ar_wrap_size : integer;
    
    -- Burst length counters - track current beat number within a burst
    -- The axi_awlen_cntr internal write address counter to keep track of beats in a burst transaction
    signal axi_awlen_cntr : std_logic_vector(7 downto 0);
    -- The axi_arlen_cntr internal read address counter to keep track of beats in a burst transaction
    signal axi_arlen_cntr : std_logic_vector(7 downto 0);
    
    -- Latched burst control signals - captured from address channel and used throughout burst
    signal axi_arburst : std_logic_vector(2-1 downto 0);  -- Read burst type (FIXED, INCR, WRAP)
    signal axi_awburst : std_logic_vector(2-1 downto 0);  -- Write burst type (FIXED, INCR, WRAP)
    signal axi_arlen   : std_logic_vector(8-1 downto 0);  -- Read burst length (ARLEN value)
    signal axi_awlen   : std_logic_vector(8-1 downto 0);  -- Write burst length (AWLEN value)

    --------------------------------------------------------------------------
    -- Address Decoding Constants
    -- Used to extract register/memory address from AXI address bus
    --------------------------------------------------------------------------
    -- local parameter for addressing 32 bit / 64 bit C_S_AXI_DATA_WIDTH
    -- ADDR_LSB is used for addressing 32/64 bit registers/memories
    -- ADDR_LSB = 2 for 32 bits (n downto 2) - skips byte address bits [1:0]
    -- ADDR_LSB = 3 for 64 bits (n downto 3) - skips byte address bits [2:0]
    -- ADDR_LSB = 4 for 128 bits (n downto 4) - skips byte address bits [3:0]
    constant ADDR_LSB          : integer := (C_S_AXI_DATA_WIDTH/32) + 1;
    constant OPT_MEM_ADDR_BITS : integer := 3;  -- Number of address bits for memory selection (2^3 = 8 locations)
    constant USER_NUM_MEM      : integer := 1;  -- Number of memory blocks to generate
    -- Low address constant used for wrap boundary detection
    constant low               : std_logic_vector(C_S_AXI_ADDR_WIDTH - 1 downto 0) := "000000";

    ----------------------------------------------------------------------------
    -- User Registers
    -- These registers are accessible via AXI writes/reads
    ----------------------------------------------------------------------------
    signal slv_reg0 : std_logic_vector(31 downto 0); -- CTRL - Control register
    signal slv_reg1 : std_logic_vector(31 downto 0); -- STATUS - Status register

    ----------------------------------------------------------------
    -- Signals for user logic memory space example
    -- Block RAM implementation for data storage
    ----------------------------------------------------------------
    -- Memory address signals - extracted from AXI address for read/write operations
    signal mem_address_read  : std_logic_vector(OPT_MEM_ADDR_BITS downto 0);  -- Read address for memory
    signal mem_address_write : std_logic_vector(OPT_MEM_ADDR_BITS downto 0);  -- Write address for memory
    
    -- Memory data array - stores data in Block RAM
    type word_array is array (0 to USER_NUM_MEM-1) of std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
    signal mem_data_out : word_array;  -- Memory output data

    -- Loop/generate statement variables
    signal i            : integer;  -- Loop variable for memory generation
    signal j            : integer;  -- Loop variable (unused but declared)
    signal mem_byte_index : integer;  -- Loop variable for byte lane generation
    
    -- Block RAM type definition - byte-addressable memory array
    type BYTE_RAM_TYPE is array (0 to 15) of std_logic_vector(7 downto 0);

    --------------------------------------------------------------------------
    -- State Machine Definitions
    --------------------------------------------------------------------------
    -- State machine local parameters - define states for write and read FSMs
    constant Idle  : std_logic_vector(1 downto 0) := "00";  -- Idle state - ready for new transaction
    constant Raddr : std_logic_vector(1 downto 0) := "10";  -- Read address state - accepting read address
    constant Rdata : std_logic_vector(1 downto 0) := "11";  -- Read data state - sending read data beats
    constant Waddr : std_logic_vector(1 downto 0) := "10";  -- Write address state - accepting write address
    constant Wdata : std_logic_vector(1 downto 0) := "11";  -- Write data state - receiving write data beats

    -- State machine variables - current state of read and write state machines
    signal state_read  : std_logic_vector(1 downto 0);  -- Current state of read FSM
    signal state_write : std_logic_vector(1 downto 0);  -- Current state of write FSM

begin

    --------------------------------------------------------------------------
    -- Concurrent Signal Assignments
    -- These directly connect internal signals to entity outputs
    --------------------------------------------------------------------------
    -- I/O Connections assignments

    -- AXI4-Full Write Channel Outputs
    S_AXI_AWREADY <= axi_awready;  -- Write address ready to master
    S_AXI_WREADY  <= axi_wready;   -- Write data ready to master
    S_AXI_BRESP   <= axi_bresp;    -- Write response to master
    S_AXI_BUSER   <= axi_buser;    -- Write response user to master
    S_AXI_BVALID  <= axi_bvalid;   -- Write response valid to master
    S_AXI_BID     <= axi_bid;      -- Write response ID to master

    -- AXI4-Full Read Channel Outputs
    S_AXI_ARREADY <= axi_arready;  -- Read address ready to master
    S_AXI_RRESP   <= axi_rresp;    -- Read response to master
    S_AXI_RLAST   <= axi_rlast;    -- Read last to master (final beat indicator)
    S_AXI_RUSER   <= axi_ruser;    -- Read response user to master
    S_AXI_RVALID  <= axi_rvalid;   -- Read data valid to master
    S_AXI_RID     <= axi_rid;      -- Read response ID to master
    S_AXI_RDATA   <= mem_data_out(0);  -- Read data to master (from Block RAM)

    --------------------------------------------------------------------------
    -- Burst Transaction Control Logic
    -- Calculate wrap sizes and wrap enable signals for burst address handling
    --------------------------------------------------------------------------
    -- Calculate wrap size: total transfer size in bytes = data_width_bytes * (burst_length + 1)
    -- Used to determine when wrapping bursts should wrap at address boundary
    aw_wrap_size <= ((C_S_AXI_DATA_WIDTH)/8 * to_integer(unsigned(axi_awlen)));
    ar_wrap_size <= ((C_S_AXI_DATA_WIDTH)/8 * to_integer(unsigned(axi_arlen)));

    -- Wrap enable logic: detects when address matches wrap boundary
    -- For wrapping bursts, address wraps when: (address AND wrap_size) XOR wrap_size = 0
    -- This detects when address reaches a multiple of wrap_size
    aw_wrap_en <= '1' when (((axi_awaddr AND std_logic_vector(to_unsigned(aw_wrap_size, C_S_AXI_ADDR_WIDTH))) XOR std_logic_vector(to_unsigned(aw_wrap_size, C_S_AXI_ADDR_WIDTH))) = low) else '0';
    ar_wrap_en <= '1' when (((axi_araddr AND std_logic_vector(to_unsigned(ar_wrap_size, C_S_AXI_ADDR_WIDTH))) XOR std_logic_vector(to_unsigned(ar_wrap_size, C_S_AXI_ADDR_WIDTH))) = low) else '0';

    --------------------------------------------------------------------------
    -- PROCESS: Write State Machine
    -- 
    -- PURPOSE: Implements the write address and write data channel coordination
    --          for burst write transactions. This state machine ensures proper
    --          handshaking across all beats of a burst transaction.
    --
    -- AXI PROTOCOL: In AXI4-Full, write transactions can span multiple clock cycles:
    --   1. Write address channel handshake occurs (AWVALID & AWREADY)
    --   2. Multiple write data beats occur (each with WVALID & WREADY)
    --   3. WLAST is asserted on the final data beat
    --   4. Write response is sent after all beats are received (BVALID & BREADY)
    --
    -- STATE MACHINE STATES:
    --   - Idle: Initial state after reset, ready for new transaction
    --   - Waddr: Accepting write address, waiting for/accepting first data beat
    --   - Wdata: Receiving remaining data beats in the burst
    --
    -- IMPORTANT: Outstanding write transactions are not supported by this slave.
    --            Master should assert BREADY to receive response on or before
    --            it starts sending a new transaction.
    --
    -- STATE TRANSITIONS:
    --   Idle -> Waddr: When reset is released (S_AXI_ARESETN = '1')
    --   Waddr -> Wdata: When address handshake occurs but more data beats are expected
    --   Waddr -> Waddr: When single-beat transaction completes (WLAST on first beat)
    --   Wdata -> Waddr: When final data beat is received (WLAST asserted)
    --------------------------------------------------------------------------
    process (S_AXI_ACLK)
    begin
        if rising_edge(S_AXI_ACLK) then
            if S_AXI_ARESETN = '0' then
                -- Asynchronous reset: initialize all signals to safe defaults
                -- asserting initial values to all 0's during reset
                axi_awready <= '0';  -- Not ready for address
                axi_wready  <= '0';  -- Not ready for data
                axi_bvalid  <= '0';  -- No valid response
                axi_buser   <= (others => '0');  -- Clear user signals
                axi_awburst <= (others => '0');  -- Clear burst type
                axi_bid     <= (others => '0');  -- Clear response ID
                axi_awlen   <= (others => '0');  -- Clear burst length
                axi_bresp   <= (others => '0');  -- Clear response (OKAY)
                state_write <= Idle;  -- Return to idle state
            else
                case (state_write) is
                    when Idle => -- Initial state indicating reset is done and ready to receive read/write transactions
                        if (S_AXI_ARESETN = '1') then
                            -- Transition to Waddr state and assert ready signals
                            axi_awready <= '1';  -- Ready to accept write address
                            axi_wready  <= '1';  -- Ready to accept write data
                            state_write <= Waddr;  -- Move to write address state
                        else
                            -- Stay in idle state
                            state_write <= state_write;
                        end if;

                    when Waddr => -- At this state, slave is ready to receive address along with corresponding control signals and first data packet. Response valid is also handled at this state
                        if (S_AXI_AWVALID = '1' and axi_awready = '1') then
                            -- Write address handshake occurred
                            if (S_AXI_WVALID = '1' and S_AXI_WLAST = '1') then
                                -- Single-beat transaction: first (and only) data beat with WLAST
                                axi_bvalid  <= '1';  -- Assert write response valid
                                axi_awready <= '1';  -- Keep ready for next transaction
                                state_write <= Waddr;  -- Stay in Waddr (ready for next transaction)
                            else
                                -- Multi-beat transaction: more data beats expected
                                if (S_AXI_BREADY = '1' and axi_bvalid = '1') then
                                    -- Clear previous response if acknowledged
                                    axi_bvalid <= '0';
                                end if;
                                state_write <= Wdata;  -- Move to write data state for remaining beats
                                axi_awready <= '0';  -- Address channel no longer ready (busy with burst)
                            end if;
                            -- Latch burst control signals from address channel
                            axi_awburst <= S_AXI_AWBURST;  -- Capture burst type
                            axi_awlen   <= S_AXI_AWLEN;    -- Capture burst length
                            axi_bid     <= S_AXI_AWID;     -- Capture transaction ID
                        else
                            -- No address handshake - stay in current state
                            state_write <= state_write;
                            if (S_AXI_BREADY = '1' and axi_bvalid = '1') then
                                -- Clear response if acknowledged
                                axi_bvalid <= '0';
                            end if;
                        end if;

                    when Wdata => -- At this state, slave is ready to receive the data packets until the number of transfers is equal to burst length
                        if (S_AXI_WVALID = '1' and S_AXI_WLAST = '1') then
                            -- Final data beat received (WLAST asserted)
                            state_write <= Waddr;  -- Return to Waddr state (ready for next transaction)
                            axi_bvalid  <= '1';    -- Assert write response valid
                            axi_awready <= '1';    -- Ready for next write address
                        else
                            -- More data beats expected - stay in Wdata state
                            state_write <= state_write;
                        end if;

                    when others => -- reserved state - should not occur
                        -- Safe defaults
                        axi_awready <= '0';
                        axi_wready  <= '0';
                        axi_bvalid  <= '0';
                end case;
            end if;
        end if;
    end process;

    --------------------------------------------------------------------------
    -- PROCESS: Read State Machine
    -- 
    -- PURPOSE: Implements the read address and read data channel coordination
    --          for burst read transactions. This state machine ensures proper
    --          handshaking across all beats of a burst transaction.
    --
    -- AXI PROTOCOL: In AXI4-Full, read transactions can span multiple clock cycles:
    --   1. Read address channel handshake occurs (ARVALID & ARREADY)
    --   2. Multiple read data beats are sent (each with RVALID & RREADY)
    --   3. RLAST is asserted on the final data beat
    --
    -- STATE MACHINE STATES:
    --   - Idle: Initial state after reset, ready for new transaction
    --   - Raddr: Accepting read address, preparing to send first data beat
    --   - Rdata: Sending remaining data beats in the burst
    --
    -- IMPORTANT: Outstanding read transactions are not supported by this slave.
    --
    -- STATE TRANSITIONS:
    --   Idle -> Raddr: When reset is released (S_AXI_ARESETN = '1')
    --   Raddr -> Rdata: When address handshake occurs (ready to send data)
    --   Rdata -> Raddr: When final data beat is sent (RLAST handshake complete)
    --------------------------------------------------------------------------
    process (S_AXI_ACLK)
    begin
        if rising_edge(S_AXI_ACLK) then
            if S_AXI_ARESETN = '0' then
                -- Asynchronous reset: initialize all signals to safe defaults
                -- asserting initial values to all 0's during reset
                axi_arready <= '0';  -- Not ready for read address
                axi_rvalid  <= '0';  -- No valid read data
                axi_rlast   <= '0';  -- Not last beat
                axi_ruser   <= (others => '0');  -- Clear user signals
                axi_arburst <= (others => '0');  -- Clear burst type
                axi_rid     <= (others => '0');  -- Clear response ID
                axi_arlen   <= (others => '0');  -- Clear burst length
                axi_rresp   <= (others => '0');  -- Clear response (OKAY)
                state_read  <= Idle;  -- Return to idle state
            else
                case (state_read) is
                    when Idle => -- Initial state indicating reset is done and ready to receive read/write transactions
                        if (S_AXI_ARESETN = '1') then
                            -- Transition to Raddr state and assert ready signal
                            axi_arready <= '1';  -- Ready to accept read address
                            state_read  <= Raddr;  -- Move to read address state
                        else
                            -- Stay in idle state
                            state_read <= state_read;
                        end if;

                    when Raddr => -- At this state, slave is ready to receive address along with corresponding control signals
                        if (S_AXI_ARVALID = '1' and axi_arready = '1') then
                            -- Read address handshake occurred
                            state_read  <= Rdata;  -- Move to read data state
                            axi_rvalid  <= '1';    -- Assert read data valid (data available)
                            axi_arready <= '0';    -- Address channel no longer ready (busy with burst)
                            
                            -- Check if single-beat transaction (ARLEN = 0)
                            if (S_AXI_ARLEN = "00000000") then
                                axi_rlast <= '1';  -- Assert RLAST for single-beat transaction
                            end if;
                            
                            -- Latch burst control signals from address channel
                            axi_arburst <= S_AXI_ARBURST;  -- Capture burst type
                            axi_arlen   <= S_AXI_ARLEN;    -- Capture burst length
                            axi_rid     <= S_AXI_ARID;     -- Capture transaction ID
                        else
                            -- No address handshake - stay in current state
                            state_read <= state_read;
                        end if;

                    when Rdata => -- At this state, slave is ready to send the data packets until the number of transfers is equal to burst length
                        -- Check if this is the second-to-last beat (prepare to assert RLAST)
                        if ((axi_arlen_cntr = std_logic_vector(unsigned(axi_arlen(7 downto 0))-1)) and axi_rlast = '0' and S_AXI_RREADY = '1') then
                            -- Next beat will be the last one
                            axi_rlast <= '1';  -- Assert RLAST for next beat
                        end if;
                        
                        -- Check if final beat handshake is complete
                        if (axi_rvalid = '1' and S_AXI_RREADY = '1' and axi_rlast = '1') then
                            -- Final data beat sent - transaction complete
                            axi_rvalid  <= '0';  -- Deassert read data valid
                            axi_arready <= '1';  -- Ready for next read address
                            axi_rlast   <= '0';  -- Clear RLAST
                            state_read  <= Raddr;  -- Return to Raddr state (ready for next transaction)
                        else
                            -- More beats to send or waiting for RREADY - stay in Rdata state
                            state_read <= state_read;
                        end if;

                    when others => -- reserved state - should not occur
                        -- Safe defaults
                        axi_arready <= '0';
                        axi_rvalid  <= '0';
                end case;
            end if;
        end if;
    end process;

    --------------------------------------------------------------------------
    -- PROCESS: Write Address Increment Logic
    -- 
    -- PURPOSE: Manages write address incrementation/wrapping for burst transactions.
    --          This process calculates the address for each beat in a write burst
    --          based on the burst type (FIXED, INCR, WRAP).
    --
    -- HOW IT WORKS:
    --   1. On write address handshake: latch initial address from AWADDR
    --   2. For each subsequent data beat: increment/wrap address based on burst type
    --   3. Burst length counter tracks current beat number
    --   4. Address is aligned to word boundaries (ADDR_LSB bits are zeroed)
    --
    -- BURST TYPE HANDLING:
    --   - FIXED ("00"): Address stays constant for all beats (same location)
    --   - INCR ("01"): Address increments by data width for each beat
    --   - WRAP ("10"): Address increments until wrap boundary, then wraps to start
    --
    -- ADDRESS ALIGNMENT:
    --   - Lower ADDR_LSB bits are always zero (word-aligned addressing)
    --   - Only upper address bits [ADDR_WIDTH-1:ADDR_LSB] are modified
    --------------------------------------------------------------------------
    process (S_AXI_ACLK)
    begin
        if rising_edge(S_AXI_ACLK) then
            if S_AXI_ARESETN = '0' then
                -- Asynchronous reset: clear address and burst counter
                -- both axi_awlen_cntr and axi_awaddr will increment after each successful data received until the number of the transfers is equal to burst length
                axi_awaddr    <= (others => '0');
                axi_awlen_cntr <= (others => '0');
            else
                -- Check if write address handshake occurred (new transaction starting)
                if (S_AXI_AWVALID = '1' and axi_awready = '1') then
                    if (S_AXI_WVALID = '1') then
                        -- First data beat received simultaneously with address
                        axi_awlen_cntr <= "00000001";  -- Initialize counter to 1 (first beat counted)
                        
                        -- Handle address increment based on burst type
                        if ((S_AXI_AWBURST = "01") or ((S_AXI_AWBURST = "10") and (S_AXI_AWLEN /= "00000000"))) then
                            -- INCR or WRAP burst: increment address for next beat
                            -- awaddr aligned to 4 byte boundary (or appropriate for data width)
                            axi_awaddr(C_S_AXI_ADDR_WIDTH - 1 downto ADDR_LSB) <= std_logic_vector(unsigned(S_AXI_AWADDR(C_S_AXI_ADDR_WIDTH - 1 downto ADDR_LSB)) + 1);
                        else
                            -- FIXED burst: address stays the same
                            axi_awaddr <= axi_awaddr;
                        end if;
                    else
                        -- Address handshake occurred but no data yet - just latch address
                        axi_awlen_cntr <= "00000000";
                        axi_awaddr     <= std_logic_vector(unsigned(S_AXI_AWADDR(C_S_AXI_ADDR_WIDTH - 1 downto 0)));
                    end if;
                elsif ((axi_awlen_cntr < axi_awlen) and S_AXI_WVALID = '1') then
                    -- Subsequent data beats: increment counter and calculate next address
                    axi_awlen_cntr <= std_logic_vector(unsigned(axi_awlen_cntr) + 1);
                    
                    -- Address calculation based on burst type
                    case (axi_awburst) is
                        when "00" => -- fixed burst
                            -- The write address for all the beats in the transaction are fixed
                            -- Address remains constant throughout the burst
                            axi_awaddr <= axi_awaddr; -- for awsize = 4 bytes (010)

                        when "01" => -- incremental burst
                            -- The write address for all the beats in the transaction are increments by awsize
                            -- Address increments by data width for each beat
                            axi_awaddr(C_S_AXI_ADDR_WIDTH - 1 downto ADDR_LSB) <= std_logic_vector(unsigned(axi_awaddr(C_S_AXI_ADDR_WIDTH - 1 downto ADDR_LSB)) + 1); -- awaddr aligned to 4 byte boundary
                            axi_awaddr(ADDR_LSB-1 downto 0) <= (others => '0'); -- for awsize = 4 bytes (010) - zero lower bits

                        when "10" => -- Wrapping burst
                            -- The write address wraps when the address reaches wrap boundary
                            -- Address increments until wrap boundary, then wraps to start address
                            if (aw_wrap_en = '1') then
                                -- Wrap boundary reached - wrap to start of wrap region
                                axi_awaddr <= std_logic_vector(unsigned(axi_awaddr) - (to_unsigned(aw_wrap_size, C_S_AXI_ADDR_WIDTH)));
                            else
                                -- Continue incrementing
                                axi_awaddr(C_S_AXI_ADDR_WIDTH - 1 downto ADDR_LSB) <= std_logic_vector(unsigned(axi_awaddr(C_S_AXI_ADDR_WIDTH - 1 downto ADDR_LSB)) + 1); -- awaddr aligned to 4 byte boundary
                                axi_awaddr(ADDR_LSB-1 downto 0) <= (others => '0'); -- for awsize = 4 bytes (010)
                            end if;

                        when others => -- reserved (incremental burst for example)
                            -- Default to incremental behavior
                            axi_awaddr(C_S_AXI_ADDR_WIDTH - 1 downto ADDR_LSB) <= std_logic_vector(unsigned(axi_awaddr(C_S_AXI_ADDR_WIDTH - 1 downto ADDR_LSB)) + 1); -- for awsize = 4 bytes (010)
                            axi_awaddr(ADDR_LSB-1 downto 0) <= (others => '0');
                    end case;
                end if;
            end if;
        end if;
    end process;

    --------------------------------------------------------------------------
    -- PROCESS: Read Address Increment Logic
    -- 
    -- PURPOSE: Manages read address incrementation/wrapping for burst transactions.
    --          This process calculates the address for each beat in a read burst
    --          based on the burst type (FIXED, INCR, WRAP).
    --
    -- HOW IT WORKS:
    --   1. On read address handshake: latch initial address from ARADDR
    --   2. For each subsequent data beat: increment/wrap address based on burst type
    --   3. Burst length counter tracks current beat number
    --   4. Address is aligned to word boundaries (ADDR_LSB bits are zeroed)
    --
    -- BURST TYPE HANDLING:
    --   - FIXED ("00"): Address stays constant for all beats
    --   - INCR ("01"): Address increments by data width for each beat
    --   - WRAP ("10"): Address increments until wrap boundary, then wraps to start
    --
    -- NOTE: This logic is similar to write address increment, but for read channel
    --------------------------------------------------------------------------
    process (S_AXI_ACLK)
    begin
        if rising_edge(S_AXI_ACLK) then
            if S_AXI_ARESETN = '0' then
                -- Asynchronous reset: clear address and burst counter
                -- both axi_arlen_cntr and axi_araddr will increment after each successful data received until the number of the transfers is equal to burst length
                axi_araddr    <= (others => '0');
                axi_arlen_cntr <= (others => '0');
            else
                -- Check if read address handshake occurred (new transaction starting)
                if (S_AXI_ARVALID = '1' and axi_arready = '1') then
                    -- Latch initial read address and reset counter
                    axi_arlen_cntr <= (others => '0');
                    axi_araddr     <= std_logic_vector(unsigned(S_AXI_ARADDR(C_S_AXI_ADDR_WIDTH - 1 downto 0)));
                elsif ((axi_arlen_cntr <= axi_arlen) and axi_rvalid = '1' and S_AXI_RREADY = '1') then
                    -- Subsequent data beats: increment counter and calculate next address
                    axi_arlen_cntr <= std_logic_vector(unsigned(axi_arlen_cntr) + 1);
                    
                    -- Address calculation based on burst type
                    case (axi_arburst) is
                        when "00" => -- fixed burst
                            -- The read address for all the beats in the transaction are fixed
                            -- Address remains constant throughout the burst
                            axi_araddr <= axi_araddr; -- for arsize = 4 bytes (010)

                        when "01" => -- incremental burst
                            -- The read address for all the beats in the transaction are increments by arsize
                            -- Address increments by data width for each beat
                            axi_araddr(C_S_AXI_ADDR_WIDTH - 1 downto ADDR_LSB) <= std_logic_vector(unsigned(axi_araddr(C_S_AXI_ADDR_WIDTH - 1 downto ADDR_LSB)) + 1); -- araddr aligned to 4 byte boundary
                            axi_araddr(ADDR_LSB-1 downto 0) <= (others => '0'); -- for arsize = 4 bytes (010) - zero lower bits

                        when "10" => -- Wrapping burst
                            -- The read address wraps when the address reaches wrap boundary
                            -- Address increments until wrap boundary, then wraps to start address
                            if (ar_wrap_en = '1') then
                                -- Wrap boundary reached - wrap to start of wrap region
                                axi_araddr <= std_logic_vector(unsigned(axi_araddr) - (to_unsigned(ar_wrap_size, C_S_AXI_ADDR_WIDTH)));
                            else
                                -- Continue incrementing
                                axi_araddr(C_S_AXI_ADDR_WIDTH - 1 downto ADDR_LSB) <= std_logic_vector(unsigned(axi_araddr(C_S_AXI_ADDR_WIDTH - 1 downto ADDR_LSB)) + 1); -- araddr aligned to 4 byte boundary
                                axi_araddr(ADDR_LSB-1 downto 0) <= (others => '0'); -- for arsize = 4 bytes (010)
                            end if;

                        when others => -- reserved (incremental burst for example)
                            -- Default to incremental behavior
                            axi_araddr(C_S_AXI_ADDR_WIDTH - 1 downto ADDR_LSB) <= std_logic_vector(unsigned(axi_araddr(C_S_AXI_ADDR_WIDTH - 1 downto ADDR_LSB)) + 1); -- for arsize = 4 bytes (010)
                            axi_araddr(ADDR_LSB-1 downto 0) <= (others => '0');
                    end case;
                end if;
            end if;
        end if;
    end process;

    --------------------------------------------------------------------------
    -- GENERATE: Memory Address Selection
    -- 
    -- PURPOSE: Generates address selection logic for Block RAM access.
    --          Extracts memory address from AXI address bus for read/write operations.
    --
    -- ADDRESS DECODING:
    --   - Reads address bits [ADDR_LSB+OPT_MEM_ADDR_BITS:ADDR_LSB] from AXI address
    --   - For writes: uses AWADDR if valid, otherwise uses latched axi_awaddr
    --   - For reads: uses latched axi_araddr
    --------------------------------------------------------------------------
    -- Example code to access user logic memory region
    gen_mem_sel : if (USER_NUM_MEM >= 1) generate
    begin
        -- Read address: extract memory address from latched read address
        mem_address_read <= axi_araddr(ADDR_LSB+OPT_MEM_ADDR_BITS downto ADDR_LSB);
        
        -- Write address: use AWADDR if write transaction is active, otherwise use latched address
        mem_address_write <= S_AXI_AWADDR(ADDR_LSB+OPT_MEM_ADDR_BITS downto ADDR_LSB) when (S_AXI_AWVALID = '1' and S_AXI_WVALID = '1') else
                             axi_awaddr(ADDR_LSB+OPT_MEM_ADDR_BITS downto ADDR_LSB);
    end generate gen_mem_sel;

    --------------------------------------------------------------------------
    -- GENERATE: Block RAM Implementation
    -- 
    -- PURPOSE: Generates Block RAM (BRAM) for user data storage.
    --          Implements byte-addressable memory with write strobe support.
    --
    -- IMPLEMENTATION:
    --   - Outer generate loop creates multiple memory blocks (if USER_NUM_MEM > 1)
    --   - Inner generate loop creates byte-wide memory banks for each byte lane
    --   - Each byte is independently writeable via write strobes (WSTRB)
    --   - Memory is read from read address, written to write address
    --
    -- BYTE WRITE ENABLE:
    --   - mem_wren: global write enable (when write data channel is ready)
    --   - WSTRB[byte_index]: per-byte write enable (which bytes to update)
    --   - Memory byte is written only if both mem_wren and WSTRB are '1'
    --
    -- MEMORY ORGANIZATION:
    --   - BYTE_RAM_TYPE: Array of 16 bytes (addressable 0-15)
    --   - Each memory location stores 8 bits
    --   - Multiple byte RAMs are combined to form full data width
    --------------------------------------------------------------------------
    -- implement Block RAM(s)
    BRAM_GEN : for i in 0 to USER_NUM_MEM-1 generate
        signal mem_wren : std_logic;  -- Memory write enable signal
    begin
        -- Generate write enable: active when slave is ready and data is valid
        mem_wren <= axi_wready and S_AXI_WVALID;

        -- Generate byte-wide memory banks for each byte lane in data width
        BYTE_BRAM_GEN : for mem_byte_index in 0 to (C_S_AXI_DATA_WIDTH/8-1) generate
            signal byte_ram : BYTE_RAM_TYPE;  -- Byte-addressable memory array (16 bytes)
            signal data_in  : std_logic_vector(8-1 downto 0);  -- Write data input for this byte
            signal data_out : std_logic_vector(8-1 downto 0);  -- Read data output for this byte
        begin
            -- assigning 8 bit data: extract byte from write data bus
            data_in <= S_AXI_WDATA((mem_byte_index*8+7) downto mem_byte_index*8);
            
            -- Read data: output byte from memory based on read address
            data_out <= byte_ram(to_integer(unsigned(mem_address_read)));

            -- Byte RAM write process: write byte when enabled by strobe
            BYTE_RAM_PROC : process(S_AXI_ACLK) is
            begin
                if (rising_edge(S_AXI_ACLK)) then
                    -- Write byte if: write enable active AND byte strobe active
                    if (mem_wren = '1' and S_AXI_WSTRB(mem_byte_index) = '1') then
                        -- Write byte to memory at write address
                        byte_ram(to_integer(unsigned(mem_address_write))) <= data_in;
                    end if;
                end if;
            end process BYTE_RAM_PROC;

            -- Combine byte outputs into full data width output
            mem_data_out(i)((mem_byte_index*8+7) downto mem_byte_index*8) <= data_out;
        end generate BYTE_BRAM_GEN;
    end generate BRAM_GEN;

    -- Add user logic here

    -- User logic ends

end arch_imp;
