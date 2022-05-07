import json
from collections import OrderedDict
import matplotlib.pyplot as plt
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

with open('savedata.dat', 'r') as f:
    unparsed_data = f.read()

json_data = json.loads(unparsed_data)
song_attempts_data = json_data['largeStringValuesContainer']['values']

difficulty_index = {'easy': 0, 'medium': 1, 'hard': 2, 'expert': 3, 'XD': 4}  # save file records song attempts/completions as a 5 item array

custom_song_attempts = {}
regular_song_attempts = {}
for current_song in song_attempts_data:
    if current_song['key'] == 'MouseUserInputMapping' or current_song['key'] == 'KeyboardUserInputMapping':
        pass
    else:
        if current_song['key'].startswith('CUSTOM'):
            custom_song_attempts[current_song['key']] = current_song['val']
        elif 'Random' in current_song['key'] or 'Calibration' in current_song['key']:   # doesn't accurately show how many times you've attempted a random song, calibration tool value seems incorrect as well
            pass
        else:
            regular_song_attempts[current_song['key']] = current_song['val']


song_attempts = OrderedDict(sorted(regular_song_attempts.items(), key=lambda t: t[1]))

width = 1       # the width of the bars: can also be len(x) sequence

fig, ax = plt.subplots()


song_attempts = json.loads(json.dumps(song_attempts))
song_attempts = dict(song_attempts.items())
song_attempts = {k: v for k, v in song_attempts.items() if v is not None and v != 0 and v != ''}
song_attempts = dict(song_attempts.items())

stats = song_attempts.values()
new_stats = {}
my_dpi = 108
plt.figure(figsize=(14, 11), dpi=my_dpi)
plt.ion()

for i, current_song in enumerate(stats):
    current_song = json.loads(current_song)
    current_song_name = current_song["statsUniqueString"][:-6]
    times_attempted = current_song["timesAttemptedDifficulty"]
    times_completed = current_song["timesCompletedDifficulty"]
    print(current_song_name)
    print(times_attempted)
    print(times_completed)
    plt.xticks(rotation=45, ha='right', fontsize=9)

    plt.bar(current_song_name, times_attempted, width, label="Times Attempted", color=(0xf7/255, 0x67/255, 0xff/255, 1), edgecolor='black')
    plt.bar(current_song_name, times_completed, width, label="Times Completed", color=(0x57/255, 0xbe/255, 0xfc/255, 1), edgecolor='black')

ax = plt.gca()
plt.show()

# ax.bar(song_attempts['statsUniqueString'], song_attempts['timesAttemptedDifficulty'][4], width, label='Times Attempted')
# ax.bar(song_attempts['statsUniqueString'], song_attempts['timesCompletedDifficulty'][4], width, bottom=song_attempts['timesAttemptedDifficulty'][4], label='Times Completed')
# plt.show()