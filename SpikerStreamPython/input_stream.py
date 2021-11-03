"""The two input streams, audio and SpikerBox."""


# Standard modules
import struct
import sys

# External modules
import numpy as np
# Import flags
failed_imports = {"audio": False, "serial": False}
try:
    import pyaudio
    failed_imports["audio"] = False
except ImportError:
    failed_imports["audio"] = True
try:
    import serial
    from serial.serialutil import SerialException
    from serial.tools import list_ports
    failed_imports["serial"] = False
except ImportError:
    failed_imports["serial"] = True


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


class AudioStream(InputStream):
    """Streams in audio input.

    Attributes
    ----------
    pyaudio_instance : pyaudio.PyAudio
        an instance of PyAudio used to open and close audio input streams.
    stream : pyaudio.Stream
        an audio stream.

    Class Attributes
    ----------------
    FORMAT : any
        input stream data type.
    CHANNELS : int
        number of audio channels. Currently only single channel is supported.
    RATE : int
        audio sample rate.
    CHUNK : int
        size of the input buffer.
    """

    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 2 * 1024

    def __init__(self):
        """Initialises and opens the audio stream."""
        super().__init__(AudioStream.CHUNK)

        # Quit if imports failed
        if failed_imports["audio"]:
            print("Failed to import the audio library! AudioStreams are currently unavailable!")
            sys.exit()

        # Initialise audio stream
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = self.pyaudio_instance.open(
            format=AudioStream.FORMAT,
            channels=AudioStream.CHANNELS,
            rate=AudioStream.RATE,
            input=True,
            output=True,
            frames_per_buffer=self.chunk,
        )

        self.array_size = 2 * self.chunk

    def update(self) -> np.ndarray:
        """Reads the audio stream.

        Returns
        -------
        wave_y : np.ndarray
            slightly processed data read from the input buffer.
        """
        # Read the binary data from the input buffer
        wave_y = self.stream.read(AudioStream.CHUNK)
        # Decode the binary data
        wave_y = struct.unpack(str(2 * AudioStream.CHUNK) + "B", wave_y)
        # Process the data to make sure the numbers are in the range 0-255
        wave_y = np.array(wave_y, dtype="b")[::2] + 128
        return wave_y

    def close(self) -> None:
        """Closes the audio stream."""
        self.pyaudio_instance.close(self.stream)


class SpikerStream(InputStream):
    """Streams in data from Backyard Brains' SpikerBox.

    Attributes
    ----------
    serial_handle : serial.Serial
        a handle to the serial port the SpikerBox is connected to.
    """

    def __init__(self, cport, chunk: int = 20000):
        """Initialises and opens the input stream.

        Parameters
        ----------
        cport : str
            the name of the serial port the SpikerBox is connected to.
        chunk : int
            the size of the input buffer. Note 20 000 = 1 second of time.
        """
        super().__init__(chunk)
        # Quit if imports failed
        if failed_imports["serial"]:
            print("Failed to import the serial library! SpikerStreams are currently unavailable!")
            sys.exit()

        # Baud rate is the rate of change of symbols (i.e. for cases where the data is non-binary)
        baudrate = 230400

        # Create a serial handle
        try:
            self.serial_handle = serial.Serial(port=cport, baudrate=baudrate)
        # Otherwise list serial ports and exit
        except SerialException as e:
            print(e)
            print("The list of COM ports is...")
            ports = list_ports.comports()
            for idx, port in enumerate(ports):
                print(f"\t{idx+1}: {port}")
            print("Exiting...")
            sys.exit()

        # Set read timeout
        self.serial_handle.timeout = self.chunk/20000.0
        self.array_size = (self.chunk // 2) - 1

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
