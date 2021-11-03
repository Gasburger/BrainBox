# Standard modules
from joblib import load
import time
import sys
import wave


# External modules
from astropy import units as u
from astropy.convolution import convolve, Box1DKernel
from catch22 import catch22_all
import numpy as np
import serial
from serial.serialutil import SerialException
from serial.tools import list_ports

# Internal modules
from constants import *
from utils import normalise_signal


class SpikerBox:
    def __init__(self, buffer_time: float, model_type: str, stream_type: str, stream_file: str = "", cport: str = ""):
        self.model = load(MODELS[model_type])
        if stream_type == "SpikerStream":
            self.stream = SpikerStream(cport, chunk=10000)
        elif stream_type == "ArrayStream":
            self.stream = ArrayStream(stream_file, 10000)
        elif stream_type == "WAVStream":
            self.stream = WAVStream(stream_file, 1.5)
        elif stream_type == "None":
            raise SerialException
        else:
            print(f"Invalid stream type {stream_type}! Exiting...")
            sys.exit()
        self.smoothing_flag = stream_type == "ArrayStream" or stream_type == "SpikerStream"
        self.buffer = None
        self.buffer_size = int(buffer_time * SpikerStream.ARRAY_UNIT_SIZE)
        self.buffer_timer = 0

    def process_input(self, controls, tick):
        # Wait self.stream.buffer_time seconds before reading from stream to ensure there is no overlap
        self.buffer_timer += tick
        if self.buffer_timer / 1000.0 < self.stream.buffer_time:
            return controls
        else:
            self.buffer_timer = 0

        # Fill buffer
        raw_data = self.stream.update()
        if self.buffer is None:
            self.buffer = raw_data
        else:
            if len(self.buffer) > self.buffer_size:
                # Reduce it
                self.buffer = self.buffer[len(raw_data) + 1:]
            self.buffer = np.concatenate([self.buffer, raw_data])
        # If buffer is larger than buffer size, we can process the data in it
        if len(self.buffer) > self.buffer_size:
            # Smoothing
            if self.smoothing_flag:
                smooth_width = len(self.buffer) // 50
                amplitude = convolve(self.buffer, Box1DKernel(smooth_width))
            else:
                amplitude = self.buffer
            # Features takes 33 times longer than it should ~0.3 seconds
            features = catch22_all(normalise_signal(amplitude))["values"]
            label = self.model.predict([features])  # Prediction not too bad speed wise ~0.01 seconds
        else:
            label = "noise"
        if label != "noise":
            print(label)
        controls[CONTROL_LEFT] = 1 if label == "left" else 0
        controls[CONTROL_RIGHT] = 1 if label == "right" else 0
        # controls[CONTROL_SHOOT] = 1 if label == "blink" else 0
        return controls


class InputStream:
    """Input stream base class.

    Attributes
    ----------
    chunk : int
        size of the input buffer.
    """

    def __init__(self, chunk: int):
        """Initialises the input stream.

        Parameters
        ----------
        chunk : int
            size of the input buffer.

        Implement for each class inheriting from this base class.
        """
        self.chunk = chunk

    def update(self) -> np.ndarray:
        """Reads data from the input buffer.

        Implement for each class inheriting from this base class.
        """
        pass

    def close(self) -> None:
        """Closes the input stream.

        Implement for each class inheriting from this base class.
        """
        pass


