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

app = Flask(__name__)
app.secret_key = "oijdwaoidjwaiojdai"
app.config['SESSION_COOKIE_NAME'] = 'COOKIE'

@app.route('/') 
def start_login():
    scope = "playlist-modify-public playlist-modify-private"
    state = generate_random_string(16)
    auth_url = ('https://accounts.spotify.com/authorize?'f'response_type=code&client_id={client_id}&'f'scope={scope}&redirect_uri={redirct_uri}&'f'state={state}')
    
    return redirect(auth_url)


@app.route('/redirected') #returns here
def handle_redirect():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    auth_code = request.args.get('code')
    state = request.args.get('state')
    
    if state is None:
        return 'auth_code request failed'
    
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
        
        response = post(url, headers=header,data=data)
        
        if response.status_code == 200:
            json_result = json.loads(response.content)
            token = json_result["access_token"]
            refresh_token = json_result["refresh_token"]
            session[TOKEN_INFO] = token
            session[REFRESH_INFO] = refresh_token
            return redirect(url_for('createPlaylist', _external=True))
        
    return "token retrieve fails"



@app.route('/createPlaylist') 
def createPlaylist():
    token = get_token() #checks if expired or nah
    header = get_auth_header(token)
    
    user_id = getUser()
    data = {"name": "Your Mixed Playlist!!", "description": "enjoy your combined playlists <3", "public": True}
 
    # creating the playlist
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    response = post(url, headers=header, json=data)
    json_result = json.loads(response.content)
    playlist_id = json_result["id"]
    playlist_url = json_result["external_urls"]["spotify"]
    
    # adding the tracks to the playlist
    response_code = addTracks(playlist_id)
    
    if response_code == 201:
        return redirect(playlist_url)

    return str(response_code)
    
    

def addTracks(playlist_id):
    token = get_token() #checks if expired or nah
    header = get_auth_header(token)
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    tracks_uri = getTracks()
    data = {"uris": tracks_uri,"position": 0}
    response = post(url, headers=header, json=data)
    
    return response.status_code
    
    
def getTracks():
    token = get_token() #checks if expired or nah
    header = get_auth_header(token)
    
    #limit it to 3 max
    artist_ids = search_artist(header, artist_names=["Olivia Rodrigo", "Taylor Swift"]) #this has to be a hard limit of 3 due to the seeds
    tracks_uri = []
    tracks_id = []
    
    for artist_id in artist_ids:
        url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=US"
        result = get(url, headers=header)
        json_result = json.loads(result.content)["tracks"]
        
        count_added_track = 0
        for track in json_result:
            
            if count_added_track >= 5:
                break
            
            tracks_uri.append(track["uri"])
            tracks_id.append(track["id"])
            
            count_added_track +=1
    
    random.shuffle(tracks_id)
    #SEED TRACKS ARE JUST IDs
    recommended_tracks_uri = getRecommendedTracks(tracks_id[:2], artist_ids) 
    
    tracks_uri.extend(recommended_tracks_uri)
    # merge user recommendations into tracks
    random.shuffle(tracks_uri)
    
    print("total tracks_uris: ", tracks_uri)
    return tracks_uri

def getRecommendedTracks(seed_tracks,seed_artists):
    token = get_token() #checks if expired or nah
    header = get_auth_header(token)
    
    # Convert seed tracks and seed artists into URL-encoded strings
    seed_tracks_str = "%".join(seed_tracks)
    seed_artists_str = "%".join(seed_artists)
    
    url = f"https://api.spotify.com/v1/recommendations?seed_artists={seed_artists_str}&seed_tracks={seed_tracks_str}"
    recommended_tracks_uri = []
    
    result = get(url, headers=header)
    json_result = json.loads(result.content)
    
    #IT ONLY TAKES 5 SEEDS IN TOTAL!!!!!
    print("this is for reco| seed tracks: ", seed_tracks_str, "| seed artists: ", seed_artists_str, "| result: ", json_result)
    
    tracks_data = json_result["tracks"]
    
    for track in tracks_data:
       reco_track_uri = track[0]['uri']
       recommended_tracks_uri.append(reco_track_uri)
        
    return recommended_tracks_uri


def getUser():
    token = get_token() #checks if expired or nah
    header = get_auth_header(token)
    url = "https://api.spotify.com/v1/me"
    
    result = get(url, headers=header)
    json_result = json.loads(result.content)
    user_id = json_result["id"]
    return user_id
    

#get five recommendations --> add it to the playlist
# need seed artists (to capture their style); make sure genres aint seen yet) & seed tracks (random)

def search_artist(header, artist_names):
    artist_ids = []
    url = "https://api.spotify.com/v1/search"
    
    for artist_name in artist_names:
        query = f"q={artist_name}&type=artist&limit=1"
        query_url = url + "?" + query
    
        result = get(query_url, headers=header)
        json_result = json.loads(result.content)["artists"]["items"]
        artist_ids.append(json_result[0]["id"])
    
    return artist_ids


def get_auth_header(token):
    return {"Authorization": "Bearer " + token}


def get_token():
    token = session.get(TOKEN_INFO, None)
    if token:
        return token
    else:
        refreshed_token = refresh_token()
        if refreshed_token:
            return refreshed_token
    return None
        #get token information for artist search and playlist creation
        #create a refresh token
        
        
def refresh_token():
    refresh_token = session.get(REFRESH_INFO, None)
    
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
        
        if response.status_code == 200:
            json_result = json.loads(response.content)
            new_access_token = json_result["access_token"]
            session[TOKEN_INFO] = new_access_token
            return new_access_token
        else:
            return None
    return None
        
        
def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))
    
    
app.run()

