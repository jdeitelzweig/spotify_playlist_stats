import argparse
import os
import cv2

from playlist_stats import *

def _pprint_tuple(fp, tuple_list, round_second=False):
    for first, second in tuple_list:
        fp.write(f"{first}: {round(second, 2) if round_second else second}\n")


def _write_header(fp, text):
    fp.write("#"*30 + "\n")
    fp.write(f"{text}\n")
    fp.write("#"*30 + "\n")


def generate_report(output_path, adds, top_k=5, collaborative=False):
    '''
    Writes a file to output_path detailing statistics about the playlist
    '''
    metrics = ["popularity", "loudness", "energy", "danceability"]

    with open(output_path, "w+") as f:
        _write_header(f, "Playlist Statistics")

        # Top artists
        f.write(f"Top {top_k} artists:\n")
        _pprint_tuple(f, get_top_artists(adds, n=top_k))
        f.write("\n")

        # Top genres
        f.write(f"Top {top_k} genres:\n")
        _pprint_tuple(f, get_top_genres(adds, n=top_k))
        f.write("\n")

        # Average metric
        for metric in metrics + ["explicit"]:
            f.write(f"{metric}: {round(get_metric(adds, metric), 2)}\n")
        f.write("\n")

        if collaborative:
            _write_header(f, "Statistics Per Person")

            # Top artist per person
            f.write("Top artist:\n")
            _pprint_tuple(f, get_top_artists(adds, per_person=True))
            f.write("\n")

            # Top genre per person
            f.write("Top genre:\n")
            _pprint_tuple(f, get_top_genres(adds, per_person=True))
            f.write("\n")

            # Average metric per person
            for metric in metrics + ["explicit"]:
                f.write(f"{metric}:\n")
                _pprint_tuple(f, get_metric(adds, metric, per_person=True), round_second=True)
                f.write("\n")

        # Individual song stats
        _write_header(f, "Song Statistics")
        for metric in metrics + ["time_released"]:
            f.write(f"Highest {metric}: ")
            highest = get_highest(adds, metric)
            f.write(f"{highest.name}, {highest._asdict()[metric]}") 
            if collaborative:
                f.write(f", {highest.adder}")
            f.write("\n")

            f.write(f"Lowest {metric}: ")
            lowest = get_highest(adds, metric, lowest=True)
            f.write(f"{lowest.name}, {lowest._asdict()[metric]}") 
            if collaborative:
                f.write(f", {lowest.adder}")
            f.write("\n")
            f.write("\n")


def main():
    '''
    Generates a report of statistics and generates figures with additional information
    '''
    # argparse data, config, output dir

    # load data
    config = load_config("config.json")
    data = read_data("data/2021.csv", config)

    # determine if collaborative
    collaborative = len(get_per_person(data)) > 1

    # create output directory


    # generate report
    generate_report("results/test.txt", data, collaborative=collaborative)

    # generate figures
    # generate_songs_added_graph()
    # generate_time_added_heatmap()
    # generate_date_released_heatmap()
    
    # # generate average image
    # cv2.imwrite()

    

if __name__ == "__main__":
    main()
