
        
def getRecommendedTracks(seed_tracks,seed_artists):
    token = get_token() #checks if expired or nah
    header = get_auth_header(token)
    url = f"https://api.spotify.com/v1/recommendations?limit=5&seed_artists={seed_tracks}&seed_artists={seed_artists}"
    
    result = get(url, headers=header)
    json_result = json.loads(result.content)
    
    tracks_data = json_result["tracks"]
    
    print(tracks_data)
    
    
getRecommendedTracks("4NHQUGzhtTLFvgF5SZesLK", "0c6xIDDpzE81m2q797ordA")