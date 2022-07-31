import json

import matplotlib
import requests

matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.switch_backend('Agg')
from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename

app = Flask(__name__)


# utilizing spinsha.re's api to translate save file custom song title to actual custom song title
# for example, it would take a string "CUSTOM_spinshare_5e9bf7e70019a_Stats" and translate it to "Rainbow Road"
def custom_string_to_title(title):
    title1 = title.split('_')[1]
    title2 = title.split('_')[2]
    file_reference = title1 + "_" + title2
    if "spinshare_" not in file_reference:  # not a spinsha.re song, can't look up the title
        return ''
    else:
        url = "https://spinsha.re/api/song/" + file_reference
        r = requests.get(url)
        data = r.json()
        data = data['data']  # drill down one level

        try:
            title = data['title']
        except:
            title = ''
        print(file_reference + ": " + title)
        return title


# defines index.html as the render template for flask
@app.route('/')
def upload_file():
    return render_template('index.html')


# on POST request (when user submits form + save file), run work_with_file() method
@app.route('/', methods=['POST'])
def work_with_file():
    if request.method == 'POST':
        file = request.files['file']
        if file.filename != '':
            file.save(secure_filename(file.filename))  # sanitize filename, then save the file for processing

        with open(file.filename, 'r', encoding="utf8") as f:
            unparsed_data = f.read()

        json_data = json.loads(unparsed_data)
        song_attempts_data = json_data['largeStringValuesContainer']['values']  # drilling down to the data we want

        custom_or_original = request.values.get("custom")  # get the value of the custom radio button

        # save file records song attempts/completions as a 5 item array
        difficulty_dict = {'easy': 0, 'medium': 1, 'hard': 2, 'expert': 3, 'XD': 4}
        difficulty = request.values.get('difficulty')  # get the value of the difficulty radio button
        difficulty_index = difficulty_dict[difficulty]

        sort_by = request.values.get('sort')  # get the value of the sort radio button (Attempts or Completions)

        song_attempts = {}
        for current_song in song_attempts_data:  # separate songs into custom and regular, and remove extraneous entries
            song_title_in_file = current_song['key']
            if song_title_in_file == 'MouseUserInputMapping' or song_title_in_file == 'KeyboardUserInputMapping' or not song_title_in_file.endswith(
                    '_Stats'):  # remove extraneous entries
                pass
            else:
                song_title_truncated = song_title_in_file[:-6]  # remove the "_Stats" from the end of the song title
                if 'Random' in song_title_truncated \
                        or 'Calibration' in song_title_truncated \
                        or 'Create Custom' in song_title_truncated \
                        or 'CreateCustomTrack' in song_title_truncated:  # removing junk data
                    pass
                elif custom_or_original == 'custom' or custom_or_original == 'original':  # did user select custom song radio button?
                    song_attempts[song_title_truncated] = current_song['val']

        plt.ioff()  # turn off interactive mode for the graph, since we're returning an image
        width = 1
        my_dpi = 108

        fig = plt.figure(figsize=(18, 14), dpi=my_dpi)  # customize the chart size

        stats = {k: v for k, v in song_attempts.items()
                 if v is not None
                 and v != 0
                 and v != ''}  # remove songs that have no attempts or are empty

        new_stats = {}
        final_stats = {'song_title': [],
                       'song_attempts': [],
                       'song_completions': [],
                       'high_score': [],
                       'best_streak': [],
                       'performance_visualization': []}

        for k, v in stats.items():
            v = json.loads(v)
            if custom_or_original == 'custom' and not k.startswith(
                    'CUSTOM_'):  # filter out OST if user selected customs
                continue
            elif custom_or_original == 'original' and k.startswith(
                    'CUSTOM_'):  # filter out custom songs if user selected originals
                continue
            try:
                final_stats['performance_visualization'].append(v.get('performances')[difficulty_index].get('v'))
            except TypeError:  # this error is likely hit when the save data for this song hasn't been upgraded to the new format. playing the song once after the update should fix this.
                continue
            final_stats['song_title'].append(k)
            final_stats['song_attempts'].append(v.get('timesAttemptedDifficulty')[difficulty_index])
            final_stats['song_completions'].append(v.get('timesCompletedDifficulty')[difficulty_index])
            final_stats['high_score'].append(v.get('bestScoresForDifficulty')[difficulty_index])
            final_stats['best_streak'].append(v.get('bestStreakForDifficulty')[difficulty_index])

        song_attempts = []
        song_completions = []
        song_titles = []
        if sort_by == 'Attempts':  # did user select to sort by attempts?
            zipped_lists = zip(final_stats['song_attempts'], final_stats['song_completions'], final_stats[
                'song_title'])  # whichever dict is listed first will be the one that gets sorted
            sorted_stats = sorted(zipped_lists, reverse=True)
            tuples = zip(*sorted_stats)
            song_attempts, song_completions, song_titles = [list(t) for t in tuples]
        elif sort_by == 'Completions':  # or by completions?
            zipped_lists = zip(final_stats['song_completions'], final_stats['song_attempts'], final_stats[
                'song_title'])  # whichever dict is listed first will be the one that gets sorted
            sorted_stats = sorted(zipped_lists, reverse=True)
            tuples = zip(*sorted_stats)
            song_completions, song_attempts, song_titles = [list(t) for t in tuples]

        if custom_or_original == 'custom':
            custom_lookups = 0  # counter for how many custom songs we've looked up
            custom_song_titles = []  # list of custom song titles
            custom_song_attempts = []  # list of custom song attempts
            custom_song_completions = []  # list of custom song completions
            for i in range(len(song_titles)):
                try:
                    if custom_lookups < 50:
                        translated_title = custom_string_to_title(song_titles[i])  # rename to the actual song title
                        # if lookup fails, or if song has never been attempted, remove it from the list
                        if translated_title == '' or song_attempts[i] == 0:
                            continue
                        # if we've already looked up another version of this song, don't increment the counter
                        elif translated_title in custom_song_titles:
                            index = song_titles.index(translated_title)
                            custom_song_attempts[index] += song_attempts[i]  # combine the attempts and completions
                            custom_song_completions[index] += song_completions[i]
                            continue
                        else:  # lookup successful, first time we've seen this song, increment counter
                            song_titles[i] = translated_title
                            custom_song_titles.append(translated_title)
                            custom_song_attempts.append(song_attempts[i])
                            custom_song_completions.append(song_completions[i])
                            custom_lookups += 1
                    else:
                        pass
                except IndexError:
                    pass
            song_titles = custom_song_titles
            song_attempts = custom_song_attempts
            song_completions = custom_song_completions
            #  end of 'if custom'

        plt.xticks(rotation=45, ha='right', fontsize=9)  # customize the x-axis labels (song titles)
        plt.bar(song_titles[:50], song_attempts[:50], width, color=(0xf7 / 0xff, 0x67 / 0xff, 0xff / 0xff, 1),
                edgecolor='black')  # plot the attempts bar graph
        plt.bar(song_titles[:50], song_completions[:50], width, color=(0x57 / 255, 0xbe / 255, 0xfc / 255, 1),
                edgecolor='black')  # plot the completions bar graph

        plt.gcf().subplots_adjust(bottom=0.14)  # adjust the bottom margin to make room for long song titles
        ax = plt.gca()

        ax.set_ylabel('Times Attempted/Completed')  # decorating the graph with labels, legend, etc.
        ax.set_xlabel('Song')
        ax.legend(['Times Attempted', 'Times Completed'])
        ax.set_title('Song Attempts vs. Completions')
        fig.savefig('static/attempts.png', dpi=108)
        return redirect('static/attempts.png')  # return the graph to the user


if __name__ == '__main__':
    app.run(host='0.0.0.0')
