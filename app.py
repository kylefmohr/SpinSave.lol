import json

import matplotlib
import requests

matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.switch_backend('Agg')
from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
from flask_caching import Cache

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'FileSystemCache', 'CACHE_DIR': 'cache', 'CACHE_THRESHOLD': 25000, 'CACHE_IGNORE_ERRORS': True})

# utilizing spinsha.re's api to translate save file custom song title to actual custom song title
# for example, it would take a string "CUSTOM_spinshare_5e9bf7e70019a_Stats" and translate it to "Rainbow Road"
@cache.memoize()
def custom_string_to_title(title):
    title1 = title.split('_')[1]
    title2 = title.split('_')[2]
    fileReference = title1 + "_" + title2
    if "spinshare_" not in fileReference:  # not a spinsha.re song, can't look up the title
        return ''
    else:
        url = "https://spinsha.re/api/song/" + fileReference
        r = requests.get(url)
        data = r.json()
        data = data['data'] # drill down one level
        try:
            title = data['title']
        except:
            title = ''
        print(fileReference + ": " + title)
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
            file.save(secure_filename(file.filename)) # sanitize filename, then save the file for processing

        with open(file.filename, 'r', encoding="utf8") as f:
            unparsed_data = f.read()

        json_data = json.loads(unparsed_data)
        song_attempts_data = json_data['largeStringValuesContainer']['values'] # just drilling down a couple levels in the json data so we can more easily ignore irrelevant data
        
        custom_or_original = request.values.get("custom") # get the value of the custom radio button
        
        difficulty_index = {'easy': 0, 'medium': 1, 'hard': 2, 'expert': 3, 'XD': 4}  # save file records song attempts/completions as a 5 item array
        difficulty = request.values.get('difficulty') # get the value of the difficulty radio button
        difficulty_index = difficulty_index[difficulty]

        sort_by = request.values.get('sort') # get the value of the sort radio button

        song_attempts = {}
        for current_song in song_attempts_data:  # separate songs into custom and regular, and remove extraneous entries
            if current_song['key'] == 'MouseUserInputMapping' or current_song['key'] == 'KeyboardUserInputMapping': # removing junk data
                pass
            else:
                if current_song['key'].startswith('CUSTOM'): # all custom songs start with CUSTOM_
                    if custom_or_original == 'custom': # did user select custom songs?
                        song_attempts[current_song['key']] = current_song['val']

                elif 'Random' in current_song['key'] or 'Calibration' in current_song['key'] or 'Create Custom' in current_song['key'] or 'CreateCustomTrack' in current_song['key']:   # more junk data, doesn't accurately show how many times you've attempted a random song, calibration tool value seems incorrect as well
                    pass
                else:
                    if custom_or_original == 'original': # or did user select original songs?
                        song_attempts[current_song['key']] = current_song['val']

        plt.ioff() # turn off interactive mode for plotting the bar graph, since we're just rendering it to a static image
        width = 1
        my_dpi = 108

        fig = plt.figure(figsize=(18, 14), dpi=my_dpi) # customize the chart size

        song_attempts = json.loads(json.dumps(song_attempts))
        song_attempts = dict(song_attempts.items())
        song_attempts = {k: v for k, v in song_attempts.items() if v is not None and v != 0 and v != ''} # remove songs that have no attempts or are empty
        song_attempts = dict(song_attempts.items())

        stats = list(song_attempts.values())
        stats = json.loads(json.dumps(stats))
        new_stats = {}
        final_stats = {'song_title': [], 'song_attempts': [], 'song_completions': [], 'high_score': [], 'best_accuracy': [], 'best_streak': []}
        for i in range(len(stats)):  # finally, this is the for loop that loops through each song in the list of either custom or original songs
            new_stats[i] = json.loads(stats[i])
            new_stats[i] = new_stats[i].values()
            new_stats[i] = list(new_stats[i])
            # try:
            #     if custom_or_original == 'custom':
            #         if custom_lookups <= 50:  # limit to 50 custom songs, otherwise we risk overloading the spinshare api, and also it doesn't look good on a bar graph
            #             title = custom_string_to_title(new_stats[i][6][:-6])
            #             if title == '':
            #                 continue  # skip to next song if we can't find the song title
            #             else:
            #                 custom_lookups += 1
            #                 final_stats['song_title'].append(title)
            #     else:
            try:
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
        song_attempts = []
        song_completions = []
        song_titles = []
        if sort_by == 'Attempts':  # did user select to sort by attempts?
            zipped_lists = zip(final_stats['song_attempts'], final_stats['song_completions'], final_stats['song_title'])  # whichever dict is listed first will be the one that gets sorted
            sorted_stats = sorted(zipped_lists, reverse=True)
            tuples = zip(*sorted_stats)
            song_attempts, song_completions, song_titles = [list(t) for t in tuples]
        elif sort_by == 'Completions':  # or by completions?
            zipped_lists = zip(final_stats['song_completions'], final_stats['song_attempts'], final_stats['song_title'])  # whichever dict is listed first will be the one that gets sorted
            sorted_stats = sorted(zipped_lists, reverse=True)
            tuples = zip(*sorted_stats)
            song_completions, song_attempts, song_titles = [list(t) for t in tuples]
        if custom_or_original == 'custom':
            custom_lookups = 0  # counter for how many custom songs we've looked up

            for i in range(len(song_titles)):
                try:
                    if custom_lookups < 50:
                        song_titles[i] = custom_string_to_title(song_titles[i])
                        if song_titles[i] == '' or song_attempts[i] == 0:
                            song_titles.remove(song_titles[i])
                            song_attempts.remove(song_attempts[i])
                            song_completions.remove(song_completions[i])
                            continue
                        else:
                            custom_lookups += 1
                    else:
                        song_titles.remove(song_titles[i])
                        song_attempts.remove(song_attempts[i])
                        song_completions.remove(song_completions[i])
                except IndexError:
                    print('IndexError: ' + str(i))
                    pass



        plt.xticks(rotation=45, ha='right', fontsize=9)  # customize the x-axis labels (song titles)
        plt.bar(song_titles[:50], song_attempts[:50], width, color=(0xf7/0xff, 0x67/0xff, 0xff/0xff, 1), edgecolor='black')  # plot the attempts bar graph
        plt.bar(song_titles[:50], song_completions[:50], width, color=(0x57/255, 0xbe/255, 0xfc/255, 1), edgecolor='black')  # plot the completions bar graph

        plt.gcf().subplots_adjust(bottom=0.14)  # adjust the bottom margin to make room for long song titles
        ax = plt.gca()

        ax.set_ylabel('Times Attempted/Completed')  # decorating the graph with labels, legend, etc.
        ax.set_xlabel('Song')
        ax.legend(['Times Attempted', 'Times Completed'])
        ax.set_title('Song Attempts vs. Completions')
        fig.savefig('static/attempts.png', dpi=108)
        return redirect('static/attempts.png')  # return the graph to the user

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)