class SpikerStream(InputStream):
    """Streams in data from Backyard Brains' SpikerBox.

    Attributes
    ----------
    serial_handle : serial.Serial
        a handle to the serial port the SpikerBox is connected to.
    """

    CHUNK_UNIT_TIME = 20000
    ARRAY_UNIT_SIZE = (CHUNK_UNIT_TIME // 2) - 1
    # Baud rate is the rate of change of symbols (i.e. for cases where the data is non-binary)
    BAUDRATE = 230400

    def __init__(self, cport, chunk: int = 20000):
        """Initialises and opens the input stream.

        Parameters
        ----------
        cport : str
            the name of the serial port the SpikerBox is connected to.
        chunk : int
            the size of the input buffer. Note 20 000 = 1 second of time.
        """
        super().__init__((chunk // 2) - 1)

        # Create a serial handle
        try:
            print(f"Attempting to open port {cport}")
            self.serial_handle = serial.Serial(port=cport, baudrate=SpikerStream.BAUDRATE)
        # Otherwise list serial ports and exit
        except SerialException as _:
            print("The list of COM ports is...")
            ports = list_ports.comports()
            for idx, port in enumerate(ports):
                print(f"\t{idx+1}: {port}")
            raise SerialException

        # Set read timeout
        self.serial_handle.timeout = chunk/20000.0
        self.buffer_time = chunk/20000.0

    def update(self) -> np.ndarray:
        """Reads the input stream from the arduino/SpikerBox.

        Returns
        -------
        data : np.ndarray
            streamed processed data coming from the SpikerBox.
        """
        data = self.read_arduino()
        processed_data = SpikerStream.process_data(data)
        return processed_data

    def close(self) -> None:
        """Closes the input stream by closing the serial port."""

        # Close the serial port
        if self.serial_handle.read():
            self.serial_handle.flushInput()
            self.serial_handle.flushOutput()
            self.serial_handle.close()

    def read_arduino(self) -> np.ndarray:
        """Read the input buffer.

        Returns
        -------
        data : np.ndarray
            the raw data from the input buffer read as integers.
        """
        data = self.serial_handle.read(self.chunk)
        return np.array([int(data_bit) for data_bit in data])

    @staticmethod
    def process_data(data: np.ndarray) -> np.ndarray:
        """Processes the raw data from the input buffer.

        Parameters
        ----------
        data : np.ndarray
            unprocessed input buffer data.

        Returns
        -------
        result : np.ndarray
            processed input buffer data.
        """
        result = []
        i = 1
        while i < (len(data) - 1):
            # Found beginning of frame
            if data[i] > 127:
                # Extract one sample from 2 bytes
                intout = (np.bitwise_and(data[i], 127)) * 128
                i += 1
                intout = intout + data[i]
                result = np.append(result, intout)
            i += 1
        return result


class ArrayStream(InputStream):
    """Streams in data loaded from a numpy array file.

    Attributes
    ----------
    chunk : int
        size of the input buffer.
    """

    def __init__(self, array_file: str, chunk: int):
        """Initialises the input stream.

        Parameters
        ----------
        array_file: str
            the path of the array to stream in.
        chunk : int
            the size of the input buffer. Note 20 000 = 1 second of time.

        Implement for each class inheriting from this base class.
        """
        super().__init__((chunk // 2) - 1)
        self.array = np.load(array_file)
        self.buffer_time = chunk / 20000
        self.pointer = 0

    def update(self) -> np.ndarray:
        """Reads data from the input buffer.

        Implement for each class inheriting from this base class.
        """
        array_slice = self.array[self.pointer:self.pointer + self.chunk]
        self.pointer += self.chunk
        if self.pointer > len(self.array):
            self.pointer = 0
            print("Restarting stream...")
        return array_slice

    def close(self) -> None:
        """Closes the input stream."""
        pass


class WAVStream(InputStream):
    """Streams in data loaded from a numpy array file.

    Attributes
    ----------
    chunk : int
        size of the input buffer.
    """

    def __init__(self, wav_file: str, buffer_time: float):
        """Initialises the input stream.

        Parameters
        ----------
        array_file: str
            the path of the array to stream in.
        chunk : int
            the size of the input buffer. Note 20 000 = 1 second of time.

        Implement for each class inheriting from this base class.
        """

        # Open .wav file
        w = wave.open(wav_file)
        # Extract raw audio from .wav file
        self.array = np.array(np.frombuffer(w.readframes(-1), dtype=np.int16), dtype=np.float64).tolist()
        super().__init__(int(buffer_time * w.getframerate()))
        w.close()
        self.pointer = 0
        self.buffer_time = buffer_time

    def update(self) -> np.ndarray:
        """Reads data from the input buffer.

        Implement for each class inheriting from this base class.
        """
        array_slice = self.array[self.pointer:self.pointer + self.chunk]
        self.pointer += self.chunk
        if self.pointer > len(self.array):
            self.pointer = 0
            print("Restarting stream...")
        return array_slice

    def close(self) -> None:
        """Closes the input stream."""
        pass
