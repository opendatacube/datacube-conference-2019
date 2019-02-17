from skimage import measure
import numpy as np
from typing import List, Iterable, Tuple
import xarray as xr 

def segment_raster_into_pixel_groups( array: np.array,
                                      connectivity:int = 1) -> Iterable[List[Tuple[float,float]]]:
    
    arr = measure.label(array, connectivity=connectivity)
    pixel_groups = (np.dstack(np.where(arr == y))[0] for y in range(1,np.amax(arr)))
    
    yield pixel_groups

def segment_raster_into_grouped_sub_rasters(array: np.array) -> Iterable[np.array]:
    
    pixel_groups = segment_raster_into_pixel_groups(array)
    for group in pixel_groups:
        dynamic_array = np.zeros(array.shape) 
        for x,y in group:
            dynamic_array[x][y] = 1  
        yield dynamic_array

##### Different way of doing it
        
def group_pixels(array, connectivity = 1):
    arr = measure.label(array, connectivity=connectivity)
    return [np.dstack(np.where(arr == y))[0] for y in range(1,np.amax(arr))]

def numpy_group_mask(boolean_np_array, min_size = 5):  
    all_groups = group_pixels(boolean_np_array.astype(int))
    candidate_groups = filter(lambda group:
                                  (len(group) > min_size) & (group != 0).all(),
                                  all_groups)
    candidate_pixels = (pixel for group in candidate_groups for pixel in group)  
    dynamic_array = np.zeros(boolean_np_array.shape) 
    for x,y in candidate_pixels:
        dynamic_array[x][y] = 1  
    return dynamic_array.astype(bool)


def boolean_xarray_min_size_segmentation_filter(da,  min_size = 5):
    mask_np = numpy_group_mask(da.values,min_size = min_size)
    return xr.DataArray(mask_np,
                        dims = da.dims,
                        coords = da.coords,
                        attrs = {"group_size": min_size},
                        name = "filtered_chunks_mask")
