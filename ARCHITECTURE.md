# Architecture

Lit up is a tool to make playlists

## Uploading Songs

- POST `/songs/{id}` to initiate song processing
  - This will publish to `song_processing_events` topic
  - A queue listener will pick up this new song processing event & kick off the process
    - Rip song audio from YT
    - Get Album artwork
- GET `/songs/{id}/processing-status` will return the songs processing status

## Making Playlist

- Songs must be present GET `/songs`
- Choose songs to add to the playlist
- Add other metadata to playlist and POST `/playlists`
- When playlist is deployed via POST `/playlists/{id}/deployments`
  - Publish to the `playlist_events` topic
  - Generate Favicon
  - Generate concatenated playlist
  - Generate appConfig
  - Call TBD deployment method
    - git pull repo
    - build web project
    - use aws cli to upload web files to s3
    - will need to update the active versions in cloudfront request handler
- Get deployment status GET `/playlist/{playlistId}/deployments/{deploymentId}`
