# sinnoh

#### Vision
Status-quo Spotify playlist pitching software & vendors kinda suck; it's scammy, ridden with bots, and doesn't find playlists your music would actually fit well on. Sinnoh is a playlist pitching software that does 3 things
1) identifies playlists based on a criterion:
- criterion (A) is collaborative playlists with some amount of followers
- criterion (B) is independent (non editor or major label) playlists that receive submissions for music to get featured on their playlists

2) conducts a "fit analysis" to see which playlists are most similar to my music
- Spotify does ML on all it's playlists to rank it on things like acousticness, danceability, and more. These "features" are available for every song on the platform via this API endpoint: https://developer.spotify.com/documentation/web-api/reference/get-audio-features
- So, what we'll do is for a given MAS project song, this algo will take a given playlist, average every single feature across all songs, and do element-wise subtraction on the playlist's average scores to the MAS project's songs scores. The playlist must have a difference amount within a certain % threshold in order to be considered a "good fit" for my music.

3) Fraud Detection
- this algo will also have a homemade ML model that identifies whether a certain spotify playlist is botted. We'll gather a sample of botted playlists from artist.tools website, and train a supervised ML model on the data.
- We'll filter out playlists that seem botted

#### Value Propositions
- Playlists are offered highly relevant playlist pitches that their listeners would find compelling; COllaborative playlist listeners get new music
- The M.A.S. Project is offered exposure
- Michael Sawers gets to learn more python and ML

#### Tech Stack
##### Primary Language
- Python
##### Fraud Dectection
- Homemade ML fraud detection model

#### MVP
- Make an API call
- Filter the playlist to see if it's collaborative (criterion A) and has > 10 monthly listeners
- Use the bot checker here https://www.artist.tools/bot-checker (somehow, there's no API) to see if it's botted or not.
- If it's not botted, add your music to the playlist

