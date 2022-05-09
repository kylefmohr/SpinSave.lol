import json
from collections import OrderedDict


import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.switch_backend('Agg')
from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename

app = Flask(__name__)


@app.route('/')
def upload_file():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def work_with_file():
    if request.method == 'POST':
        file = request.files['file']
        if file.filename != '':
            file.save(secure_filename(file.filename))

        with open(file.filename, 'r', encoding="utf8") as f:
            unparsed_data = f.read()

        json_data = json.loads(unparsed_data)
        song_attempts_data = json_data['largeStringValuesContainer']['values']

        difficulty_index = {'easy': 0, 'medium': 1, 'hard': 2, 'expert': 3, 'XD': 4}  # save file records song attempts/completions as a 5 item array
        difficulty = request.values.get('difficulty')
        difficulty_index = difficulty_index[difficulty]
        custom_song_attempts = {}
        regular_song_attempts = {}
        for current_song in song_attempts_data:
            if current_song['key'] == 'MouseUserInputMapping' or current_song['key'] == 'KeyboardUserInputMapping':
                pass
            else:
                if current_song['key'].startswith('CUSTOM'):
                    custom_song_attempts[current_song['key']] = current_song['val']
                elif 'Random' in current_song['key'] or 'Calibration' in current_song['key'] or 'Create Custom' in current_song['key'] or 'CreateCustomTrack' in current_song['key']:   # doesn't accurately show how many times you've attempted a random song, calibration tool value seems incorrect as well
                    pass
                else:
                    regular_song_attempts[current_song['key']] = current_song['val']

        song_attempts = OrderedDict(sorted(regular_song_attempts.items(), key=lambda t: t[1]))
        plt.ioff()
        width = 1
        my_dpi = 108

        fig = plt.figure(figsize=(18, 14), dpi=my_dpi)


        song_attempts = json.loads(json.dumps(song_attempts))
        song_attempts = dict(song_attempts.items())
        song_attempts = {k: v for k, v in song_attempts.items() if v is not None and v != 0 and v != ''}
        song_attempts = dict(song_attempts.items())

        stats = song_attempts.values()

        for i, current_song in enumerate(stats):
            current_song = json.loads(current_song)
            try:  # needed to try/except this after testing this on other users saved data. It wasn't necessary on mine, but multiple other users ran into errors without it
                current_song_name = current_song["statsUniqueString"][:-6]  # statsUniqueString is usually, for example, "I See Lite_Stats"
                times_attempted = current_song["timesAttemptedDifficulty"][difficulty_index]
                times_completed = current_song["timesCompletedDifficulty"][difficulty_index]
            except KeyError:
                pass

            print(current_song_name)
            print(times_attempted)
            print(times_completed)
            plt.xticks(rotation=45, ha='right', fontsize=9)

            plt.bar(current_song_name, times_attempted, width, label="Times Attempted", color=(0xf7/0xff, 0x67/0xff, 0xff/0xff, 1), edgecolor='black')
            # The colors are formatted like that because I had a hexadecimal color value (0xf767ff), but matplotlib wants an RGB decimal value, where 1, 0, 1, would be 0xFF00FF. The last number is the transparency. edgecolor gives the bars an outline
            plt.bar(current_song_name, times_completed, width, label="Times Completed", color=(0x57/255, 0xbe/255, 0xfc/255, 1), edgecolor='black')
        plt.gcf().subplots_adjust(bottom=0.14)
        fig.savefig('static/attempts.png', dpi=108)
        plt.show()
        return redirect('static/attempts.png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)