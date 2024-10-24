"""
Filename:    daily_filtered_anomalies_era5_prs.py
Author:      Deanna Nash, dlnash@ucsb.edu
Description: Functions to filter annual climatology of daily gridded/time series ERA5 data using harmonics.

"""
import sys
import numpy as np
import xarray as xr

# Path to modules
sys.path.append('../../../modules/')

from harmonics import harmonic

#######################
# Variables to Update #
#######################

region='gulf_of_mexico2'

### Constants ###
outdir = '/expanse/nfs/cw3e/cwp140/preprocessed/ERA5/cross_section/'
datadir = '/expanse/nfs/cw3e/cwp140/preprocessed/ERA5/cross_section/daily/'
fmt = '.nc'

print('Step 1: Reading data...')
filename_pattern = datadir + "era5_{0}_025dg_daily_uvwq_*.nc".format(region)
print(filename_pattern)
ds = xr.open_mfdataset(filename_pattern,
                       engine='netcdf4',
                       combine='by_coords')

print('ds size in GB {:0.2f}\n'.format(ds.nbytes / 1e9))

## add wvflux data to dataset
qu = ds.q*ds.u
qv = ds.q*ds.v
ds = ds.assign(wvflux=np.sqrt(qu**2 + qv**2))


## calculate annual climatology
print('Step 2: Calculating annual climatology...')
clim_mean = ds.groupby('time.dayofyear').mean('time')
clim_std = ds.groupby('time.dayofyear').std('time')

# # ### Save Daily Climatology as netcdf

## Save Daily Climatology as netcdf
clim_path = outdir + 'daily_mean_clim_' + region + fmt
clim_mean.load().to_netcdf(path=clim_path, mode = 'w', format='NETCDF4')

## Save Standard Deviation as netcdf
std_path = outdir + 'daily_std_clim_' + region + fmt
clim_std.load().to_netcdf(path=std_path, mode = 'w', format='NETCDF4')

## filter annual climatology
print('Step 3: Filtering annual climatology...')
filtered_clim = harmonic(clim_mean)

## Save Filtered Climatology as netcdf
print('Step 4: Saving filtered climatology...')
clim_path = outdir + 'filtered_daily_mean_clim_' + region + fmt
filtered_clim.load().to_netcdf(path=clim_path, mode = 'w', format='NETCDF4')

## Calculate Anomalies
print('Step 5: Calculating anomalies...')
anomalies = ds.groupby('time.dayofyear') - filtered_clim
# long_term_mean = anomalies.mean('time', skipna=True)

## Write anomalies to yearly file
print('Step 6: Writing anomalies to yearly files...')
years, datasets = zip(*anomalies.groupby('time.year'))
paths = [outdir +'anomalies/daily_filtered_anomalies_{0}_%s.nc'.format(region) % y for y in years]
xr.save_mfdataset(datasets, paths)