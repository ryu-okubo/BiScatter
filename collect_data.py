import serial
import time
from serial.tools import list_ports
from datetime import datetime


SERIAL_DEFAULT_TIMEOUT = 15.0

def list_usb():
    """ list all available com ports

    Raises:
        ValueError: no available usb

    Returns:
        list: list of device dev path for available com ports
    """
    ports = list_ports.comports()
    dev = [i.device for i in ports]
    if not dev:
        raise ValueError("usb not available")
    return dev

class Serial_Service:
    """
    A class to control the MCU through serial communication

    ...

    Attributes
    ----------
    port : str
        COM port the MCU is connected
    baudrate : int
        baud rate of the MCU
    ser : Serial
        Serial class set up between machine and MCU

    Methods
    -------
    collect_data(duration, PLOT=True, SAVE=True, save_dir="Data/test"):
        collect data for given duration in [us] via teensy ADC and return the collected data as numpy array
    move_stepper(self, distance):
        move motion stage to given position with respect to the intial position.

    """
    def __init__(self, port, baudrate) -> None:
        """Constructor for Serial_Service class

        Args:
            port (str): COM port the MCU is connected to
            baudrate (int): baud rate of the MCU
        """
        self.port = port
        self.baudrate = baudrate

        self.ser = serial.Serial(port, baudrate, timeout=SERIAL_DEFAULT_TIMEOUT)
        print("teensy connected")

    def collect_data(self, duration, PLOT=True, SAVE=True, save_dir="Data/test"):
        """collect the data from the ADC of teensy. 
        Change the Pin number from the teensy code if needed

        Args:
            duration (int): time duration of data collection in [us]
            PLOT (bool): Plot the time domain signal if true. Defaults to True.
            SAVE (bool): Save the collected data as a numpy file if True. Defaults to True.
            save_dir (str, optional): _description_. Defaults to "Data/test".

        Returns:
            2D numpy array: first dimension is sample, and second dimension is [timestamp, ADC_reading]
        """
        self.clear_buffer()
        # collected_data = []
        command = 'collect_data'
        self.ser.write(bytes(command, 'utf-8'))
        time.sleep(1)
        output = self.ser.readline().decode('utf-8').strip()
        print(output)
        duration = str(duration)
        self.ser.write(bytes(duration, 'utf-8'))
        time.sleep(1)
        output = self.ser.readline().decode('utf-8').strip()
        print(output)

        # Generate current date and time
        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Create filename with prefix and timestamp
        filename = f"{save_dir}_{current_datetime}.bin"

        while (True):
            with open(filename, 'ab') as file:
                output = self.ser.read(self.ser.in_waiting) 
                file.write(output)
                if b'Done' in output:
                    print("DONE: COMMAND COLLECT_DATA")
                    file.close()
                    return

    def parse_bin_file(self, filepath):
        parsed_data = []

        with open(filepath, 'rb') as file:
            # Read the entire file content
            content = file.read()

            # Decode the content to a string
            content_str = content.decode('utf-8').strip()

            # Split the content by lines
            lines = content_str.split('\r\n')

            for line in lines:
                if line and ',' in line:
                    # Split each line by comma and convert to tuple of integers
                    values = list(map(int, line.split(',')))
                    if len(values) == 2 and values[0] < 1e8:
                        parsed_data.append(values)
            file.close()
        
        return parsed_data
    
    def clear_buffer(self):
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        return
    
    def close_serial(self):
        """close the serial port.
        ALWAYS RUN THIS after finish running experiments
        """
        self.ser.close()
        print("teensy serial closed")


if __name__ == "__main__":
    usb_ports = [usb for usb in list_usb() if 'usb' in usb.lower()]
    if len(usb_ports) == 0:
        raise Exception("no usb")
    else:
        serial_port = usb_ports[0]
        print(usb_ports[0])

    teensy = Serial_Service(serial_port, 115200)
    teensy.collect_data(duration=50000, PLOT=False, SAVE=False, save_dir='./Data/test.bin')
    teensy.close_serial()