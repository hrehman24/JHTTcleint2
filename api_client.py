import requests


class BeatifyClient:

    # Artist resource request methods via requests.Session()
    def __init__(self, base_url=None, aux_url=None, timeout=10):
        self.base_url = (base_url or "http://130.162.240.153:5000").rstrip("/")
        self.aux_url = (aux_url or "http://localhost:7000").rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _api(self, path):
        return f"{self.base_url}/Beatify/api/v1{path}"

    def _aux(self, path):
        return f"{self.aux_url}{path}"

    @staticmethod
    def _json_or_empty(response):
        try:
            return response.json()
        except ValueError:
            return {}

    def get_artists(self):
        response = self.session.get(self._api("/artists"), timeout=self.timeout)
        json_response = self._json_or_empty(response)
        return json_response
    
    def get_artist(self, id):
        response = self.session.get(self._api(f"/artists/{id}"), timeout=self.timeout)
        json_response = self._json_or_empty(response)
        return json_response
    
    def create_artist(self, name):
        data = {
            "name": name
        }
        response = self.session.post(self._api("/artists"), json=data, timeout=self.timeout)
        return response
    
    def update_artist(self, id, name):
        data = {
            "name": name
        }
        response = self.session.put(self._api(f"/artists/{id}"), json=data, timeout=self.timeout)
        return response
    
    def delete_artist(self, id):
        response = self.session.delete(self._api(f"/artists/{id}"), timeout=self.timeout)
        return response
    
    # Album resource request methods via requests.Session()

    def get_albums(self):
        response = self.session.get(self._api("/albums"), timeout=self.timeout)
        json_response = self._json_or_empty(response)
        return json_response
    
    def get_album(self, id):
        response = self.session.get(self._api(f"/albums/{id}"), timeout=self.timeout)
        json_response = self._json_or_empty(response)
        return json_response
    
    def create_album(self, name, artist_id):
        data = {
            "name": name,
            "artist_id": artist_id
        }
        response = self.session.post(self._api("/albums"), json=data, timeout=self.timeout)
        return response
    
    def update_album(self, id, name, artist_id):
        data = {
            "name": name,
            "artist_id": artist_id
        }
        response = self.session.put(self._api(f"/albums/{id}"), json=data, timeout=self.timeout)
        return response
    
    def delete_album(self, id):
        response = self.session.delete(self._api(f"/albums/{id}"), timeout=self.timeout)
        return response
    
    # Track resource request methods via requests.Session()

    def get_tracks(self):
        response = self.session.get(self._api("/tracks"), timeout=self.timeout)
        json_response = self._json_or_empty(response)
        return json_response
    
    def get_track(self, id):
        response = self.session.get(self._api(f"/tracks/{id}"), timeout=self.timeout)
        json_response = self._json_or_empty(response)
        return json_response
    
    def create_track(self, name, length, album_id):
        data = {
            "name": name,
            "length": length,
            "album_id": album_id
        }
        response = self.session.post(self._api("/tracks"), json=data, timeout=self.timeout)
        return response
    
    def update_track(self, id, name, length, album_id):
        data = {
            "name": name,
            "length": length,
            "album_id": album_id
        }
        response = self.session.put(self._api(f"/tracks/{id}"), json=data, timeout=self.timeout)
        return response    
    
    def delete_track(self, id):
        response = self.session.delete(self._api(f"/tracks/{id}"), timeout=self.timeout)
        return response    
    
    # Playlist resource request methods via requests.Session()

    def get_playlists(self):
        response = self.session.get(self._api("/playlists"), timeout=self.timeout)
        json_response = self._json_or_empty(response)
        return json_response
    
    def get_playlist(self, id):
        response = self.session.get(self._api(f"/playlists/{id}"), timeout=self.timeout)
        json_response = self._json_or_empty(response)
        return json_response
    
    def create_playlist(self, name, description):
        data = {
            "name": name,
            "description": description
        }
        response = self.session.post(self._api("/playlists"), json=data, timeout=self.timeout)
        return response
    
    def update_playlist(self, id, name, description):
        data = {
            "name": name,
            "description": description
        }
        response = self.session.put(self._api(f"/playlists/{id}"), json=data, timeout=self.timeout)
        return response    
    
    def delete_playlist(self, id):
        response = self.session.delete(self._api(f"/playlists/{id}"), timeout=self.timeout)
        return response 
    
    def add_track_to_playlist(self, playlist_id, track_id):
        data = {
            "track_id": track_id
        }
        response = self.session.put(self._api(f"/playlists/{playlist_id}"), json=data, timeout=self.timeout)
        return response
    
    def add_user_to_playlist(self, playlist_id, user_id):
        data = {
            "user_id": user_id
        }
        response = self.session.put(self._api(f"/playlists/{playlist_id}"), json=data, timeout=self.timeout)
        return response
    
    # User resource request methods via requests.Session()

    def get_users(self):
        response = self.session.get(self._api("/users"), timeout=self.timeout)
        json_response = self._json_or_empty(response)
        return json_response
    
    def get_user(self, id): 
        response = self.session.get(self._api(f"/users/{id}"), timeout=self.timeout)
        json_response = self._json_or_empty(response)
        return json_response
    
    def create_user(self, name):
        data = {
            "name": name
        }
        response = self.session.post(self._api("/users"), json=data, timeout=self.timeout)
        return response    
    
    def update_user(self, id, name):
        data = {
            "name": name
        }
        response = self.session.put(self._api(f"/users/{id}"), json=data, timeout=self.timeout)
        return response
    
    def delete_user(self, id):
        response = self.session.delete(self._api(f"/users/{id}"), timeout=self.timeout)
        return response

    # Auxiliary service request methods

    def get_aux_root(self):
        return self.session.get(self._aux("/"), timeout=self.timeout)

    def get_analytics_summary(self):
        return self.session.get(self._aux("/analytics/summary"), timeout=self.timeout)

    def get_top_artists(self):
        return self.session.get(self._aux("/analytics/top-artists"), timeout=self.timeout)

    def get_user_recommendations(self, user_id):
        return self.session.get(self._aux(f"/recommendations/user/{user_id}"), timeout=self.timeout)
    
 
    

