import base64
from requests import post, get
import json

client_id = "0344808376044123b52d771e92858c83"
client_secret = "c358e0a6e90d480cacbc745fddc15cf7"

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    url = 'https://accounts.spotify.com/api/token' #endpoint
    headers = {
        "Authorization": "Basic " +auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url,headers=headers,data=data )
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}


def search_artist(token, artist_names):
    artist_ids = []
    url = "https://api.spotify.com/v1/search"
    header = get_auth_header(token)
    
    for artist_name in artist_names:
        query = f"q={artist_name}&type=artist&limit=1"
        query_url = url + "?" + query
    
        result = get(query_url, headers=header)
        json_result = json.loads(result.content)["artists"]["items"]
        artist_ids.append(json_result[0]["id"])
    
    return artist_ids

def get_artist_top_tracks(token, artist_ids):
    tracks = []
    header = get_auth_header(token)

    for artist_id in artist_ids:
        url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=US"
        result = get(url, headers=header)
        json_result = json.loads(result.content)["tracks"]
        
        for track in json_result:
            tracks.append(track["id"])
        

def main():
    token = get_token()
    artist_ids = search_artist(token, ["Lola Amour", "Casey Lowry"])
    get_artist_top_tracks(token, artist_ids)

main()
