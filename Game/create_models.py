# Standard modules
import argparse
import glob
import sys
import time
from typing import Dict, List, Tuple

# External modules
from catch22 import catch22_all
from joblib import dump
import numpy as np
# Models
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn import svm

# Internal modules
from utils import get_snippet_event, parse_snippet

# Type aliases
Snippets = Dict[str, List[Tuple[np.ndarray, np.ndarray]]]


def main(args: List = sys.argv[1:]):
    """Main entry point.

    Parameters
    ----------
    args : List
        unparsed command line arguments
    """
    parsed_args = _parse_args(args)

    # Select model to train
    models = []
    if parsed_args.model_type == "KNN":
        models.append(KNeighborsClassifier(n_neighbors=5))
    elif parsed_args.model_type == "RFC":
        models.append(RandomForestClassifier())
    elif parsed_args.model_type == "SVM":
        models.append(svm.SVC())
    elif parsed_args.model_type == "all":
        models.append(KNeighborsClassifier(n_neighbors=5))
        models.append(RandomForestClassifier())
        models.append(svm.SVC())
    else:
        print(f"The model type {parsed_args.model_type} is invalid! Please choose a valid model type.")
        sys.exit()

    # Load snippets
    snippets_folder = "../WaveformSnipper/Snippets"
    noise_folder = "../WaveformSnipper/Snippets/Noise"
    print("Loading snippets...")
    snippets = load_snippets({}, snippets_folder)
    print("Loading complete!")
    print("Loading noise snippets...")
    snippets = load_snippets(snippets, noise_folder)
    print("Loading complete!")

    start_time = time.time()
    # Process snippets into catch22 data and labels
    print("Processing snippets...")
    data, labels = process_snippets(snippets)
    print("Processing complete!")

    # Train model
    print("Training...")
    for model in models:
        model.fit(data, labels)
    print("Training complete!")
    elapsed_time = time.time() - start_time
    print(f"This took {elapsed_time:.2f} seconds to complete!")

    # Save model
    if len(models) == 1:
        dump(models[0], f"models/{parsed_args.model_type}.joblib")
    else:
        dump(models[0], f"models/KNN.joblib")
        dump(models[1], f"models/RFC.joblib")
        dump(models[2], f"models/SVM.joblib")


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
        description="This CLI program is used to train models."
    )

    parser.add_argument(
        "model_type",
        choices=["KNN", "RFC", "SVM", "all"],
        help="The type of model to train.",
    )

    return parser.parse_args(args)


def load_snippets(
    snippets: Snippets,
    snippet_folder: str,
) -> Snippets:
    """Load snippets from a folder into a dictionary of event types and slices.

    Parameters
    ----------
    snippets : Snippets
        a dictionary of events and a list of slices.
    snippet_folder : str
        the folder of snippets to load from.

    Returns
    -------
    snippets : Snippets
        the loaded snippets.
    """
    # Find all snippets
    for snippet_file in glob.glob(f"{snippet_folder}/*.npy"):
        # Load data
        snippet = np.load(snippet_file)
        signal_slice, time_slice = parse_snippet(snippet)
        event = get_snippet_event(snippet_file)
        # Looking only at left, right and noise
        if event != "left" and event != "right" and event != "noise":
            continue
        # Add data to dictionary
        if event not in snippets:
            snippets[event] = [(signal_slice, time_slice)]
        else:
            snippets[event].append((signal_slice, time_slice))

    return snippets


def process_snippets(snippets: Snippets) -> Tuple[List, List]:
    """Process snippet data into a list of catch22 features.

    Parameters
    ----------
    snippets : Snippets
        the snippets to process.

    Returns
    -------
    data : List[List]
        list of catch22 features for each snippet.
    labels : List[str]
        corresponding list of labels for each snippet.
    """
    # Compute catch22 data
    data = []
    # Create list of labels and names associated with catch22 data
    labels = []
    for event in snippets:
        for signal_slice, _ in snippets[event]:
            data.append(catch22_all(signal_slice)["values"])
            labels.append(event)
    print(f"There are {len(data)} samples to train/test on.")

    return data, labels


if __name__ == "__main__":
    main()
