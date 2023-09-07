import base64
import requests
from requests import post, get
import json
from flask import Flask, request, url_for, session, redirect #will be used for redirect_uri; esssentially where our "app" is hosted
import string
import random

# These are the client ids of the app for the Spotify API
client_id = "0344808376044123b52d771e92858c83"
client_secret = "c358e0a6e90d480cacbc745fddc15cf7"
redirct_uri = "http://127.0.0.1:5000/redirected"
TOKEN_INFO = "token_info"
REFRESH_INFO = "refresh_token_info"

# These are clients and sessions with Flask
app = Flask(__name__)
app.secret_key = "oijdwaoidjwaiojdai"
app.config['SESSION_COOKIE_NAME'] = 'COOKIE'


# The starting/log-in route (logging in to spotify)
@app.route('/') 
def start_login():
    # Establishes scope and client
    scope = "playlist-modify-public playlist-modify-private" # The scope request we're making
    state = generate_random_string(16)
    auth_url = ('https://accounts.spotify.com/authorize?'f'response_type=code&client_id={client_id}&'f'scope={scope}&redirect_uri={redirct_uri}&'f'state={state}')
    
    # Redirects to handle_redirect(), which is the route/link "/redirected"
    return redirect(auth_url)


# Establishes authentication and retrieves the token for the session
@app.route('/redirected') #returns here
def handle_redirect():
    
    # For authentication, returns status (success or not)
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    auth_code = request.args.get('code')
    state = request.args.get('state')
    
    if state is None:
        return 'auth_code request failed'
    
    # If authentication retrieval is a success, retrieve the token
    else:
        url = "https://accounts.spotify.com/api/token"
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirct_uri
        }
        header = {
            "Authorization" : "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = post(url, headers=header,data=data) # Post request requires header and data, as specified in spotify
        
        # If token is received
        if response.status_code == 200:
            json_result = json.loads(response.content)
            token = json_result["access_token"]             # Gets access token from json response
            refresh_token = json_result["refresh_token"]    # Gets refresh token from json response
            session[TOKEN_INFO] = token                     # Initializing token into the variable
            session[REFRESH_INFO] = refresh_token           # Initializing token into the variable
            
            # Redirects to createPlaylist(), which is the route/link for "/createPlaylist"
            return redirect(url_for('createPlaylist', _external=True))
        
    return "token retrieve fails"


# Creates the playlist
@app.route('/createPlaylist') 
def createPlaylist():
    token = get_token()                 # Retrieves the (refreshed/)token
    header = get_auth_header(token)     # Retrieves the authentication header
    
    # Grab's the user information to create the playlist under that user
    user_id = getUser()
    data = {"name": "Your Mixed Playlist!!", "description": "~~enjoy your combined playlists <3~~", "public": True}
 
    # Create the playlist
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    response = post(url, headers=header, json=data)
    json_result = json.loads(response.content)
    
    # Grab the playlist ID (to add tracks) and URL (for redirection)
    playlist_id = json_result["id"]
    playlist_url = json_result["external_urls"]["spotify"]
    
    # Add the tracks into the playlist
    response_code = addTracks(playlist_id)
    
    # If adding tracks was a success, redirect to the playlist URL
    if response_code == 201:
        return redirect(playlist_url)

    return str(response_code)
    
    
# Add tracks into the playlist
def addTracks(playlist_id):
    token = get_token()                 # Retrieves the (refreshed/)token
    header = get_auth_header(token)     # Retrieves the authentication header
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"  

    # Grab the tracks
    tracks_uri = getTracks()
    
    # Adding the tracks into the playlist
    data = {"uris": tracks_uri,"position": 0}
    response = post(url, headers=header, json=data)
    
    return response.status_code
    
    
# Grab the tracks    
def getTracks():
    token = get_token()                 # Retrieves the (refreshed/)token
    header = get_auth_header(token)     # Retrieves the authentication header
    
    # Search query method for the chosen artists
    # Max limit of artist is three!
    ### Find a way to input these artists via front-end web
    artist_ids = search_artist(header, artist_names=["BBNO&", "21 Savage"]) 
    tracks_uri = []
    tracks_id = []
    
    # Retrieves the top tracks per chosen artist
    ### Find a way to retrieve tracks from discography/radio
    for artist_id in artist_ids:
        url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=US"
        result = get(url, headers=header)
        json_result = json.loads(result.content)["tracks"]
        
        # Max tracks added PER artist is 5
        count_added_track = 0
        
        for track in json_result:
            
            # If it's the 5th track, stop
            if count_added_track >= 5:
                break
            
            tracks_uri.append(track["uri"])     # Retrieve the uri (link) for the track
            tracks_id.append(track["id"])       # Retrieve the id (used as seeds) for the recommendation endpoint
            
            count_added_track +=1
    
    # Grab the recommendation tracks based on artist and tracks; style-based recommendations
    recommended_tracks_uri = getRecommendedTracks(tracks_id[:2], artist_ids) 
    tracks_uri.extend(recommended_tracks_uri)
    
    # Shuffle the tracks
    random.shuffle(tracks_uri)

    return tracks_uri


# Grab the recommended tracks
def getRecommendedTracks(seed_tracks,seed_artists):
    token = get_token() 
    header = get_auth_header(token)
    
    # Convert seed tracks and seed artists into URL-encoded strings
    seed_tracks_str = ",".join(seed_tracks)
    seed_artists_str = ",".join(seed_artists)
    
    # It only takes five seeds (2 tracks & 2-3 artists)
    url = f"https://api.spotify.com/v1/recommendations?limit=5&market=US&seed_artists={seed_artists_str}&seed_tracks={seed_tracks_str}"
    
    recommended_tracks_uri = []
    result = get(url, headers=header)
    json_result = json.loads(result.content)["tracks"]
    
    # Retrieve the uri (link) for the track
    for track in json_result:
        reco_track_uri = track['uri']
        recommended_tracks_uri.append(reco_track_uri)
        
    return recommended_tracks_uri


# Grab the ID of the user; to create a playlist under that user
def getUser():
    token = get_token() 
    header = get_auth_header(token)
    url = "https://api.spotify.com/v1/me"
    
    result = get(url, headers=header)
    json_result = json.loads(result.content)
    user_id = json_result["id"]
    return user_id
 

# Query the chosen artists and retrieve their IDs
def search_artist(header, artist_names):
    artist_ids = []
    url = "https://api.spotify.com/v1/search"
    
    # Search artist from chosen and retrieve ID
    for artist_name in artist_names:
        query = f"q={artist_name}&type=artist&limit=1"
        query_url = url + "?" + query
    
        result = get(query_url, headers=header)
        json_result = json.loads(result.content)["artists"]["items"]
        artist_ids.append(json_result[0]["id"])
    
    return artist_ids


# Authenthication header, used for ALL requests to the spotify web api
def get_auth_header(token):
    return {"Authorization": "Bearer " + token}


# Retrieve the session token
def get_token():
    token = session.get(TOKEN_INFO, None)
    if token: # If token is all good
        return token
    
    # Refresh the token if it isn't good
    else:
        refreshed_token = refresh_token()
        if refreshed_token: # Retrieval is a success
            return refreshed_token
        
    return None
        
  
# Refresh the token      
def refresh_token():
    refresh_token = session.get(REFRESH_INFO, None)
    
    # Ask for a new token
    if refresh_token:
        auth_string = client_id + ":" + client_secret
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
        url = "https://accounts.spotify.com/api/token"
        
        data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
        }
        
        header = {
            "Authorization" : "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = requests.post(url, headers=header, json=data)
        
        # If request is a success
        if response.status_code == 200:
            json_result = json.loads(response.content)
            new_access_token = json_result["access_token"]
            session[TOKEN_INFO] = new_access_token              # Saving refreshed token into actual token variable
            return new_access_token
        else:
            return None
        
    return None
        

# Created for unique something lmao i forgor         
def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))
    
    
app.run()

