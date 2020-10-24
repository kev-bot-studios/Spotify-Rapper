# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os
import site
import matplotlib.pyplot as plt
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

site.addsitedir(os.path.relpath('..//..//DontUpload'))
import spotify_creds as sc


class Artist:
    """
    Class for obtaining information about an artist
    
    Attributes:
        artist (str): Name of artist
        artist_uri (str): Spotify artist uri code
        
    """

    
    def __init__(self, artist, uri):
        
        self.artist = artist
        self.artist_uri = uri
        self.audio_feats_to_query = ['danceability', 'energy', 'key', 'loudness',
                                        'mode', 'speechiness', 'acousticness', 
                                        'instrumentalness', 'liveness', 'valence',
                                        'tempo']
        self.feat_num = len(self.audio_feats_to_query)
        self.init_client()
        self.get_artist_image()
        self.get_album_details()
        self.get_song_details()
        
    def init_client(self):
        """
        Initialize connection to spotify API

        """
        
        creds = sc.load_creds()
        client_id = creds['client_id']
        client_secret = creds['client_secret']
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id,
                                                      client_secret=client_secret)
        self.sp = spotipy.Spotify(client_credentials_manager=
                                  client_credentials_manager)
    
    def get_artist_image(self):
        """
        Get image of artist
        """
        
        spot_name = self.sp.artist(self.artist_uri)['name']
        results = self.sp.search(q='artist:' + spot_name, type='artist')
        items = results['artists']['items']
        url = items[0]['images'][2]['url'] #0 widest, 2 narrowest
        self.image_url = url
        
    
    def get_album_details(self):
        """
        Get album level details about an artist

        """
        
        # get list of artist albums
        query = self.sp.artist_albums(self.artist_uri, album_type = 'album')
        albums = query['items']
        while query['next']:
            query = self.sp.next(query)
            albums.extend(query['items'])
        
        # extract relevant information from artist album dictionary
        album_summary = pd.DataFrame(columns = ['date', 'num_tracks','album_uri'])        
        for album in albums:
        
            name = album['name']
            album_summary.loc[name, 'date'] = album['release_date']
            album_summary.loc[name, 'num_tracks'] = album['total_tracks']
            album_summary.loc[name, 'album_uri'] = album['uri']    
        
        self.album_summary = album_summary
    
    
    def get_song_details(self):
        """
        Get song level details about an artist

        """
        
        album_track_summary = {}
        for ii in range(len(self.album_summary)):   
            
            # get individual tracks associated with artist's album
            query = self.sp.album_tracks(self.album_summary.album_uri[ii])
            tracks = query['items']
            while query['next']:
                query = self.sp.next(query)
                tracks.extend(query['items'])
            
            album = self.album_summary.index[ii]
            album_df = pd.DataFrame(columns = ['duration', 'track_uri'] + 
                                    self.audio_feats_to_query)
            
            # save track level general characteristics
            for jj in range(len(tracks)):
                track_name = tracks[jj]['name']
                album_df.loc[track_name, 'duration'] = tracks[jj]['duration_ms'] / 1000
                album_df.loc[track_name, 'track_uri'] = tracks[jj]['uri']
            
            
            # get audio features for all tracks on albums, add them to df
            audio_feats = self.sp.audio_features(album_df.track_uri.tolist())
            for kk in range(len(tracks)):
                track_name = tracks[kk]['name']

                for ll in range(len(self.audio_feats_to_query)):
                    
                    feat = self.audio_feats_to_query[ll]
                    album_df.loc[track_name, feat] = audio_feats[kk][feat]
                    
            album_track_summary[album] = album_df
            
    
        self.album_track_summary = album_track_summary
        
    
    def get_artist_data(self):
        """
        Get discrete data related to an artists avergae level of audio featues,
            their inner album volatility for these features, total albums, 
            tracks per album, and average time between releasing albums
            
        Returns:
            artist_summary_data (pd.Series): Series with artist level 
                discrete data

        """
                
        # average time between album releases
        dates = (pd.DatetimeIndex(self.album_summary.date)
                         .sort_values(ascending = False))
        time_between_releases = [dates[ii] - dates[ii+1] for ii 
                                 in range(len(dates) - 1)]
        av_release_date = np.mean(time_between_releases)

        # total albums released, tracks per album
        albums = self.album_summary.shape[0]
        track_per_album = self.album_summary.num_tracks.mean()
                
        
        # aggregate track data to artist album
        artist_feats = pd.DataFrame(index = self.audio_feats_to_query,
                                   columns = ['mean', 'vol'])
        
        for ii in range(self.feat_num): 
            
            feat_mean = []
            feat_vol = []
            
            for jj in range(len(self.album_summary.index.tolist())): 

                album_name = list(self.album_track_summary.keys())[jj]
                feat = self.audio_feats_to_query[ii]
                album_detail = self.album_track_summary[album_name]
                feat_vals = album_detail[feat].values
                feat_mean.append(feat_vals.mean())
                feat_vol.append(feat_vals.std()) 
                
            artist_feats.loc[feat, 'mean'] = np.mean(feat_mean)
            artist_feats.loc[feat, 'vol'] = np.mean(feat_vol)
        
        
        # save artist level discrete data
        artist_summary_data = pd.Series(dtype = 'object')
        artist_summary_data.loc['av_time_btwn_release'] = (av_release_date).days
        artist_summary_data.loc['total_albums'] = albums
        artist_summary_data.loc['track_per_album'] = track_per_album
        artist_summary_data.loc['image_url'] = self.image_url
        
        for feat in artist_feats.index:
            
            artist_summary_data.loc[feat + ' mean'] = artist_feats.loc[feat, 'mean']
            artist_summary_data.loc[feat + ' vol'] = artist_feats.loc[feat, 'vol']
        
        return(artist_summary_data)
            
            
    def plot_album_charac(self, album, char):
        """
        Plot distribution of audio feature for an artist album

        Parameters:
            album (str): name of artist album
            char (str): name of audio feature

        """
        
        album_chars = self.album_track_summary[album]
        plt.bar(album_chars.index, album_chars.loc[:, char])
        plt.title(f'{char} for {album} by {self.artist}')
        plt.xticks(rotation = 90)


