import argparse
import os
import cv2
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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


def generate_cumulative_graph(output_path, adds, per_person=False):
    fig, ax = plt.subplots()
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Number of Songs Added")
    ax.set_title("Songs Added Over Time")

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())

    if per_person:
        for person, person_adds in get_per_person(adds).items():
            x = [add.time_added.date() for add in person_adds]
            y = range(len(person_adds))
            ax.plot(x, y, label=person)
        ax.legend(loc='upper left')
    else:
        x = [add.time_added.date() for add in adds]
        y = range(len(adds))
        ax.plot(x, y)

    fig.savefig(output_path)


def generate_pie_chart(output_path, adds):
    per_person = get_per_person(adds)
    fig, ax = plt.subplots()
    ax.pie([len(person_adds) for person_adds in per_person.values()], labels=list(per_person), autopct='%1.1f%%')
    ax.axis('equal')
    ax.set_title("Percent Added By Users")
    fig.savefig(output_path)


def generate_time_added_heatmap(output_path, adds, collaborative=False):
    per_person = get_per_person(adds)
    add_times = get_time_added_hist(adds)
    hours = [f"{i}:00-{i}:59" for i in range(24)]
    people = list(per_person)

    fig, ax = plt.subplots()
    im = ax.imshow(add_times, cmap="plasma", aspect=2)

    ax.set_xticks(np.arange(len(hours)), labels=hours)
    ax.set_yticks(np.arange(len(people)), labels=people)
    if not collaborative:
        ax.get_yaxis().set_visible(False)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
            rotation_mode="anchor")

    ax.set_title("Songs Added Per Hour")
    fig.tight_layout()
    fig.savefig(output_path)


def generate_date_released_heatmap(output_path, adds, collaborative=False):
    per_person = get_per_person(adds)
    add_years, years = get_release_hist(adds)
    people = list(per_person)

    fig, ax = plt.subplots()
    im = ax.imshow(add_years, cmap="plasma", aspect=4)

    ax.set_xticks(np.arange(len(years)), labels=[year if year % 10 == 0 else "" for year in years])
    ax.set_yticks(np.arange(len(people)), labels=people)
    if not collaborative:
        ax.get_yaxis().set_visible(False)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
            rotation_mode="anchor")

    ax.set_title("Release Years of Songs Added")
    fig.tight_layout()
    fig.savefig(output_path)


def main():
    '''
    Generates a report of statistics and generates figures with additional information
    '''
    # Read command line args
    parser = argparse.ArgumentParser(description="Obtains stats for a Spotify playlist")
    parser.add_argument("playlist_data", help="The csv file containing data from Exportify")
    parser.add_argument("output_dir", help="The name of a directory to output data to")
    parser.add_argument("--config_file", help="The user configuration file described in README.md")
    parser.add_argument('--average_image', action='store_true', help="Set this flag to generate the average album cover (slow)")
    args = parser.parse_args()

    # Load data
    config = load_config(args.config_file)
    data = read_data(args.playlist_data, config)

    # Determine if playlist is collaborative
    collaborative = len(get_per_person(data)) > 1

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Generate report
    generate_report(os.path.join(args.output_dir, "stats.txt"), data, collaborative=collaborative)

    # Generate figures
    generate_cumulative_graph(os.path.join(args.output_dir, "cumulative.png"), data)

    if collaborative:
        generate_cumulative_graph(os.path.join(args.output_dir, "cumulative_person.png"), data, per_person=True)
        generate_pie_chart(os.path.join(args.output_dir, "pie.png"), data)

    generate_time_added_heatmap(os.path.join(args.output_dir, "times_added.png"), data, collaborative=collaborative)
    generate_date_released_heatmap(os.path.join(args.output_dir, "dates_released.png"), data, collaborative=collaborative)
    
    # Generate average image
    if args.average_image:
        cv2.imwrite(os.path.join(args.output_dir, "average_image.png"), get_average_album_cover(data))
    

if __name__ == "__main__":
    main()
