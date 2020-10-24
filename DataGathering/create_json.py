# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import json


def load_data():
    
    # Load artist maping
    art_map = np.load('..//Data//artist_links.npy',allow_pickle='TRUE').item()
    return(art_map)


def get_points(radius, npoints):
    
    radians_point = 2*np.pi/npoints
    points = pd.DataFrame(columns = ['x','y'])
    for ii in range(0, npoints):
        points.loc[ii, 'x'] = radius*np.cos(ii*radians_point)
        points.loc[ii, 'y'] = radius*np.sin(ii*radians_point)
    return points
        
    
    
def create_json_file(writeJSON = False):
    
    art_map = load_data()
    npoints = len(art_map)
    
    points = get_points(10, npoints)
    artists = list(art_map.keys())
    
    json_dict = dict()
    json_dict['nodes'] = []
    
    
    # Get x,y coordinates for artist in circle network
    for ii in range(npoints):
        

        node_dict = {'id': artists[ii],
                    'x' : points.loc[ii, 'x'],
                    'y':  points.loc[ii, 'y']}
        
        json_dict['nodes'].append(node_dict)
    

    json_dict['edges'] = []
    
    # Get edges / connections for network graphg
    for key, values in art_map.items():
        for value in values:
            edge_dict = {'from': key, 
                         'to': value}
            json_dict['edges'].append(edge_dict)
            
    
    if writeJSON == True:
        with open('..//Data//JSON//artist_map.json', 'w') as fp:
            json.dump(json_dict, fp)
            print('wrote JSON file')


def create_json_file_d3(writeJSON=False):

    art_map = load_data()
    npoints = len(art_map)
    artists = list(art_map.keys())
    
    json_dict = dict()
    json_dict['nodes'] = []  

    # Get x,y coordinates for artist in circle network
    for ii in range(npoints):
        
        node_dict = {'id': ii,
                    'name' : artists[ii]}  
        
        json_dict['nodes'].append(node_dict)

    json_dict['links'] = []

    # Get edges / connections for network graph (KDC NOTE DO ONLY ONE WAY!!!!!!!!!!!!!!!!)

            
    
            