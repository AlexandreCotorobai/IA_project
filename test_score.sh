#!/bin/bash

# Remove the highscores.json file if it exists
rm -f highscores.json

# Get the number of times to run the code if it is provided
if [ $# -eq 1 ]
then
    num=$1
else
    num=10
fi

# Run the code num times
for ((i=0; i<num; i++))
do
    python3 student.py
    sleep 1
done

# Print the highscores
python3 print_highscores.py
