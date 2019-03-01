import numpy as np
import xarray as xr
import warnings
import folium
import dask

import datacube.storage.masking as masking

def visualize_target_area(center=False, buffer=False, top_left=False, bottom_right=False):
    '''Utility to generate a folium map based on your target coordinates
    Arguments:
    ----------
    
    center: tuple of int or float
         (lat, lon) coordinates of the center
    buffer: int or float
         buffer around center
    top_left: tuple of int or float
         (lat, lon) coordinates of the top left corner
    bottom_right: tuple of int or float
         (lat, lon) coordinates of the bottom right corner
    Returns:
    --------
    m: folium map
    x: tuple of (lon_min, lon_max)
    y: tuple of (lat_min, lat_max)
    '''
    def test_input(var):
        return var is not False
    map_center = all([test_input(center), test_input(buffer)])
    map_corner = all([test_input(top_left), test_input(bottom_right)])
    
    if map_center:
        if not isinstance(center, tuple) or not all([isinstance(x, (int, float)) for x in center]):
            raise ValueError('\'center\' must be a tuple of float or int')
        if not isinstance(buffer, (int, float)):
            raise ValueError('\'buffer\' must be a int or float')
        lon_min = center[1] - buffer
        lon_max = center[1] + buffer

        lat_min = center[0] - buffer
        lat_max = center[0] + buffer
    elif map_corner:
        if not isinstance(top_left, tuple) or not all([isinstance(x, (int, float)) for x in top_left]):
            raise ValueError('\'top_left\' must be a tuple of float or int')
        if not isinstance(bottom_right, tuple) or not all([isinstance(x, (int, float)) for x in bottom_right]):
            raise ValueError('\'bottom_right\' must be a tuple of float or int')
        lat_min = top_left[0]
        lon_min = top_left[1]
        
        lat_max = bottom_right[0]
        lon_max = bottom_right[1]
        
        center = (np.mean([lat_min, lat_max]), np.mean([lon_min, lon_max]))
    else:
        raise RuntimeError('You need pass at least \'center\' and \'buffer\' OR \'top_left\' and \'bottom_right\'')
    
    bbox = [[lat_min, lon_min],
           [lat_min, lon_max],
           [lat_max, lon_max],
           [lat_max, lon_min],
           [lat_min, lon_min]]
    m = folium.Map(location=center, zoom_start=10)
    bounds = folium.PolyLine(bbox, color='red')
    m.fit_bounds([[lat_min, lon_min], [lat_max, lon_max]])
    bounds.add_to(m)
    return m, (lon_min, lon_max), (lat_min, lat_max)


def ndvi(nir, red):
    '''Utility to calculate NDVI
    Arguments:
    ----------
    
    nir: xarray.DataArray
        Near-InfraRed measurement
    red: xarray.DataArray
        Visible Red measurement

    Returns:
    --------
    ndvi: xarray.DataArray
    '''
    if not all([isinstance(x, xr.DataArray) for x in [nir, red]]):
        raise TypeError('nir and red must be a xarray.DataArray')
    # calculate ndvi
    ndvi = (nir - red) / (nir + red)
    # saturate outside -1 to 1
    ndvi = ndvi.where(~(ndvi > 1), other=1)
    ndvi = ndvi.where(~(ndvi < -1), other=-1)
    # apply mask

    return ndvi


def _do_block_mean(block):
    return np.array([np.nanmean(block)], dtype='float32', ndmin=block.ndim)


def _build_coords_info(coords, dims):
    coords_dict = {}
    for c, dim in zip(coords, dims):
        min_c = min(coords[c])
        max_c = max(coords[c])
        coords_dict[c] = np.linspace(min_c, max_c, dim)
    return coords_dict


def _do_downsample(input_xarray, rechunking):
    # rechunking
    if isinstance(input_xarray, xr.Dataset):
        data_stack = []
        for m in input_xarray.data_vars:
            if rechunking is not False:
                data_stack.append(input_xarray[m].data.rechunk(rechunking))
            else:
                data_stack.append(input_xarray[m].data)

        data_stack = dask.array.stack(data_stack, axis=-1)
    elif isinstance(input_xarray, xr.DataArray):
        if rechunking is not False:
            data_stack = input_xarray.data.rechunk(rechunking)
        else:
            data_stack = input_xarray.data
        data_stack = dask.array.stack([data_stack], axis=-1)
    
    # performing the resampling
    return data_stack.map_blocks(_do_block_mean, dims=data_stack.ndim, dtype='float32', chunks=tuple([1 for _ in range(data_stack.ndim)]))


def downsample_by_chunks(input_xarray, rechunking=False, return_xarray=False):
    """Downsample the input image so that the output data will have one pixel for every chunk
    
    Arguments:
    -----------
    input_xarray : xarray.Dataset or xarray.DataArray
        dataset to resample
    rechunking : tuple of int, optional (default : False)\n
        whether you want to rechunk the data prior to downsample it. This will give you control on the output resolution
    return_xarray : bool, optional (default : False)\n
        whether you want a numpy array or xarray object as output
    
    Returns:
    -----------
    out : np.ndarray, xarray.Dataset or xarray.DataArray
        downsampled data by averaging the data in each chunk
    """
    if rechunking is not False and (not isinstance(rechunking, tuple) or not all([isinstance(x, int) for x in rechunking])):
        raise TypeError('rechunking must be a tuple of int')

    if isinstance(input_xarray, xr.Dataset):
        # performing rechunking and donwsampling
        resampled_data = _do_downsample(input_xarray, rechunking)
        if return_xarray is False:
            # if you don't want an xarray object, return the raw data
            return resampled_data

        # linear interpolation of coordinates info to reflect the new data shape
        coords_dict = _build_coords_info(input_xarray.coords, resampled_data.shape[:-1])

        # rebuilding the measurements as DataArray
        vars_dict = {}
        for i, var in enumerate(input_xarray.data_vars):
            vars_dict[var] = xr.DataArray(np.take(resampled_data, i, axis=-1),
                                            coords=coords_dict,
                                            dims=tuple(coords_dict.keys()))

        # returning the dataset
        return xr.Dataset(vars_dict, attrs=input_xarray.attrs.copy())

    elif isinstance(input_xarray, xr.DataArray):
        # performing rechunking and donwsampling
        resampled_data = _do_downsample(input_xarray, rechunking)
        if return_xarray is False:
            # if you don't want an xarray object, return the raw data
            return resampled_data
        
        # linear interpolation of coordinates info to reflect the new data shape
        coords_dict = _build_coords_info(input_xarray.coords, resampled_data.shape[:-1])

        # return the DataArray
        return xr.DataArray(np.take(resampled_data, 0, axis=-1),
                            coords=coords_dict,
                            dims=tuple(coords_dict.keys()))
    else:
        raise TypeError('input_xarray must be a xarray.Dataset or xarray.DataArray')
