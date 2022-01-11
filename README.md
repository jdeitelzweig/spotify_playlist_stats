# Spotify Playlist Stats
This code computes some interesting statistics for Spotify playlists.

Rather than using the Spotify API itself, this is meant to work with CSV data output by [Exportify](https://github.com/watsonbox/exportify).

## Usage

To generate a full set of statistics and figures for your playlist csv, run
`python generate_stats.py <path_to_data> <output_path>`

See `example/` for what this script outputs.

To display custom names and to use different timezones, create a JSON configuration file with the following format:
```json
{
    "<spotify_user_id>": {
        "name": "<display name>",
        "timezone": "<pytz timezone name>"
    },
    "spotify:user:12345": {
        "name": "Example User",
        "timezone": "US/Eastern"
    }
}
```
This can then be used by specifying the `--config_file` argument.

This script also allows you to compute the average album cover for a playlist. Since this operation can be time consuming for large playlists, it is disabled by default. To output the average image, set the `--average_image` flag.