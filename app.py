import json
import os
import matplotlib
import requests
from pathlib import Path
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.switch_backend('Agg')
from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename

app = Flask(__name__)


# utilizing spinsha.re's api to translate save file custom song title to actual custom song title
# for example, it would take a string "CUSTOM_spinshare_5e9bf7e70019a_Stats" and translate it to "Rainbow Road"
def custom_string_to_title(title, difficulty_lookup_string):
    title1 = title.split('_')[1]
    title2 = title.split('_')[2]
    file_reference = title1 + "_" + title2
    if "spinshare_" not in file_reference:  # not a spinsha.re song, can't look up the title
        return ''
    else:
        if local_lookup(file_reference) != '':  # first attempt looking up the song in the local cache
            return local_lookup(file_reference)
        else:  # if the song is not in the local cache, then use the api
            url = "https://spinsha.re/api/song/" + file_reference
            r = requests.get(url)
            data = r.json()
            data = data['data']  # drill down one level

            try:
                title = data['title']
                difficulty = data[difficulty_lookup_string]
            except:
                title = ''
                difficulty = -1
            print(file_reference + ": " + title + " difficulty: " + str(difficulty))
            save_lookup(file_reference, title, difficulty)
            return title  # not returning difficulty yet, just saving it to local cache


def local_lookup(file_reference):
    filename = "cache/lookups.json"
    try:
        with open(filename, 'r+') as file:
            data = json.load(file)
            for entry in data["lookups"]:
                if file_reference in entry:
                    return entry[file_reference][0]
                else:
                    return ''
    except FileNotFoundError:
        if not os.path.exists(filename.split('/')[0]):
            os.makedirs(filename.split('/')[0])
        print("File not found when performing local lookup, creating new file")
        with open(filename, 'w+') as file:
            data = {
                "lookups": {}
            }
            json.dump(data, file, indent=4)
        local_lookup(file_reference)  # once FileNotFoundError is fixed, recursively call this function


def save_lookup(file_reference, title, difficulty):
    filename = "cache/lookups.json"
    new_entry = {file_reference: [title, difficulty]}
    with open(filename, 'r+') as file:
        data = json.load(file)
        data["lookups"].append(new_entry)
        file.seek(0)
        json.dump(data, file, indent=4)


