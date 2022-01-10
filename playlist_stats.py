'''
Functions to aid in obtaining stats from Spotify playlists. 

Rather than using the Spotify API itself, this is meant to work with CSV data output by Exportify
https://github.com/watsonbox/exportify
'''

import asyncio
from collections import Counter, namedtuple, defaultdict
import csv
from datetime import datetime
import json
import re

import cv2
import httpx
import numpy as np
import pytz

Addition = namedtuple(
    "Addition", 
    ['name', 'artists', 'adder', 'time_added', 'time_released', 'genres', \
    'popularity', 'danceability', 'loudness', 'energy', 'explicit', 'album_cover_url']
)

STANDARD_SPOTIFY_IMAGE_SIZE = (640, 640)

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


def _get_default_user_config(sp_id):
    return {
        "name": sp_id,
        "timezone": "US/Eastern"
    }


def load_config(filename):
    with open(filename, "r") as f:
        return json.load(f)


def _extract_fields(line, config={}):
    adder = config.get(line[_convert_column_name('Q')], _get_default_user_config(line[_convert_column_name('Q')]))
    return Addition(
        line[_convert_column_name('B')],
        re.split(r"(?<!\\), ", line[_convert_column_name('D')]),
        adder["name"],
        _extract_date(line[_convert_column_name('R')], pytz.timezone(adder["timezone"])),
        _extract_date(line[_convert_column_name('I')]),
        re.split(r"(?<!\\),", line[_convert_column_name('S')]),
        float(line[_convert_column_name('P')]),
        float(line[_convert_column_name('T')]),
        float(line[_convert_column_name('W')]),
        float(line[_convert_column_name('U')]),
        line[_convert_column_name('O')] == "true",
        line[_convert_column_name('J')],
    )


def read_data(filename, config={}):
    '''
    Read data from an exportify CSV file and return the songs as a list of Additions
    '''
    data = []
    with open(filename, "r") as f:
        csv_reader = csv.reader(f)
        next(csv_reader)
        for line in csv_reader:
            data.append(_extract_fields(line, config=config))
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


def get_top_artists(adds, n=20, per_person=False):
    '''
    Returns the top artists for a playlist
    '''
    if per_person:
        most_common = []
        for person, person_adds in get_per_person(adds).items():
            c = Counter(_flatten([add.artists for add in person_adds]))
            most_common.append((person, c.most_common(1)[0]))
        return most_common
    c = Counter(_flatten([add.artists for add in adds]))
    return c.most_common(n)


def get_top_genres(adds, n=10, per_person=False):
    '''
    Returns the top genres for a playlist
    '''
    if per_person:
        most_common = []
        for person, person_adds in get_per_person(adds).items():
            c = Counter(_flatten([add.genres for add in person_adds]))
            most_common.append((person, c.most_common(1)[0]))
        return most_common
    c = Counter(_flatten([add.genres for add in adds]))
    return c.most_common(n)


def get_metric(adds, metric_name, per_person=False):
    '''
    Returns the average value per person for a particular metric
    '''
    if per_person:
        per_person = get_per_person(adds)
        metrics = []
        for person, person_adds in per_person.items():
            metric = sum([add._asdict()[metric_name] for add in person_adds]) / len(person_adds)
            metrics.append((person, metric))
        return metrics

    return sum([add._asdict()[metric_name] for add in adds]) / len(adds)


def get_highest(adds, metric_name, lowest=False):
    '''
    Returns the addition that has the largest value for a particular metric
    '''
    if lowest:
        return min(adds, key=lambda x:x._asdict()[metric_name])
    return max(adds, key=lambda x:x._asdict()[metric_name])


def get_release_hist(adds):
    '''
    Returns a histogram of the release years of songs added by a particular person
    Normalizes the histogram per person
    '''
    per_person = get_per_person(adds)
    years_per_person = []
    for person_adds in per_person.values():
        person_years = [add.time_released.year for add in person_adds]
        years_per_person.append(person_years)

    flat_years = _flatten(years_per_person)
    year_bins = list(range(min(flat_years), max(flat_years)+1))

    add_years = np.zeros((len(per_person), len(year_bins)))

    for i, person_years in enumerate(years_per_person):
        hist, _ = np.histogram(person_years, bins=year_bins + [year_bins[-1] + 1])
        add_years[i] = hist / hist.sum()

    return add_years, year_bins


def get_time_added_hist(adds):
    '''
    Returns a histogram of times each song was added to the playlist
    Normalizes the histogram per person
    '''
    per_person = get_per_person(adds)

    add_times = np.zeros((len(per_person), 24))
    for i, person_adds in enumerate(per_person.values()):
        hourly_adds = [0] * 24
        for add in person_adds:
            hourly_adds[add.time_added.hour % 24] += 1
        add_times[i] = np.array(hourly_adds) / sum(hourly_adds)

    return add_times


async def _get_image_from_url(client, url):
    req = client.get(url)
    nparr = np.frombuffer((await req).content, np.uint8)
    img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img_np.shape[0:2] != STANDARD_SPOTIFY_IMAGE_SIZE:
        img_np = cv2.resize(img_np, STANDARD_SPOTIFY_IMAGE_SIZE)
    return img_np


async def _get_all_images(urls):
    async with httpx.AsyncClient() as client:
        tasks = (_get_image_from_url(client, url) for url in urls)
        reqs = await asyncio.gather(*tasks)
    return np.array(reqs)


def get_average_album_cover(adds):
    '''
    Computes a pixelwise average across all album covers in the playlist
    '''
    urls = [add.album_cover_url for add in adds]
    imgs = asyncio.run(_get_all_images(urls))
    return np.mean(imgs, axis=0) / 255.0