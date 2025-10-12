import serial
import time
import logging
import sys
from datetime import datetime

# Configure logging for power supply operations
def setup_power_supply_logging(log_level=logging.INFO, log_file=None):
    """
    Setup logging configuration for power supply operations.
    
    :param log_level: Logging level (default: INFO)
    :param log_file: Optional log file path (default: None, logs to console)
    """
    logger = logging.getLogger('power_supply')
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Initialize default logger
power_supply_logger = setup_power_supply_logging()

try:
    import pyvisa
    PYVISA_AVAILABLE = True
    power_supply_logger.info("PyVISA library loaded successfully - GPIB support enabled")
except ImportError:
    PYVISA_AVAILABLE = False
    power_supply_logger.warning("PyVISA not available. GPIB support disabled.")

class KeysightE3632A_RS232:
    def __init__(self, port, baud_rate=9600, timeout=1):
        """
        Initialize the RS-232 connection to the Keysight E3632A.

        :param port: COM port (e.g., "COM3" on Windows or "/dev/ttyS0" on Linux).
        :param baud_rate: Baud rate for communication (default: 9600).
        :param timeout: Timeout for serial read/write operations (default: 1 second).
        """
        self.logger = logging.getLogger('power_supply.rs232')
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        
        self.logger.info(f"Initializing RS232 connection to {port} at {baud_rate} baud")
        
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout,
            )
            self.logger.info(f"Successfully connected to {port} at {baud_rate} baud")
            print(f"Connected to {port} at {baud_rate} baud.")
        except serial.SerialException as e:
            self.logger.error(f"Failed to connect to {port}: {e}")
            raise ConnectionError(f"Failed to connect to {port}: {e}")

    def send_command(self, command):
        """
        Send an SCPI command to the instrument.

        :param command: The SCPI command string to send (e.g., "VOLT 5").
        """
        self.logger.debug(f"Sending SCPI command: {command}")
        full_command = command + "\n"
        self.serial.write(full_command.encode('ascii'))
        time.sleep(0.1)  # Small delay to allow processing

    def read_response(self):
        """
        Read the response from the instrument.

        :return: The response string.
        """
        response = self.serial.readline().decode('ascii').strip()
        self.logger.debug(f"Received response: {response}")
        return response

    def set_voltage(self, voltage):
        """
        Set the output voltage.

        :param voltage: Voltage level to set (in volts).
        """
        self.logger.info(f"Setting voltage to {voltage} V")
        self.send_command(f"VOLT {voltage}")
        print(f"Voltage set to {voltage} V")

    def get_voltage(self):
        """
        Get the currently set output voltage.

        :return: Voltage level (in volts).
        """
        self.logger.debug("Querying voltage setting")
        self.send_command("VOLT?")
        voltage = self.read_response()
        voltage_float = float(voltage)
        self.logger.info(f"Voltage setting: {voltage_float} V")
        print(f"Set Voltage: {voltage} V")
        return voltage_float

    def measure_voltage(self):
        """
        Measure the output voltage.

        :return: Measured voltage (in volts).
        """
        self.logger.debug("Measuring output voltage")
        self.send_command("MEAS:VOLT?")
        voltage = self.read_response()
        voltage_float = float(voltage)
        self.logger.info(f"Measured voltage: {voltage_float} V")
        print(f"Measured Voltage: {voltage} V")
        return voltage_float

    def set_current(self, current):
        """
        Set the output current limit.

        :param current: Current limit to set (in amps).
        """
        self.logger.info(f"Setting current limit to {current} A")
        self.send_command(f"CURR {current}")
        print(f"Current limit set to {current} A")

    def output_on(self):
        """
        Turn the output ON.
        """
        self.logger.info("Turning output ON")
        self.send_command("OUTP ON")
        print("Output turned ON")

    def output_off(self):
        """
        Turn the output OFF.
        """
        self.logger.info("Turning output OFF")
        self.send_command("OUTP OFF")
        print("Output turned OFF")

    def identify(self):
        """
        Query the instrument's identification string.

        :return: Identification string of the instrument.
        """
        self.logger.debug("Querying instrument identification")
        self.send_command("*IDN?")
        idn = self.read_response()
        self.logger.info(f"Instrument identification: {idn}")
        print(f"Instrument ID: {idn}")
        return idn

    def graceful_shutdown(self):
        """
        Gracefully shutdown the power supply by turning off output and logging the event.
        """
        try:
            self.logger.info("Initiating graceful shutdown - turning output OFF")
            self.output_off()
            self.logger.info("Graceful shutdown completed successfully")
            print("\n🛑 Graceful shutdown completed - Power supply output turned OFF")
        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}")
            print(f"\n⚠️ Error during graceful shutdown: {e}")

    def check_safety(self, max_voltage=5.5, max_current=0.6):
        v = self.measure_voltage()
        c = self.measure_current()
        if v > max_voltage or c > max_current:
            print(f"⚠️  Safety trip! V={v}, I={c}")
            self.output_off()
            logging.warning(f"Safety shutdown at V={v}, I={c}")
            raise RuntimeError("Safety shutdown triggered.")

    def toggle_output(self, on_time, off_time=None, cycles=1):
        """
        Perform multiple power cycles with progress indication.

        :param on_time: Duration (s) for output ON.
        :param off_time: Duration (s) for output OFF (defaults to on_time if None).
        :param cycles: Number of ON/OFF cycles.
        """
        if off_time is None:
            off_time = on_time

        self.logger.info(f"Starting toggle output: {cycles} cycles, ON={on_time}s, OFF={off_time}s")
        print(f"Starting {cycles} toggle cycles: ON={on_time}s, OFF={off_time}s")
        print("Press Ctrl+C to stop toggle cycling gracefully")

        try:
            for i in range(cycles):
                print(f"\n=== Power Cycle {i + 1}/{cycles} ===")
                try:
                    # Turn ON
                    self.output_on()
                    self._show_progress(on_time, label="ON phase")

                    # Turn OFF
                    self.output_off()
                    self._show_progress(off_time, label="OFF phase")

                    print(f"[Cycle {i + 1}] Completed successfully.\n")
                except Exception as e:
                    self.logger.error(f"Error in cycle {i + 1}: {e}")
                    print(f"[Cycle {i + 1}] Error: {e}")
                    self.reconnect()
        
        except KeyboardInterrupt:
            self.logger.warning("Toggle output cycling interrupted by user (Ctrl+C)")
            print(f"\n⚠️ Toggle output cycling interrupted by user (Ctrl+C)")
            self.graceful_shutdown()
            return

    def reconnect(self):
        """
        Attempt to reconnect to the power supply after an error.
        """
        self.logger.info(f"Attempting to reconnect to {self.port}")
        try:
            if hasattr(self, 'serial') and self.serial.is_open:
                self.serial.close()
            
            # Reinitialize the connection
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
            )
            self.logger.info(f"Successfully reconnected to {self.port}")
            print(f"Reconnected to {self.port}")
        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")
            print(f"Reconnection failed: {e}")
            raise ConnectionError(f"Failed to reconnect: {e}")

    def _show_progress(self, duration, label=""):
        """
        Display a live progress bar for the specified duration.
        """
        start = time.time()
        width = 30  # characters wide progress bar
        while True:
            elapsed = time.time() - start
            remaining = duration - elapsed
            if remaining < 0:
                break
            filled = int(width * (elapsed / duration))
            bar = "█" * filled + "-" * (width - filled)
            sys.stdout.write(f"\r[{bar}] {label} {elapsed:4.1f}/{duration:.1f}s remaining {remaining:4.1f}s ")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * 80 + "\r")  # clear line after done

    def power_cycle(self, cycles=1, on_time=1.0, off_time=1.0, voltage=None, current=None, callback=None, show_progress=True):
        """
        Perform multiple power cycles (ON/OFF sequences).
        
        :param cycles: Number of power cycles to perform (default: 1)
        :param on_time: Time to keep output ON in seconds (default: 1.0)
        :param off_time: Time to keep output OFF in seconds (default: 1.0)
        :param voltage: Voltage to set before cycling (if None, uses current setting)
        :param current: Current limit to set before cycling (if None, uses current setting)
        :param callback: Optional callback function called after each cycle with cycle number
        :param show_progress: Show progress bars for timing (default: True)
        :return: List of cycle results with timestamps and measurements
        """
        cycle_results = []
        
        self.logger.info(f"Starting power cycling: {cycles} cycles, ON={on_time}s, OFF={off_time}s, voltage={voltage}V, current={current}A")
        
        # Set voltage and current if specified
        if voltage is not None:
            self.logger.info(f"Setting voltage to {voltage}V before cycling")
            self.set_voltage(voltage)
        if current is not None:
            self.logger.info(f"Setting current limit to {current}A before cycling")
            self.set_current(current)
        
        print(f"Starting {cycles} power cycle(s): ON={on_time}s, OFF={off_time}s")
        print("Press Ctrl+C to stop power cycling gracefully")
        
        try:
            for cycle_num in range(1, cycles + 1):
                cycle_start_time = time.time()
                self.logger.info(f"Starting cycle {cycle_num}/{cycles}")
                
                cycle_result = {
                    'cycle': cycle_num,
                    'start_time': cycle_start_time,
                    'on_time': on_time,
                    'off_time': off_time,
                    'voltage_setting': self.get_voltage(),
                    'current_setting': None,  # Current limit query not available in basic SCPI
                    'measurements': []
                }
                
                try:
                    # Turn output ON
                    self.output_on()
                    on_start = time.time()
                    
                    # Measure during ON time
                    if on_time > 0.1:  # Only measure if ON time is long enough
                        time.sleep(0.1)  # Brief delay for stabilization
                        voltage_measured = self.measure_voltage()
                        cycle_result['measurements'].append({
                            'time': time.time() - cycle_start_time,
                            'voltage': voltage_measured,
                            'state': 'ON'
                        })
                    
                    # Wait for ON time with progress bar
                    if show_progress and on_time > 0.1:
                        self._show_progress(on_time, f"Cycle {cycle_num}/{cycles} - Power ON | Power OFF in {on_time:.1f}s")
                    else:
                        time.sleep(on_time)
                
                    # Turn output OFF
                    self.output_off()
                    off_start = time.time()
                    
                    # Wait for OFF time with progress bar
                    if show_progress and off_time > 0.1:
                        next_state = f"Power ON in {off_time:.1f}s" if cycle_num < cycles else "Cycle complete"
                        self._show_progress(off_time, f"Cycle {cycle_num}/{cycles} - Power OFF | {next_state}")
                    else:
                        time.sleep(off_time)
                    
                    cycle_end_time = time.time()
                    cycle_result['end_time'] = cycle_end_time
                    cycle_result['total_duration'] = cycle_end_time - cycle_start_time
                    
                    cycle_results.append(cycle_result)
                    self.logger.info(f"Cycle {cycle_num}/{cycles} completed successfully in {cycle_result['total_duration']:.2f}s")
                    print(f"Cycle {cycle_num}/{cycles} completed in {cycle_result['total_duration']:.2f}s")
                    
                    # Call callback if provided
                    if callback:
                        self.logger.debug(f"Calling callback for cycle {cycle_num}")
                        callback(cycle_num, cycle_result)
                        
                except Exception as e:
                    self.logger.error(f"Error during cycle {cycle_num}: {e}")
                    print(f"Error during cycle {cycle_num}: {e}")
                    cycle_result['error'] = str(e)
                    cycle_results.append(cycle_result)
                    # Continue with next cycle unless critical error
                    continue
        
        except KeyboardInterrupt:
            self.logger.warning("Power cycling interrupted by user (Ctrl+C)")
            print(f"\n⚠️ Power cycling interrupted by user (Ctrl+C)")
            self.graceful_shutdown()
            cycle_results.append({
                'cycle': 'INTERRUPTED',
                'interrupted': True,
                'completed_cycles': len(cycle_results),
                'total_requested': cycles,
                'interrupt_time': time.time()
            })
            return cycle_results
        
        self.logger.info(f"Power cycling completed. {len(cycle_results)} cycles executed.")
        print(f"Power cycling completed. {len(cycle_results)} cycles executed.")
        return cycle_results

    def power_cycle_with_ramp(self, cycles=1, on_time=1.0, off_time=1.0, voltage_start=0.0, voltage_end=5.0, 
                             voltage_steps=10, current=None, callback=None, show_progress=True):
        """
        Perform power cycles with voltage ramping during ON time.
        
        :param cycles: Number of power cycles to perform
        :param on_time: Time to keep output ON in seconds
        :param off_time: Time to keep output OFF in seconds
        :param voltage_start: Starting voltage for ramp (volts)
        :param voltage_end: Ending voltage for ramp (volts)
        :param voltage_steps: Number of voltage steps during ramp
        :param current: Current limit to set before cycling
        :param callback: Optional callback function called after each cycle
        :param show_progress: Show progress bars for timing (default: True)
        :return: List of cycle results with ramp measurements
        """
        cycle_results = []
        
        self.logger.info(f"Starting voltage ramp cycling: {cycles} cycles, ON={on_time}s, OFF={off_time}s, ramp={voltage_start}V→{voltage_end}V, steps={voltage_steps}, current={current}A")
        
        # Set current if specified
        if current is not None:
            self.logger.info(f"Setting current limit to {current}A before ramp cycling")
            self.set_current(current)
        
        print(f"Starting {cycles} power cycle(s) with voltage ramp: {voltage_start}V to {voltage_end}V")
        print("Press Ctrl+C to stop voltage ramp cycling gracefully")
        
        try:
            for cycle_num in range(1, cycles + 1):
                cycle_start_time = time.time()
                self.logger.info(f"Starting ramp cycle {cycle_num}/{cycles}")
                
                cycle_result = {
                    'cycle': cycle_num,
                    'start_time': cycle_start_time,
                    'on_time': on_time,
                    'off_time': off_time,
                    'voltage_start': voltage_start,
                    'voltage_end': voltage_end,
                    'voltage_steps': voltage_steps,
                    'measurements': []
                }
                
                try:
                    # Turn output ON
                    self.output_on()
                    
                    # Perform voltage ramp with progress bar
                    voltage_step_size = (voltage_end - voltage_start) / voltage_steps
                    step_time = on_time / voltage_steps
                    
                    # Always perform voltage ramp, with or without progress bar
                    for step in range(voltage_steps + 1):
                        voltage = voltage_start + (step * voltage_step_size)
                        self.set_voltage(voltage)
                        
                        # Measure voltage after brief stabilization
                        time.sleep(0.05)
                        voltage_measured = self.measure_voltage()
                        cycle_result['measurements'].append({
                            'time': time.time() - cycle_start_time,
                            'voltage_set': voltage,
                            'voltage_measured': voltage_measured,
                            'step': step,
                            'state': 'ON'
                        })
                        
                        # Wait for step time
                        time.sleep(step_time)
                
                    # Turn output OFF
                    self.output_off()
                    
                    # Wait for OFF time with progress bar
                    if show_progress and off_time > 0.1:
                        next_state = f"Power ON in {off_time:.1f}s" if cycle_num < cycles else "Cycle complete"
                        self._show_progress(off_time, f"Cycle {cycle_num}/{cycles} - Power OFF | {next_state}")
                    else:
                        time.sleep(off_time)
                    
                    cycle_end_time = time.time()
                    cycle_result['end_time'] = cycle_end_time
                    cycle_result['total_duration'] = cycle_end_time - cycle_start_time
                    
                    cycle_results.append(cycle_result)
                    self.logger.info(f"Ramp cycle {cycle_num}/{cycles} completed successfully in {cycle_result['total_duration']:.2f}s")
                    print(f"Ramp cycle {cycle_num}/{cycles} completed in {cycle_result['total_duration']:.2f}s")
                    
                    # Call callback if provided
                    if callback:
                        self.logger.debug(f"Calling callback for ramp cycle {cycle_num}")
                        callback(cycle_num, cycle_result)
                        
                except Exception as e:
                    self.logger.error(f"Error during ramp cycle {cycle_num}: {e}")
                    print(f"Error during ramp cycle {cycle_num}: {e}")
                    cycle_result['error'] = str(e)
                    cycle_results.append(cycle_result)
                    continue
        
        except KeyboardInterrupt:
            self.logger.warning("Voltage ramp cycling interrupted by user (Ctrl+C)")
            print(f"\n⚠️ Voltage ramp cycling interrupted by user (Ctrl+C)")
            self.graceful_shutdown()
            cycle_results.append({
                'cycle': 'INTERRUPTED',
                'interrupted': True,
                'completed_cycles': len(cycle_results),
                'total_requested': cycles,
                'interrupt_time': time.time()
            })
            return cycle_results
        
        self.logger.info(f"Voltage ramp cycling completed. {len(cycle_results)} cycles executed.")
        print(f"Voltage ramp cycling completed. {len(cycle_results)} cycles executed.")
        return cycle_results

    def close(self):
        """
        Close the RS-232 connection.
        """
        self.logger.info(f"Closing RS232 connection to {self.port}")
        if self.serial.is_open:
            self.serial.close()
            self.logger.info(f"RS232 connection to {self.port} closed successfully")
            print("Connection closed.")


