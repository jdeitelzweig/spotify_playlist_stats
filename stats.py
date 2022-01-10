'''
Functions to aid in obtaining stats from Spotify playlists. 

Currently working with collaborative playlists, may need to be slightly adjusted to work with single user playlists

Rather than using the Spotify API itself, this is meant to work with CSV data output by Exportify
https://github.com/watsonbox/exportify
'''

import csv
import re
from collections import Counter, namedtuple, defaultdict
from datetime import datetime
import pytz

PERSON_DICT = {
    "spotify:user:12135790462": "Josh",
    "spotify:user:shrey2000": "Shrey",
    "spotify:user:1248038176": "Jackson",
    "spotify:user:ja0tvr5t90axnr1gprruxor5f": "Dylan",
    "spotify:user:12137975671": "Alonso",
    "spotify:user:nimbus__": "Dylan",
    "spotify:user:raylizz": "Dylan",
    "spotify:user:12173409565": "Justin"
}

TIMEZONE_MAP = {
    "Alonso": "US/Mountain",
    "Jackson": "US/Eastern",
    "Josh": "US/Eastern",
    "Shrey": "US/Eastern",
    "Dylan": "US/Eastern"
}

Addition = namedtuple(
    "Addition", 
    ['name', 'artists', 'adder', 'time_added', 'time_released', 'genres', \
    'popularity', 'danceability', 'loudness', 'energy', 'explicit']
)

def _convert_column_name(column):
    return ord(column) - ord('A')


def _extract_date(date_string, timezone=pytz.utc):
    # Implies only YYYY
    if "-" not in date_string:
        return datetime(int(date_string), 1, 1, tzinfo=pytz.utc)
    # Implies only YYYY-MM
    if len(date_string.split("-")) == 2:
        info = date_string.split("-")
        return datetime(int(info[0]), int(info[1]), 1, tzinfo=pytz.utc)
    # Convert UTC ending Z to python datetime format
    if "Z" in date_string:
        date_string = date_string[:-1] + "+00:00"
    
    return datetime.fromisoformat(date_string).astimezone(timezone)


def _extract_fields(line):
    adder = PERSON_DICT[line[_convert_column_name('Q')]]
    return Addition(
        line[_convert_column_name('B')],
        re.split(r"(?<!\\), ", line[_convert_column_name('D')]),
        adder,
        _extract_date(line[_convert_column_name('R')], pytz.timezone(TIMEZONE_MAP[adder])),
        _extract_date(line[_convert_column_name('I')]),
        re.split(r"(?<!\\),", line[_convert_column_name('S')]),
        float(line[_convert_column_name('P')]),
        float(line[_convert_column_name('T')]),
        float(line[_convert_column_name('W')]),
        float(line[_convert_column_name('U')]),
        line[_convert_column_name('O')] == "true",
    )


def read_data(filename):
    '''
    Read data from an exportify CSV file and return the songs as a list of Additions
    '''
    data = []
    with open(filename, "r") as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        for line in csv_reader:
            data.append(_extract_fields(line))

    return data


def get_per_person(adds):
    '''
    Returns the exportify CSV data sorted by person (for collaborative playlists)
    '''
    per_person = defaultdict(list)
    for add in adds:
        per_person[add.adder].append(add)
    return per_person


def _flatten(t):
    return [item for sublist in t for item in sublist if item]


def get_top_artists(adds, n=20):
    '''
    Returns the top artists for a playlist
    '''
    c = Counter(_flatten([add.artists for add in adds]))
    return c.most_common(n)


def get_top_genres(adds, n=10):
    '''
    Returns the top genres for a playlist
    '''
    c = Counter(_flatten([add.genres for add in adds]))
    return c.most_common(n)


def get_metric_per_person(adds, metric_name):
    '''
    Returns the average value per person for a particular metric
    '''
    per_person = get_per_person(adds)

    metrics = []
    for person, adds in per_person.items():
        metric = sum([add._asdict()[metric_name] for add in adds]) / len(adds)
        metrics.append((person, metric))
    return metrics


def get_highest(adds, metric_name, lowest=False):
    '''
    Returns the addition that has the largest value for a particular metric
    '''
    if lowest:
        return min(adds, key=lambda x:x._asdict()[metric_name])
    return max(adds, key=lambda x:x._asdict()[metric_name])


def _pprint_tuple(tuple_list, round_second=False):
    for first, second in tuple_list:
        print(f"{first}: {round(second, 2) if round_second else second}")


def main():
    data = read_data("data/2021.csv")

    print("Popularity by Person")
    _pprint_tuple(get_metric_per_person(data, "popularity"), True)
    print()

    print("Newest song:")
    oldest = get_highest(data, "time_released")
    print(f"{oldest.name}, {oldest.time_released.date()}")
    print()

    print("Top 5 genres:")
    _pprint_tuple(get_top_genres(data, 5))
    

if __name__ == "__main__":
    main()
