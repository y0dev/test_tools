import serial
import time
import logging

try:
    import pyvisa
    PYVISA_AVAILABLE = True
except ImportError:
    PYVISA_AVAILABLE = False
    logging.warning("PyVISA not available. GPIB support disabled.")

class KeysightE3632A_RS232:
    def __init__(self, port, baud_rate=9600, timeout=1):
        """
        Initialize the RS-232 connection to the Keysight E3632A.

        :param port: COM port (e.g., "COM3" on Windows or "/dev/ttyS0" on Linux).
        :param baud_rate: Baud rate for communication (default: 9600).
        :param timeout: Timeout for serial read/write operations (default: 1 second).
        """
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout,
            )
            print(f"Connected to {port} at {baud_rate} baud.")
        except serial.SerialException as e:
            raise ConnectionError(f"Failed to connect to {port}: {e}")

    def send_command(self, command):
        """
        Send an SCPI command to the instrument.

        :param command: The SCPI command string to send (e.g., "VOLT 5").
        """
        full_command = command + "\n"
        self.serial.write(full_command.encode('ascii'))
        time.sleep(0.1)  # Small delay to allow processing

    def read_response(self):
        """
        Read the response from the instrument.

        :return: The response string.
        """
        response = self.serial.readline().decode('ascii').strip()
        return response

    def set_voltage(self, voltage):
        """
        Set the output voltage.

        :param voltage: Voltage level to set (in volts).
        """
        self.send_command(f"VOLT {voltage}")
        print(f"Voltage set to {voltage} V")

    def get_voltage(self):
        """
        Get the currently set output voltage.

        :return: Voltage level (in volts).
        """
        self.send_command("VOLT?")
        voltage = self.read_response()
        print(f"Set Voltage: {voltage} V")
        return float(voltage)

    def measure_voltage(self):
        """
        Measure the output voltage.

        :return: Measured voltage (in volts).
        """
        self.send_command("MEAS:VOLT?")
        voltage = self.read_response()
        print(f"Measured Voltage: {voltage} V")
        return float(voltage)

    def set_current(self, current):
        """
        Set the output current limit.

        :param current: Current limit to set (in amps).
        """
        self.send_command(f"CURR {current}")
        print(f"Current limit set to {current} A")

    def output_on(self):
        """
        Turn the output ON.
        """
        self.send_command("OUTP ON")
        print("Output turned ON")

    def output_off(self):
        """
        Turn the output OFF.
        """
        self.send_command("OUTP OFF")
        print("Output turned OFF")

    def identify(self):
        """
        Query the instrument's identification string.

        :return: Identification string of the instrument.
        """
        self.send_command("*IDN?")
        idn = self.read_response()
        print(f"Instrument ID: {idn}")
        return idn

    def close(self):
        """
        Close the RS-232 connection.
        """
        if self.serial.is_open:
            self.serial.close()
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
        if not PYVISA_AVAILABLE:
            raise ImportError("PyVISA is required for GPIB communication")
        
        try:
            self.rm = pyvisa.ResourceManager()
            self.instrument = self.rm.open_resource(resource_name)
            self.instrument.timeout = timeout
            print(f"Connected to {resource_name} via GPIB")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {resource_name}: {e}")
    
    def send_command(self, command):
        """
        Send an SCPI command to the instrument.
        
        :param command: The SCPI command string to send
        """
        self.instrument.write(command)
        time.sleep(0.1)  # Small delay to allow processing
    
    def read_response(self):
        """
        Read the response from the instrument.
        
        :return: The response string
        """
        return self.instrument.read().strip()
    
    def set_voltage(self, voltage):
        """
        Set the output voltage.
        
        :param voltage: Voltage level to set (in volts)
        """
        self.send_command(f"VOLT {voltage}")
        print(f"Voltage set to {voltage} V")
    
    def get_voltage(self):
        """
        Get the currently set output voltage.
        
        :return: Voltage level (in volts)
        """
        voltage = self.instrument.query("VOLT?")
        print(f"Set Voltage: {voltage} V")
        return float(voltage)
    
    def measure_voltage(self):
        """
        Measure the output voltage.
        
        :return: Measured voltage (in volts)
        """
        voltage = self.instrument.query("MEAS:VOLT?")
        print(f"Measured Voltage: {voltage} V")
        return float(voltage)
    
    def set_current(self, current):
        """
        Set the output current limit.
        
        :param current: Current limit to set (in amps)
        """
        self.send_command(f"CURR {current}")
        print(f"Current limit set to {current} A")
    
    def output_on(self):
        """
        Turn the output ON.
        """
        self.send_command("OUTP ON")
        print("Output turned ON")
    
    def output_off(self):
        """
        Turn the output OFF.
        """
        self.send_command("OUTP OFF")
        print("Output turned OFF")
    
    def identify(self):
        """
        Query the instrument's identification string.
        
        :return: Identification string of the instrument
        """
        idn = self.instrument.query("*IDN?")
        print(f"Instrument ID: {idn}")
        return idn
    
    def close(self):
        """
        Close the GPIB connection.
        """
        if hasattr(self, 'instrument'):
            self.instrument.close()
        if hasattr(self, 'rm'):
            self.rm.close()
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
        if 'resource' in config:
            # GPIB connection
            return KeysightE3632A_GPIB(
                resource_name=config['resource'],
                timeout=config.get('timeout', 10000)
            )
        elif 'port' in config:
            # RS232 connection
            return KeysightE3632A_RS232(
                port=config['port'],
                baud_rate=config.get('baud_rate', 9600),
                timeout=config.get('timeout', 1)
            )
        else:
            raise ValueError("Power supply configuration must include either 'resource' (GPIB) or 'port' (RS232)")


# Example usage
if __name__ == "__main__":
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
    
    try:
        # Create power supply using factory
        psu = PowerSupplyFactory.create_power_supply(gpib_config)
        
        # Example functionalities
        psu.identify()
        psu.set_voltage(5.0)
        psu.get_voltage()
        psu.set_current(0.5)
        psu.measure_voltage()
        psu.output_on()
        time.sleep(5)
        psu.output_off()
        
    except ConnectionError as e:
        print(e)
    finally:
        if 'psu' in locals():
            psu.close()