class KeysightE3632A_GPIB:
    """
    GPIB interface for Keysight E3632A power supply.
    """
    
    def __init__(self, resource_name, timeout=10000):
        """
        Initialize the GPIB connection to the Keysight E3632A.
        
        :param resource_name: GPIB resource name (e.g., "GPIB0::5::INSTR")
        :param timeout: Timeout in milliseconds
        """
        self.logger = logging.getLogger('power_supply.gpib')
        self.resource_name = resource_name
        self.timeout = timeout
        
        self.logger.info(f"Initializing GPIB connection to {resource_name}")
        
        if not PYVISA_AVAILABLE:
            self.logger.error("PyVISA is required for GPIB communication")
            raise ImportError("PyVISA is required for GPIB communication")
        
        try:
            self.rm = pyvisa.ResourceManager()
            self.instrument = self.rm.open_resource(resource_name)
            self.instrument.timeout = timeout
            self.logger.info(f"Successfully connected to {resource_name} via GPIB")
            print(f"Connected to {resource_name} via GPIB")
        except Exception as e:
            self.logger.error(f"Failed to connect to {resource_name}: {e}")
            raise ConnectionError(f"Failed to connect to {resource_name}: {e}")
    
    def send_command(self, command):
        """
        Send an SCPI command to the instrument.
        
        :param command: The SCPI command string to send
        """
        self.logger.debug(f"Sending SCPI command: {command}")
        self.instrument.write(command)
        time.sleep(0.1)  # Small delay to allow processing
    
    def read_response(self):
        """
        Read the response from the instrument.
        
        :return: The response string
        """
        response = self.instrument.read().strip()
        self.logger.debug(f"Received response: {response}")
        return response
    
    def set_voltage(self, voltage):
        """
        Set the output voltage.
        
        :param voltage: Voltage level to set (in volts)
        """
        self.logger.info(f"Setting voltage to {voltage} V")
        self.send_command(f"VOLT {voltage}")
        print(f"Voltage set to {voltage} V")
    
    def get_voltage(self):
        """
        Get the currently set output voltage.
        
        :return: Voltage level (in volts)
        """
        self.logger.debug("Querying voltage setting")
        voltage = self.instrument.query("VOLT?")
        voltage_float = float(voltage)
        self.logger.info(f"Voltage setting: {voltage_float} V")
        print(f"Set Voltage: {voltage} V")
        return voltage_float
    
    def measure_voltage(self):
        """
        Measure the output voltage.
        
        :return: Measured voltage (in volts)
        """
        self.logger.debug("Measuring output voltage")
        voltage = self.instrument.query("MEAS:VOLT?")
        voltage_float = float(voltage)
        self.logger.info(f"Measured voltage: {voltage_float} V")
        print(f"Measured Voltage: {voltage} V")
        return voltage_float
    
    def set_current(self, current):
        """
        Set the output current limit.
        
        :param current: Current limit to set (in amps)
        """
        self.logger.info(f"Setting current limit to {current} A")
        self.send_command(f"CURR {current}")
        print(f"Current limit set to {current} A")
    
    def output_on(self):
        """
        Turn the output ON.
        """
        self.logger.info("Turning output ON")
        self.send_command("OUTP ON")
        print("Output turned ON")
    
    def output_off(self):
        """
        Turn the output OFF.
        """
        self.logger.info("Turning output OFF")
        self.send_command("OUTP OFF")
        print("Output turned OFF")
    
    def identify(self):
        """
        Query the instrument's identification string.
        
        :return: Identification string of the instrument
        """
        self.logger.debug("Querying instrument identification")
        idn = self.instrument.query("*IDN?")
        self.logger.info(f"Instrument identification: {idn}")
        print(f"Instrument ID: {idn}")
        return idn
    
    def graceful_shutdown(self):
        """
        Gracefully shutdown the power supply by turning off output and logging the event.
        """
        try:
            self.logger.info("Initiating graceful shutdown - turning output OFF")
            self.output_off()
            self.logger.info("Graceful shutdown completed successfully")
            print("\n🛑 Graceful shutdown completed - Power supply output turned OFF")
        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}")
            print(f"\n⚠️ Error during graceful shutdown: {e}")

    def reconnect(self):
        """
        Attempt to reconnect to the power supply after an error.
        """
        self.logger.info(f"Attempting to reconnect to {self.resource_name}")
        try:
            if hasattr(self, 'instrument'):
                self.instrument.close()
            if hasattr(self, 'rm'):
                self.rm.close()
            
            # Reinitialize the connection
            self.rm = pyvisa.ResourceManager()
            self.instrument = self.rm.open_resource(self.resource_name)
            self.instrument.timeout = self.timeout
            self.logger.info(f"Successfully reconnected to {self.resource_name}")
            print(f"Reconnected to {self.resource_name}")
        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")
            print(f"Reconnection failed: {e}")
            raise ConnectionError(f"Failed to reconnect: {e}")
    
    def _show_progress(self, duration, label=""):
        """
        Display a live progress bar for the specified duration.
        """
        start = time.time()
        width = 30  # characters wide progress bar
        while True:
            elapsed = time.time() - start
            remaining = duration - elapsed
            if remaining < 0:
                break
            filled = int(width * (elapsed / duration))
            bar = "█" * filled + "-" * (width - filled)
            sys.stdout.write(f"\r[{bar}] {label} {elapsed:4.1f}/{duration:.1f}s remaining {remaining:4.1f}s ")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * 80 + "\r")  # clear line after done
    
    def power_cycle(self, cycles=1, on_time=1.0, off_time=1.0, voltage=None, current=None, callback=None, show_progress=True):
        """
        Perform multiple power cycles (ON/OFF sequences).
        
        :param cycles: Number of power cycles to perform (default: 1)
        :param on_time: Time to keep output ON in seconds (default: 1.0)
        :param off_time: Time to keep output OFF in seconds (default: 1.0)
        :param voltage: Voltage to set before cycling (if None, uses current setting)
        :param current: Current limit to set before cycling (if None, uses current setting)
        :param callback: Optional callback function called after each cycle with cycle number
        :param show_progress: Show progress bars for timing (default: True)
        :return: List of cycle results with timestamps and measurements
        """
        cycle_results = []
        
        self.logger.info(f"Starting power cycling: {cycles} cycles, ON={on_time}s, OFF={off_time}s, voltage={voltage}V, current={current}A")
        
        # Set voltage and current if specified
        if voltage is not None:
            self.logger.info(f"Setting voltage to {voltage}V before cycling")
            self.set_voltage(voltage)
        if current is not None:
            self.logger.info(f"Setting current limit to {current}A before cycling")
            self.set_current(current)
        
        print(f"Starting {cycles} power cycle(s): ON={on_time}s, OFF={off_time}s")
        print("Press Ctrl+C to stop power cycling gracefully")
        
        try:
            for cycle_num in range(1, cycles + 1):
                cycle_start_time = time.time()
                self.logger.info(f"Starting cycle {cycle_num}/{cycles}")
                
                cycle_result = {
                    'cycle': cycle_num,
                    'start_time': cycle_start_time,
                    'on_time': on_time,
                    'off_time': off_time,
                    'voltage_setting': self.get_voltage(),
                    'current_setting': None,  # Current limit query not available in basic SCPI
                    'measurements': []
                }
                
                try:
                    # Turn output ON
                    self.output_on()
                    on_start = time.time()
                    
                    # Measure during ON time
                    if on_time > 0.1:  # Only measure if ON time is long enough
                        time.sleep(0.1)  # Brief delay for stabilization
                        voltage_measured = self.measure_voltage()
                        cycle_result['measurements'].append({
                            'time': time.time() - cycle_start_time,
                            'voltage': voltage_measured,
                            'state': 'ON'
                        })
                    
                    # Wait for ON time with progress bar
                    if show_progress and on_time > 0.1:
                        self._show_progress(on_time, f"Cycle {cycle_num}/{cycles} - Power ON | Power OFF in {on_time:.1f}s")
                    else:
                        time.sleep(on_time)
                
                    # Turn output OFF
                    self.output_off()
                    off_start = time.time()
                    
                    # Wait for OFF time with progress bar
                    if show_progress and off_time > 0.1:
                        next_state = f"Power ON in {off_time:.1f}s" if cycle_num < cycles else "Cycle complete"
                        self._show_progress(off_time, f"Cycle {cycle_num}/{cycles} - Power OFF | {next_state}")
                    else:
                        time.sleep(off_time)
                    
                    cycle_end_time = time.time()
                    cycle_result['end_time'] = cycle_end_time
                    cycle_result['total_duration'] = cycle_end_time - cycle_start_time
                    
                    cycle_results.append(cycle_result)
                    self.logger.info(f"Cycle {cycle_num}/{cycles} completed successfully in {cycle_result['total_duration']:.2f}s")
                    print(f"Cycle {cycle_num}/{cycles} completed in {cycle_result['total_duration']:.2f}s")
                    
                    # Call callback if provided
                    if callback:
                        self.logger.debug(f"Calling callback for cycle {cycle_num}")
                        callback(cycle_num, cycle_result)
                        
                except Exception as e:
                    self.logger.error(f"Error during cycle {cycle_num}: {e}")
                    print(f"Error during cycle {cycle_num}: {e}")
                    cycle_result['error'] = str(e)
                    cycle_results.append(cycle_result)
                    # Continue with next cycle unless critical error
                    continue
        
        except KeyboardInterrupt:
            self.logger.warning("Power cycling interrupted by user (Ctrl+C)")
            print(f"\n⚠️ Power cycling interrupted by user (Ctrl+C)")
            self.graceful_shutdown()
            cycle_results.append({
                'cycle': 'INTERRUPTED',
                'interrupted': True,
                'completed_cycles': len(cycle_results),
                'total_requested': cycles,
                'interrupt_time': time.time()
            })
            return cycle_results
        
        self.logger.info(f"Power cycling completed. {len(cycle_results)} cycles executed.")
        print(f"Power cycling completed. {len(cycle_results)} cycles executed.")
        return cycle_results

    def power_cycle_with_ramp(self, cycles=1, on_time=1.0, off_time=1.0, voltage_start=0.0, voltage_end=5.0, 
                             voltage_steps=10, current=None, callback=None, show_progress=True):
        """
        Perform power cycles with voltage ramping during ON time.
        
        :param cycles: Number of power cycles to perform
        :param on_time: Time to keep output ON in seconds
        :param off_time: Time to keep output OFF in seconds
        :param voltage_start: Starting voltage for ramp (volts)
        :param voltage_end: Ending voltage for ramp (volts)
        :param voltage_steps: Number of voltage steps during ramp
        :param current: Current limit to set before cycling
        :param callback: Optional callback function called after each cycle
        :param show_progress: Show progress bars for timing (default: True)
        :return: List of cycle results with ramp measurements
        """
        cycle_results = []
        
        self.logger.info(f"Starting voltage ramp cycling: {cycles} cycles, ON={on_time}s, OFF={off_time}s, ramp={voltage_start}V→{voltage_end}V, steps={voltage_steps}, current={current}A")
        
        # Set current if specified
        if current is not None:
            self.logger.info(f"Setting current limit to {current}A before ramp cycling")
            self.set_current(current)
        
        print(f"Starting {cycles} power cycle(s) with voltage ramp: {voltage_start}V to {voltage_end}V")
        print("Press Ctrl+C to stop voltage ramp cycling gracefully")
        
        try:
            for cycle_num in range(1, cycles + 1):
                cycle_start_time = time.time()
                self.logger.info(f"Starting ramp cycle {cycle_num}/{cycles}")
                
                cycle_result = {
                    'cycle': cycle_num,
                    'start_time': cycle_start_time,
                    'on_time': on_time,
                    'off_time': off_time,
                    'voltage_start': voltage_start,
                    'voltage_end': voltage_end,
                    'voltage_steps': voltage_steps,
                    'measurements': []
                }
                
                try:
                    # Turn output ON
                    self.output_on()
                    
                    # Perform voltage ramp with progress bar
                    voltage_step_size = (voltage_end - voltage_start) / voltage_steps
                    step_time = on_time / voltage_steps
                    
                    # Always perform voltage ramp, with or without progress bar
                    for step in range(voltage_steps + 1):
                        voltage = voltage_start + (step * voltage_step_size)
                        self.set_voltage(voltage)
                        
                        # Measure voltage after brief stabilization
                        time.sleep(0.05)
                        voltage_measured = self.measure_voltage()
                        cycle_result['measurements'].append({
                            'time': time.time() - cycle_start_time,
                            'voltage_set': voltage,
                            'voltage_measured': voltage_measured,
                            'step': step,
                            'state': 'ON'
                        })
                        
                        # Wait for step time
                        time.sleep(step_time)
                
                    # Turn output OFF
                    self.output_off()
                    
                    # Wait for OFF time with progress bar
                    if show_progress and off_time > 0.1:
                        next_state = f"Power ON in {off_time:.1f}s" if cycle_num < cycles else "Cycle complete"
                        self._show_progress(off_time, f"Cycle {cycle_num}/{cycles} - Power OFF | {next_state}")
                    else:
                        time.sleep(off_time)
                    
                    cycle_end_time = time.time()
                    cycle_result['end_time'] = cycle_end_time
                    cycle_result['total_duration'] = cycle_end_time - cycle_start_time
                    
                    cycle_results.append(cycle_result)
                    self.logger.info(f"Ramp cycle {cycle_num}/{cycles} completed successfully in {cycle_result['total_duration']:.2f}s")
                    print(f"Ramp cycle {cycle_num}/{cycles} completed in {cycle_result['total_duration']:.2f}s")
                    
                    # Call callback if provided
                    if callback:
                        self.logger.debug(f"Calling callback for ramp cycle {cycle_num}")
                        callback(cycle_num, cycle_result)
                        
                except Exception as e:
                    self.logger.error(f"Error during ramp cycle {cycle_num}: {e}")
                    print(f"Error during ramp cycle {cycle_num}: {e}")
                    cycle_result['error'] = str(e)
                    cycle_results.append(cycle_result)
                    continue
        
        except KeyboardInterrupt:
            self.logger.warning("Voltage ramp cycling interrupted by user (Ctrl+C)")
            print(f"\n⚠️ Voltage ramp cycling interrupted by user (Ctrl+C)")
            self.graceful_shutdown()
            cycle_results.append({
                'cycle': 'INTERRUPTED',
                'interrupted': True,
                'completed_cycles': len(cycle_results),
                'total_requested': cycles,
                'interrupt_time': time.time()
            })
            return cycle_results
        
        self.logger.info(f"Voltage ramp cycling completed. {len(cycle_results)} cycles executed.")
        print(f"Voltage ramp cycling completed. {len(cycle_results)} cycles executed.")
        return cycle_results

    def close(self):
        """
        Close the GPIB connection.
        """
        self.logger.info(f"Closing GPIB connection to {self.resource_name}")
        if hasattr(self, 'instrument'):
            self.instrument.close()
            self.logger.debug("GPIB instrument connection closed")
        if hasattr(self, 'rm'):
            self.rm.close()
            self.logger.debug("GPIB resource manager closed")
        self.logger.info(f"GPIB connection to {self.resource_name} closed successfully")
        print("GPIB connection closed.")


