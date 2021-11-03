# Waveform Snipper

The waveform snipper is a tool that creates small snippets of SpikerRecorder waveform recordings. These snippets are created
around timestamps recorded by SpikerRecorder.

## Usage

* Add the folder containing the .wav and .txt files as a command line argument and the script will create snippets automatically, 
saving it to a specified folder or the Snippets folder in WaveformSnipper.
* Other parameters can be changed using other command line arguments which you can see the details of by entering -help as one
of the command line arguments.

## Opening snippets

* To open a snippet you must use numpy's load function like this **arr** = numpy.load(*filename*). The amplitude is the first row
of the array and the time is the second row. There is a function called ***parse_snippet*** located in ***main.py*** that can
separate these arrays given a loaded snippet array.

## Snipper Viewer

Can be used to view a particular snippet.

## Snipper Processor

Creates training data and labels to train a KNN model. Also tests the model's accuracy by doing a train_test split.

## Levenshtein checker

Look up Levenshtein distance function for python as a way to measure accuracy e.g.

* LRRRLLL
* LRLRLRR
