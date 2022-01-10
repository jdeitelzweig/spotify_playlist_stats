# Spotify Playlist Stats
This code computes some interesting statistics for Spotify playlists.

It currently works for collaborative playlists, and will need to be slightly altered for single user playlists.

Rather than using the Spotify API itself, this is meant to work with CSV data output by [Exportify](https://github.com/watsonbox/exportify).

Displaying custom ames for users and timezone adjustmentts can be specified in a JSON configuration file with the following format:
```json
{
    <spotify_user_id>: {
        "name": <display name>,
        "timezone": <pytz timezone name>
    },
    "spotify:user:12345": {
        "name": "Example User",
        "timezone": "US/Eastern"
    }
}
```

Example usage can be found in the main method of `stats.py` as well as in `visuals.ipynb`.