class PowerSupplyFactory:
    """
    Factory class to create power supply instances based on configuration.
    """
    
    @staticmethod
    def create_power_supply(config):
        """
        Create a power supply instance based on configuration.
        
        :param config: Power supply configuration dictionary
        :return: Power supply instance
        """
        logger = logging.getLogger('power_supply.factory')
        logger.info(f"Creating power supply with config: {config}")
        
        if 'resource' in config:
            # GPIB connection
            logger.info(f"Creating GPIB power supply: {config['resource']}")
            return KeysightE3632A_GPIB(
                resource_name=config['resource'],
                timeout=config.get('timeout', 10000)
            )
        elif 'port' in config:
            # RS232 connection
            logger.info(f"Creating RS232 power supply: {config['port']}")
            return KeysightE3632A_RS232(
                port=config['port'],
                baud_rate=config.get('baud_rate', 9600),
                timeout=config.get('timeout', 1)
            )
        else:
            logger.error("Power supply configuration must include either 'resource' (GPIB) or 'port' (RS232)")
            raise ValueError("Power supply configuration must include either 'resource' (GPIB) or 'port' (RS232)")


# Example usage
if __name__ == "__main__":
    # Setup logging for example
    example_logger = setup_power_supply_logging(log_level=logging.INFO, log_file="power_supply_example.log")
    example_logger.info("Starting power supply example")
    
    # Example RS232 usage
    rs232_config = {
        'port': 'COM3',
        'baud_rate': 9600,
        'timeout': 1
    }
    
    # Example GPIB usage
    gpib_config = {
        'resource': 'GPIB0::5::INSTR',
        'timeout': 10000
    }
    
    # Power cycling callback function
    def cycle_callback(cycle_num, result):
        example_logger.info(f"Callback: Cycle {cycle_num} completed with voltage {result['voltage_setting']}V")
        print(f"Callback: Cycle {cycle_num} completed with voltage {result['voltage_setting']}V")
    
    try:
        # Create power supply using factory
        example_logger.info("Creating power supply instance")
        psu = PowerSupplyFactory.create_power_supply(gpib_config)
        
        # Basic functionality example
        print("=== Basic Power Supply Operations ===")
        psu.identify()
        psu.set_voltage(5.0)
        psu.get_voltage()
        psu.set_current(0.5)
        psu.measure_voltage()
        
        # Power cycling examples
        print("\n=== Power Cycling Examples ===")
        
        # Example 1: Simple single cycle with progress bar
        print("\n1. Single power cycle with progress bar:")
        results = psu.power_cycle(cycles=1, on_time=2.0, off_time=1.0, voltage=3.3, show_progress=True)
        
        # Example 2: Multiple cycles with callback and progress bar
        print("\n2. Multiple power cycles with callback and progress bar:")
        results = psu.power_cycle(
            cycles=3, 
            on_time=1.5, 
            off_time=0.5, 
            voltage=5.0, 
            current=0.3,
            callback=cycle_callback,
            show_progress=True
        )
        
        # Example 3: Stress testing with many cycles (no progress bar for speed)
        print("\n3. Stress testing (5 cycles) - no progress bar:")
        results = psu.power_cycle(
            cycles=5,
            on_time=0.5,
            off_time=0.2,
            voltage=3.3,
            current=0.1,
            show_progress=False
        )
        
        # Example 4: Voltage ramp cycling with progress bar
        print("\n4. Voltage ramp cycling with progress bar:")
        ramp_results = psu.power_cycle_with_ramp(
            cycles=2,
            on_time=3.0,
            off_time=1.0,
            voltage_start=0.0,
            voltage_end=5.0,
            voltage_steps=5,
            current=0.2,
            show_progress=True
        )
        
        # Print summary of all cycles
        print(f"\n=== Power Cycling Summary ===")
        print(f"Standard cycles completed: {len(results)}")
        for result in results:
            if 'error' not in result:
                print(f"Cycle {result['cycle']}: {result['total_duration']:.2f}s "
                      f"(ON: {result['on_time']}s, OFF: {result['off_time']}s)")
            else:
                print(f"Cycle {result['cycle']}: ERROR - {result['error']}")
        
        print(f"\nRamp cycles completed: {len(ramp_results)}")
        for result in ramp_results:
            if 'error' not in result:
                print(f"Ramp Cycle {result['cycle']}: {result['total_duration']:.2f}s "
                      f"({result['voltage_start']}V to {result['voltage_end']}V, "
                      f"{result['voltage_steps']} steps)")
            else:
                print(f"Ramp Cycle {result['cycle']}: ERROR - {result['error']}")
        
    except KeyboardInterrupt:
        example_logger.warning("Example interrupted by user (Ctrl+C)")
        print(f"\n⚠️ Example interrupted by user (Ctrl+C)")
        if 'psu' in locals():
            example_logger.info("Performing graceful shutdown")
            psu.graceful_shutdown()
    except ConnectionError as e:
        example_logger.error(f"Connection error: {e}")
        print(f"Connection error: {e}")
    except Exception as e:
        example_logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")
    finally:
        if 'psu' in locals():
            example_logger.info("Closing power supply connection")
            psu.close()
        example_logger.info("Power supply example completed")
