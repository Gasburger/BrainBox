# PHYS3888 Spiker Box Training Group 3

## How to use main

* **main** is a function that takes in a value corresponding to which week the data it should process is from. If no input is given, it will then default to week 3's data.

## Adding new data

* If data from a week is to be added, first create a new folder named "Week {currentWeek}" and then inside that folder create another folder called "Output". Add the .wav and .txt data to the folder named "Week {currentWeek}".

## Annotations/Events parser

* Parses Spiker Box events files returning a map of tags and timestamps.

### Week 3 Data Explained

* aw1, aw2 and aw3 are recordings of brain alpha waves (~10 Hz). The tags are either eyes open or eyes closed. The smoothedalpharange plot attempts to show the strength of the alpha wave signal.
* eye1l2r3b is a recording of eye movements. Tags are either left, right or blink. The smoothedalpharange plot is meaningless for this recording.
