# Get json file and print highscores
#
# Usage: python print_highscores.py
# File is always highscores.json
#

import json

with open("highscores.json") as json_file:
    data = json.load(json_file)
    avg_score = sum([score[1] for score in data]) / len(data)
    print("Average score:", avg_score)
    print("All scores:", [score[1] for score in data])