############################################
# Hard-coded artists data from Spotify API #
############################################
        
        
def load_artist_mapping():
    """
    Map selected artists to Spotify uri and if artist is classic

    Returns:
        artist_dict (dict): mapping between artists and Spotify uri and if aritst
            is a classic artist

    """
    
    contemp_artists = ['JID', 'Logic', 'BROCKHAMPTON', 'Smino', 'SZA', 
                       'Travis Scott']
    
    contemp_uri_list = [
                'spotify:artist:6U3ybJ9UHNKEdsH7ktGBZ7', 'spotify:artist:4xRYI6VqpkE3UwrDrAZL8L',
                'spotify:artist:1Bl6wpkWCQ4KVgnASpvzzA', 'spotify:artist:1ybINI1qPiFbwDXamRtwxD',
                'spotify:artist:7tYKF4w9nC0nq9CsPZTHyP', 'spotify:artist:0Y5tJX1MQlPlqiwlOH1tJY']
    
    
    classic_artists = [
                'MF DOOM', 'Nas', 'Kendrick Lamar', 'J. Cole', 'Mos Def', 
                'The Notorious B.I.G.', 'Tupac', 'Dr. Dre',
                'Snoop Dog', 'Mobb Deep', 'Kanye West', 'Jay-Z', 'De La Soul', 
                'Wu-Tang Clan', 'Lauryn Hill', 'Outkast', 'A Tribe Called Quest', 
                'Naughty by Nature', 'Cypress Hill', 'Common']
    
    classic_uri_list = [
                'spotify:artist:2pAWfrd7WFF3XhVt9GooDL', 'spotify:artist:20qISvAhX20dpIbOOzGK3q', 
                'spotify:artist:2YZyLoL8N0Wb9xBt1NhZWg', 'spotify:artist:6l3HvQ5sa6mXTsMTB19rO5', 
                'spotify:artist:0Mz5XE0kb1GBnbLQm2VbcO', 'spotify:artist:5me0Irg2ANcsgc93uaYrpb',
                'spotify:artist:1ZwdS5xdxEREPySFridCfh', 'spotify:artist:6DPYiyq5kWVQS4RGwxzPC7',
                'spotify:artist:7hJcb9fa4alzcOq3EaNPoG', 'spotify:artist:6O2zJ0tId7g07yzHtX0yap',
                'spotify:artist:5K4W6rqBFWDnAN6FQUkS6x', 'spotify:artist:3nFkdlSjzX9mRTtwJOzDYB',
                'spotify:artist:1Z8ODXyhEBi3WynYw0Rya6', 'spotify:artist:34EP7KEpOjXcM2TCat1ISk',
                'spotify:artist:2Mu5NfyYm8n5iTomuKAEHl', 'spotify:artist:1G9G7WwrXka3Z1r7aIDjI7',
                'spotify:artist:09hVIj6vWgoCDtT03h8ZCa', 'spotify:artist:4Otx4bRLSfpah5kX8hdgDC',
                'spotify:artist:4P0dddbxPil35MNN9G2MEX', 'spotify:artist:2GHclqNVjqGuiE5mA7BEoc']
    
    contemp_bool = [False for ii in range(len(contemp_artists))]
    classic_bool = [True for ii in range(len(classic_artists))]
    contemp_tuple = [(contemp_uri_list[ii], contemp_bool[ii]) for ii in range(len(contemp_artists))]
    classic_tuple = [(classic_uri_list[ii], classic_bool[ii]) for ii in range(len(classic_artists))]

    contemp_dict = dict(zip(contemp_artists, contemp_tuple))
    classic_dict = dict(zip(classic_artists, classic_tuple))  
    artist_dict = dict(contemp_dict)
    artist_dict.update(classic_dict)
                        
    return(artist_dict)


def load_artist_data(artist_dict, writeCSV = False):
    """
    Aggregate discrete data for specific artists

    Parameters:
        artist_dict (dict): mapping between artist and Spotify uri and if artist 
        is a classic artist
        writeCSV (bool), optional: write dataframe to a CSV file
    
    Returns:
        all_data (pd.DataFrame): artist level data
    
    """

  
    ii = 0
    for key, value in artist_dict.items():
        artist_data = Artist(key, value[0]).get_artist_data()
        if ii == 0:
            all_data = pd.DataFrame(columns = artist_data.index.tolist() + ['classic'])
        all_data.loc[key, artist_data.index] = artist_data.values
        all_data.loc[key, 'classic'] = value[1]
        ii += 1
    

    if writeCSV == True:
        
        all_data = all_data.reset_index()
        all_data = all_data.rename(columns = {'index':'artist'})
        all_data.to_csv("..//Data//artist_static_data.csv", index = False)
        
    return(all_data)
   
  