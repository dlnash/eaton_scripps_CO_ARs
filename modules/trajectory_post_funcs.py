"""
Filename:    trajectory_post_funcs.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: post-processing functions for trajectories
"""

import math
import xarray as xr
import pandas as pd
import numpy as np
import dask
import geopandas as gpd
import shapely.geometry
from utils import  find_closest_MERRA2_lon_df, find_closest_MERRA2_lon, MERRA2_range, roundPartial


dask.config.set(**{'array.slicing.split_large_chunks': True})

def load_trajectories(name):
    path_to_data = '/expanse/nfs/cw3e/cwp140/'
    ## load PRISM watershed precip dataset
    fname = path_to_data + 'preprocessed/PRISM/PRISM_HUC8_CO_sp.nc'
    PRISM = xr.open_dataset(fname)
    
    HUC8_lst = PRISM.HUC8.values ## get list of HUC8 IDs
    
    ## a quick function that assigns each watershed a basin value 
    ## based on the first 2 numbers of the HUC8 identifier
    
    basin_lst = []
    for i, HUC8_ID in enumerate(HUC8_lst):
        HUC2 = HUC8_ID[:2]
        if HUC2 == '14':
            basin = 'Colorado'
        elif HUC2 == '13':
            basin = 'Rio Grande'
        elif HUC2 == '11':
            basin = 'Arkansas'
        elif HUC2 == '10':
            basin = 'Missouri'
       
        basin_lst.append(basin)
        
    ds_lst = []
    for i, HUC8_ID in enumerate(HUC8_lst):
        fname = path_to_data +'preprocessed/ERA5_trajectories/{1}/PRISM_HUC8_{0}.nc'.format(HUC8_ID, name)
        ds = xr.open_dataset(fname)
        ds_lst.append(ds)
        
    ## concat ds_lst along HUC8 index
    ds = xr.concat(ds_lst, pd.Index(HUC8_lst, name="HUC8"))
    ## add the basin name as a coord
    ds = ds.assign_coords({'basin': ("HUC8", basin_lst)})

    return ds
    
def calculate_heatmaps_from_trajectories(ds, normalize=True, AR=True):

    ## open as geopandas dataframe
    df = ds.to_dataframe()
    if AR == True:
        df = df.dropna(subset = ['ar_scale'])
    else: 
        df = df
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")

    ### Code is based on https://james-brennan.github.io/posts/fast_gridding_geopandas/

    ### BUILD A GRID 
    # total area for the grid
    # xmin, ymin, xmax, ymax= gdf.total_bounds
    ## Set up the grid to match ERA5 spacing
    xmin, ymin, xmax, ymax= [-175., 15., -85.,  63.]
    # how many cells across
    cell_size = 0.5 ## quarter degree cell size
    # ncells_x = (xmax-xmin)/cell_size
    # ncells_y = (ymax-ymin)/cell_size
    
    # projection of the grid
    crs = "EPSG:4326"
    # create the cells in a loop
    grid_cells = []
    for x0 in np.arange(xmin, xmax+cell_size, cell_size ):
        for y0 in np.arange(ymin, ymax+cell_size, cell_size):
            # bounds
            x1 = x0-cell_size
            y1 = y0+cell_size
            grid_cells.append( shapely.geometry.box(x0, y0, x1, y1)  )
    cell = gpd.GeoDataFrame(grid_cells, columns=['geometry'], 
                                     crs=crs)

    merged = gpd.sjoin(gdf, cell, how='left', predicate='within')

    # make a simple count variable that we can sum
    merged['n_traj']=1
    # Compute stats per grid cell -- aggregate fires to grid cells with dissolve
    dissolve = merged.dissolve(by="index_right", aggfunc="count")
    # put this into cell
    cell.loc[dissolve.index, 'n_traj'] = dissolve.n_traj.values

    ## normalize cell using min-max method
    max = cell['n_traj'].max()
    min = cell['n_traj'].min()
    denom = max-min

    if normalize == True:
        cell['n_traj'] = (cell['n_traj'] - min)/denom
    else:
        cell['n_traj'] = cell['n_traj']
        
    return cell