def get_custom_song_difficulty(title):
    difficulty = -1
    filename = "cache/lookups.json"
    try:
        with open(filename, 'r+') as file:
            data = json.load(file)
            for entry in data["lookups"][0]:
                if title in entry:
                    difficulty = entry[title][1]
    except FileNotFoundError:
        print("File not found when looking up difficulty")
        pass
    return int(difficulty)


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
        song_attempts_data = json_data['largeStringValuesContainer']['values']  # drilling down to the data we want

        difficulty_index = {'easy': 0, 'medium': 1, 'hard': 2, 'expert': 3, 'XD': 4}
        difficulty = request.values.get('difficulty')  # get the value of the difficulty radio button
        difficulty_index = difficulty_index[difficulty]
        
        custom_or_original = request.values.get("custom")  # get the value of the custom radio button
        enable_difficulty_range = request.values.get("difficulty_range")  # get the value of the difficulty range checkbox
        if enable_difficulty_range == "on":  # enable filtering by difficulty range
            difficulty_range_enabled = True
            min_difficulty = int(request.values.get("min_difficulty"))
            max_difficulty = int(request.values.get("max_difficulty"))
            difficulty_range = [min_difficulty, max_difficulty]
            difficulty_lookup_string = ''
            match difficulty_index:
                case 0:
                    difficulty_lookup_string = 'easyDifficulty'    # These are the names that the spinsha.re api gives the difficulties
                case 1:
                    difficulty_lookup_string = 'normalDifficulty'
                case 2:
                    difficulty_lookup_string = 'hardDifficulty'
                case 3:
                    difficulty_lookup_string = 'expertDifficulty'
                case 4:
                    difficulty_lookup_string = 'XDDifficulty'

        else:
            difficulty_lookup_string = ''
            difficulty_range_enabled = False
            difficulty_range = [-1, -1]
        # save file records song attempts/completions as a 5 item array

        sort_by = request.values.get('sort')  # get the value of the sort radio button (Attempts or Completions)

        song_attempts = {}
        for current_song in song_attempts_data:  # separate songs into custom and regular, and remove extraneous entries
            if current_song['key'] == 'MouseUserInputMapping' or current_song['key'] == 'KeyboardUserInputMapping': # removing junk data
                pass
            else:
                if current_song['key'].startswith('CUSTOM'): # all custom songs start with CUSTOM_
                    if custom_or_original == 'custom': # did user select custom song radio button?
                        song_attempts[current_song['key']] = current_song['val']
                elif 'Random' in current_song['key'] \
                        or 'Calibration' in current_song['key'] \
                        or 'Create Custom' in current_song['key'] \
                        or 'CreateCustomTrack' in current_song['key']:   # removing junk data
                    pass
                else:
                    if custom_or_original == 'original':  # or did user select original songs?
                        song_attempts[current_song['key']] = current_song['val']

        plt.ioff()  # turn off interactive mode for the graph, since we're returning an image
        width = 1
        my_dpi = 108

        fig = plt.figure(figsize=(18, 14), dpi=my_dpi)  # customize the chart size

        song_attempts = json.loads(json.dumps(song_attempts))
        song_attempts = dict(song_attempts.items())
        song_attempts = {k: v for k, v in song_attempts.items()
                         if v is not None
                         and v != 0
                         and v != ''}  # remove songs that have no attempts or are empty
        song_attempts = dict(song_attempts.items())

        stats = list(song_attempts.values())
        stats = json.loads(json.dumps(stats))
        new_stats = {}
        final_stats = {'song_title': [],
                       'song_attempts': [],
                       'song_completions': [],
                       'high_score': [],
                       'best_accuracy': [],
                       'best_streak': []}
        for i in range(len(stats)):  # loops through each song in the list of either custom or original songs
            new_stats[i] = json.loads(stats[i])
            new_stats[i] = new_stats[i].values()
            new_stats[i] = list(new_stats[i])

            try:
                final_stats['song_title'].append(new_stats[i][6][:-6])
                final_stats['song_attempts'].append(new_stats[i][3][difficulty_index])
                final_stats['song_completions'].append(new_stats[i][4][difficulty_index])
                final_stats['high_score'].append(new_stats[i][0][difficulty_index]['valueForDifficulty'])
                final_stats['best_accuracy'].append(new_stats[i][1][difficulty_index]['valueForDifficulty'])
                final_stats['best_streak'].append(new_stats[i][2][difficulty_index]['valueForDifficulty'])
            except IndexError:
                pass

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
            custom_song_titles = []  # list of custom song titles
            custom_song_attempts = []  # list of custom song attempts
            custom_song_completions = []  # list of custom song completions
            custom_song_difficulties = []  # list of custom song difficulties
            for i in range(len(song_titles)):
                if difficulty_range_enabled:  # if the user wants to filter by difficulty range
                    translated_title = custom_string_to_title(song_titles[i], difficulty_lookup_string)  # rename to the actual song title
                    difficulty = get_custom_song_difficulty(translated_title)  # get the difficulty of the song
                    # if lookup fails, or if song has never been attempted, remove it from the list
                    if translated_title == '' or song_attempts[i] == 0:
                        continue
                    # if we've already looked up another version of this song
                    elif translated_title in custom_song_titles:
                        index = song_titles.index(translated_title)
                        custom_song_attempts[index] += song_attempts[i]  # combine the attempts and completions
                        custom_song_completions[index] += song_completions[i]
                        continue
                    else:  # lookup successful, first time we've seen this song
                        if difficulty_range[0] <= difficulty <= difficulty_range[1]:  # if the song is in the difficulty range
                            song_titles[i] = translated_title
                            custom_song_titles.append(translated_title)
                            custom_song_attempts.append(song_attempts[i])
                            custom_song_completions.append(song_completions[i])
                        else:
                            print('Song not in range, skipping...')
                else:  # if the user doesn't want to filter by difficulty range
                    try:
                        if custom_lookups < 50:
                            translated_title = custom_string_to_title(song_titles[i])   # rename to the actual song title
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
                        else:  # if we've looked up 50 songs, stop looking
                            pass
                    except IndexError:
                        pass
            song_titles = custom_song_titles
            song_attempts = custom_song_attempts
            song_completions = custom_song_completions
            #  end of 'if custom'

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
    app.run(host='0.0.0.0')