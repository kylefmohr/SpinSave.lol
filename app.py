import json
from collections import OrderedDict

import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.switch_backend('Agg')
from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename

app = Flask(__name__)

def custom_string_to_title(title):
    title1 = title.split('_')[1]
    title2 = title.split('_')[2]
    fileReference = title1 + "_" + title2
    if "spinshare_" not in fileReference:
        return ''
    else:
        url = "https://spinsha.re/api/song/" + fileReference
        r = requests.get(url)
        data = r.json()
        data = data['data']
        try:
            title = data['title']
        except:
            title = ''
        print(fileReference + ": " + title)
        return title


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
        
        custom_or_original = request.values.get("custom")
        
        difficulty_index = {'easy': 0, 'medium': 1, 'hard': 2, 'expert': 3, 'XD': 4}  # save file records song attempts/completions as a 5 item array
        difficulty = request.values.get('difficulty')
        difficulty_index = difficulty_index[difficulty]

        sort_by = request.values.get('sort')


        song_attempts = {}
        for current_song in song_attempts_data:  # separate songs into custom and regular, and remove extraneous entries
            if current_song['key'] == 'MouseUserInputMapping' or current_song['key'] == 'KeyboardUserInputMapping':
                pass
            else:
                if current_song['key'].startswith('CUSTOM'):
                    if custom_or_original == 'custom':
                        song_attempts[current_song['key']] = current_song['val']

                elif 'Random' in current_song['key'] or 'Calibration' in current_song['key'] or 'Create Custom' in current_song['key'] or 'CreateCustomTrack' in current_song['key']:   # doesn't accurately show how many times you've attempted a random song, calibration tool value seems incorrect as well
                    pass
                else:
                    if custom_or_original == 'original':
                        song_attempts[current_song['key']] = current_song['val']

        plt.ioff()
        width = 1
        my_dpi = 108

        fig = plt.figure(figsize=(18, 14), dpi=my_dpi)

        song_attempts = json.loads(json.dumps(song_attempts))
        song_attempts = dict(song_attempts.items())
        song_attempts = {k: v for k, v in song_attempts.items() if v is not None and v != 0 and v != ''}
        song_attempts = dict(song_attempts.items())

        stats = list(song_attempts.values())
        stats = json.loads(json.dumps(stats))
        new_stats = {}
        final_stats = {'song_title': [], 'song_attempts': [], 'song_completions': [], 'high_score': [], 'best_accuracy': [], 'best_streak': []}
        custom_lookups = 0
        for i in range(len(stats)):
            new_stats[i] = json.loads(stats[i])
            new_stats[i] = new_stats[i].values()
            new_stats[i] = list(new_stats[i])
            try:
                if custom_or_original == 'custom':
                    if custom_lookups <= 50:  # limit to 50 custom songs, otherwise we risk overloading the spinshare api, and also it doesn't look good on a bar graph
                        title = custom_string_to_title(new_stats[i][6][:-6])
                        if title == '':
                            # go to next index in for loop
                            continue
                        else:
                            custom_lookups += 1
                            final_stats['song_title'].append(title)
                else:
                    final_stats['song_title'].append(new_stats[i][6][:-6])
                final_stats['song_attempts'].append(new_stats[i][3][difficulty_index])
                final_stats['song_completions'].append(new_stats[i][4][difficulty_index])
                final_stats['high_score'].append(new_stats[i][0][difficulty_index]['valueForDifficulty'])
                final_stats['best_accuracy'].append(new_stats[i][1][difficulty_index]['valueForDifficulty'])
                final_stats['best_streak'].append(new_stats[i][2][difficulty_index]['valueForDifficulty'])
            except IndexError:
                pass

        # print(final_stats['best_accuracy'])
        # print(final_stats['best_streak'])
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