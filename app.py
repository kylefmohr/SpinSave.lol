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

        sort_by = request.values.get('sort')

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

        plt.ioff()
        width = 1
        my_dpi = 108

        fig = plt.figure(figsize=(18, 14), dpi=my_dpi)

        song_attempts = json.loads(json.dumps(regular_song_attempts))
        song_attempts = dict(song_attempts.items())
        song_attempts = {k: v for k, v in song_attempts.items() if v is not None and v != 0 and v != ''}
        song_attempts = dict(song_attempts.items())

        stats = list(song_attempts.values())
        #stats = sorted(stats[difficulty_index])
        stats = json.loads(json.dumps(stats))
        new_stats = {}
        final_stats = {'song_title': [], 'song_attempts': [], 'song_completions': []}
        for i in range(len(stats)):
            new_stats[i] = json.loads(stats[i])
            new_stats[i] = new_stats[i].values()
            new_stats[i] = list(new_stats[i])
            final_stats['song_title'].append(new_stats[i][6][:-6])
            final_stats['song_attempts'].append(new_stats[i][3][difficulty_index])
            final_stats['song_completions'].append(new_stats[i][4][difficulty_index])

        if sort_by == 'Attempts':
            zipped_lists = zip(final_stats['song_attempts'], final_stats['song_completions'], final_stats['song_title'])  # whichever dict is listed first will be the one that gets sorted
            sorted_stats = sorted(zipped_lists, reverse=True)
            tuples = zip(*sorted_stats)
            song_attempts, song_completions, song_title = [list(t) for t in tuples]
        elif sort_by == 'Completions':
            zipped_lists = zip(final_stats['song_completions'], final_stats['song_attempts'], final_stats['song_title'])  # whichever dict is listed first will be the one that gets sorted
            sorted_stats = sorted(zipped_lists, reverse=True)
            tuples = zip(*sorted_stats)
            song_completions, song_attempts, song_title = [list(t) for t in tuples]
        plt.xticks(rotation=45, ha='right', fontsize=9)
        plt.bar(song_title, song_attempts, width, color=(0xf7/0xff, 0x67/0xff, 0xff/0xff, 1), edgecolor='black')
        plt.bar(song_title, song_completions, width, color=(0x57/255, 0xbe/255, 0xfc/255, 1), edgecolor='black')

        plt.gcf().subplots_adjust(bottom=0.14)
        ax = plt.gca()
        ax.set_ylabel('Times Attempted/Completed')
        ax.set_xlabel('Song')
        ax.legend(['Times Attempted', 'Times Completed'])
        ax.set_title('Song Attempts vs. Completions')
        fig.savefig('static/attempts.png', dpi=108)
        #plt.show()
        return redirect('static/attempts.png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)