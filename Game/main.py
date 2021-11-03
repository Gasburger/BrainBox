# Standard modules
import argparse
import sys
from typing import List

# External modules

# Local modules
from constants import *
from game import Game


def main(args: List = sys.argv[1:]):
    """Main game function. Initialises the game and runs the game loop."""
    parsed_args = _parse_args(args)
    keyboard = parsed_args.stream_type == "None"

    game = Game(
        keyboard=keyboard,
        model_type=parsed_args.model_type,
        stream_type=parsed_args.stream_type,
        stream_file=parsed_args.stream_file,
        cport=parsed_args.cport
    )
    while True:
        game.update()
        game.draw()


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
        description="This game is to be controlled using SpikerBox input."
    )

    parser.add_argument(
        "-m", "--m", "-model", "--model",
        default=RFC,
        choices=[KNN, RFC, SVM],
        help="The type of model to train.",
        dest="model_type"
    )

    parser.add_argument(
        "-s", "--s", "-stream", "--stream",
        default="None",
        choices=[SPIKERSTREAM, ARRAYSTREAM, WAVSTREAM, "None"],
        help="Type of stream to use.",
        dest="stream_type"
    )

    parser.add_argument(
        "-f", "--f", "-file", "--file",
        nargs="?",
        default="",
        type=str,
        help="File to stream from.",
        dest="stream_file"
    )

    parser.add_argument(
        "-p", "--p", "-port", "--port",
        nargs="?",
        type=str,
        default="COM1",
        help="The serial port of the SpikerBox.",
        dest="cport"
    )

    return parser.parse_args(args)


if __name__ == "__main__":
    main()
