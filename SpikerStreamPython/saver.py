"""Program that can record SpikerBox data and save it as a numpy array file."""

# Standard modules
import argparse
import sys
import time
from typing import List

# Internal modules
from input_stream import *
from plotter import *


def main(args: List = sys.argv):
    """Main entry point.

    Parameters
    ----------
    args : List
        unparsed command line arguments. Default value is sys.argv.
    """
    # Parse command line arguments
    parsed_args = _parse_args(args[1:])

    # Create input stream
    input_stream = SpikerStream(parsed_args.serial_port, parsed_args.chunk_size)

    start_time = time.time()
    print("Starting recording...")
    save_array = input_stream.update()
    while time.time() - start_time < float(parsed_args.recording_time):
        save_array = np.concatenate([input_stream.update(), save_array])
    np.save(parsed_args.filename[0], save_array)
    print("Finishing recording...")


def _parse_args(args: List) -> argparse.Namespace:
    """Parses command line arguments.

    Parameters
    ----------
    args : List
        unparsed command line arguments

    Returns
    -------
    args : argparse.Namespace
        parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="This CLI program is used to test out the SpikerStream interface."
    )

    parser.add_argument(
        "-s", "--s", "-serialport", "--serialport",
        nargs="?",
        default="COM1",
        help="The serial port the SpikerBox is attached to.",
        dest="serial_port"
    )

    parser.add_argument(
        "-t", "--t", "-time", "--time",
        nargs="?",
        default=30,
        help="The recording time in seconds.",
        dest="recording_time"
    )

    parser.add_argument(
        "-f", "--f", "-filename", "--filename",
        nargs=1,
        help="The file name of the saved array.",
        dest="filename"
    )

    parser.add_argument(
        "-c", "--c", "-chunk", "--chunk",
        nargs="?",
        default=10000,
        help="The chunk size when using the SpikerBox stream. 20,000 = 1 second.",
        dest="chunk_size"
    )

    return parser.parse_args(args)


if __name__ == "__main__":
    main()
