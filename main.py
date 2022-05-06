import json
from collections import OrderedDict
from collections import ChainMap

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

with open('savedata.dat', 'r') as f:
    unparsed_data = f.read()


def remove_null(stats):
    parsedStats = {}
    for key, value in stats.items():
        if value is None or value == 0 or value == '':
            pass
        else:
            parsedStats[key] = value
    return parsedStats


json_data = json.loads(unparsed_data)
song_attempts_data = json_data['largeStringValuesContainer']['values']

custom_song_attempts = {}
regular_song_attempts = {}
for current_song in song_attempts_data:
    if current_song['key'] == 'MouseUserInputMapping' or current_song['key'] == 'KeyboardUserInputMapping':
        pass
    else:
        if current_song['key'].startswith('CUSTOM'):
            custom_song_attempts[current_song['key']] = current_song['val']
        else:
            regular_song_attempts[current_song['key']] = current_song['val']


expert_song_attempts = OrderedDict(sorted(regular_song_attempts.items(), key=lambda t: t[1]))

width = 1       # the width of the bars: can also be len(x) sequence

fig, ax = plt.subplots()

# ax.bar(labels, men_means, width, yerr=men_std, label='Men')
# ax.bar(labels, women_means, width, yerr=women_std, bottom=men_means,
#        label='Women')
# for current_song in custom_song_attempts:
#     print(f'{current_song} - {custom_song_attempts[current_song]}')
#             custom_song_attempts['times_attempted'] = current_song['timesAttemptedDifficulty']
# parsed_expert = {}
# for current_song in expert_song_attempts["timesAttemptedDifficulty"]:
#     print(current_song)
expert = {}
expert_song_attempts = json.loads(json.dumps(expert_song_attempts))
#expert_song_attempts = expert_song_attempts.values()
expert_song_attempts = dict(expert_song_attempts.items())
expert = {k: v for k, v in expert_song_attempts.items() if v is not None and v != 0 and v != ''}
#expert = expert.values()
expert = dict(expert.items())

stats = expert.values()
new_stats = {}
plt.ion()

for i, current_song in enumerate(stats):
    current_song = json.loads(current_song)
    print(current_song["statsUniqueString"][:-6])
    #add the current song to the new_stats dict
    new_stats[current_song["statsUniqueString"][:-6]] = current_song
    new_stats[current_song["statsUniqueString"][:-6]]["timesAttemptedDifficulty"] = current_song["timesAttemptedDifficulty"]
    print(current_song["timesAttemptedDifficulty"])
    print(current_song["timesCompletedDifficulty"])
    new_stats[current_song["statsUniqueString"][:-6]]["timesCompletedDifficulty"] = current_song["timesCompletedDifficulty"]
    plt.xticks(rotation=90)

    plt.bar(current_song["statsUniqueString"][:-6], current_song["timesAttemptedDifficulty"], width, label="Times Attempted")
    plt.bar(current_song["statsUniqueString"][:-6], current_song["timesCompletedDifficulty"], width, label="Times Completed")


plt.subplots_adjust(bottom=0.35)
plt.show()

# ax.bar(expert_song_attempts['statsUniqueString'], expert_song_attempts['timesAttemptedDifficulty'][4], width, label='Times Attempted')
# ax.bar(expert_song_attempts['statsUniqueString'], expert_song_attempts['timesCompletedDifficulty'][4], width, bottom=expert_song_attempts['timesAttemptedDifficulty'][4], label='Times Completed')
# plt.show()