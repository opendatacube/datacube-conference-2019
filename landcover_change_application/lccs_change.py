import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
import rasterio
import pandas as pd # I hate myself for this

def write_diff(foo:xr.DataArray, fn, nodata=-1, dtype=None, debug=False):
    dtype=dtype if dtype is not None else foo.dtype
    with rasterio.open(
                fn,
                'w',
                driver='GTiff',
                height=len(foo[foo.dims[1]]),
                width=len(foo[foo.dims[0]]),
                count=1, #len(bands),
                dtype=dtype,
                crs=foo.crs,
                transform=foo.transform[:6],
                nodata=nodata,
            ) as dst:
                dst.write(foo.astype(dtype).values, 1)
                
                # Copy metadata
                #for attr in foo.attrs:
                #    dst.update_tags(attr=foo.attrs[attr])
                dst.update_tags(**foo.attrs)
                
#                 # TODO: Can we add colormap so we don't have to do it in e.g. QGIS? (may not work w/ more than 256 levels)
#                 dst.write_colormap(1, {
#                     0: (255, 0, 0, 255),
#                     255: (0, 0, 255, 255),
#                 })
                                    
                dst.close()
                
    if debug:
        tmp = xr.open_rasterio('rep/landcover-hack/bleh_diff.tif').isel(band=0,drop=True).rename('tmp')
        print(tmp)
        tmp.plot(figsize=(10,10)) # The figsize is just to avoid issue w/ particular jupyter instance
        #plt.imshow(tmp);
        #return tmp
        
LCCS_Category_Labels = { # Note: AC made up the L1/L2 labels... (see http://www.fao.org/docrep/003/x0596e/x0596e01f.htm)
    # L1
    100: 'Vxx',
    200: 'NVxx',
    # L2
    110: 'TVx',
    120: 'AVx',
    210: 'TNVx',
    220: 'ANVx',
    # L3
    111: 'CTV',
    112: 'NTV',
    123: 'CAV',
    124: 'NAV',
    215: 'AS',
    216: 'BS',
    227: 'AW',
    228: 'NW',
}

LCCS_Category_Descriptions = { # Note: AC made up the L1/L2 labels...
    # L1
    100: 'L1: Primarily Vegetated',
    200: 'L1: Primarily Non-Vegetated',
    # L2
    110: 'L2: Terrestrial',
    120: 'L2: Aquatic or Regularly Flooded',
    210: 'L2: Terrestrial',
    220: 'L2: Aquatic or Regularly Flooded',
    # L3
    111: 'Cultivated & Managed Areas',
    112: '(Semi) Natural Vegetation',
    123: 'Cultivated Aquatic Areas',
    124: '(Semi) Natural Aquatic Vegetation',
    215: 'Artifical Surfaces',
    216: 'Bare Areas',
    227: 'Artifical Waterbodies, Snow & Ice',
    228: 'Natural Waterbodies, Snow & Ice',
}

LCCS_Transition_Labels = {
    111111: 'stable',
    111112: 'afforestation',
    111123: 'change in agriculture',
    111124: 'afforestation',
    111215: 'urban expansion',
    111216: 'vegetation loss',
    111227: 'inundation',
    111228: 'inundation',
    
    112111: 'agricultural expansion',
    112112: 'stable',
    112123: 'agricultural expansion',
    112124: 'inundation',
    112215: 'urban expansion',
    112216: 'vegetation loss',
    112227: 'inundation',
    112228: 'inundation',
    
    123111: 'agriculture drainage',
    123112: 'afforestation/abandonment',
    123123: 'stable',
    123124: 'vegetation establishment',
    123215: 'urban expansion',
    123216: 'vegetation loss',
    123227: 'inundation',
    123228: 'inundation',
    
    124111: 'wetland drainage',
    124112: 'wetland loss',
    124123: 'wetland establishment',
    124124: 'stable',
    124215: 'urban expansion',
    124216: 'vegetation loss',
    124227: 'inundation',
    124228: 'inundation',
    
    215111: 'withdrawal of settlements',
    215112: 'withdrawal of settlements',
    215123: 'withdrawal of settlements',
    215124: 'withdrawal of settlements',
    215215: 'stable',
    215216: 'withdrawal of settlements',
    215227: 'inundation',
    215228: 'inundation',
    
    216111: 'agriculture expansion',
    216112: 'vegetation establishment',
    216123: 'vegetation establishment',
    216124: 'vegetation establishment',
    216215: 'urban expansion',
    216216: 'stable',
    216227: 'inundation',
    216228: 'inundation',
    
    227111: 'wetland drainage',
    227112: 'wetland drainage',
    227123: 'vegetation establishment',
    227124: 'vegetation establishment',
    227215: 'urban expansion',
    227216: 'wetland drainage',
    227227: 'stable',
    227228: 'wetland establishment',
    
    228111: 'wetland drainage',
    228112: 'vegetation encroachment',
    228123: 'wetland drainage',
    228124: 'vegetation encroachment',
    228215: 'urban expansion',
    228216: 'wetland drainage',
    228227: 'urban expansion',
    228228: 'stable',
}

LCCS_Transition_State = {
    'stable': [227227, 124124, 228228, 215215, 216216, 112112, 111111, 123123],
    'degradation': [112111,227111,216228,216227,111215,111216,111227,111228,123111,124215,112123,112124,112215,112216,112227,112228,124216,236215,124227,215228,123215,123216,123227,123228,124111,124112,215227,124228,227112,227215,227216,228111,228112,228123,228124,228215,228216,228227],
    'improvement': [111124,111123,111112,215124,227123,227124,215112,215216,124123,215111,123124,216111,216112,216123,216124,123112,215123,227228],
    'unknown': [],
}

# Add entries for L1 and L2 to the above lists
for a,av in LCCS_Category_Labels.items():
    for b,bv in LCCS_Category_Labels.items():
        idx=a*1000+b
        if idx not in LCCS_Transition_Labels:
            LCCS_Transition_Labels[idx] = "{a} --> {b}".format(a=av,b=bv)
            LCCS_Transition_State['unknown'].append(idx)
            
# Create short form of transitions
LCCS_Transitions = {} 
for idx in LCCS_Transition_Labels:
    a = idx//1000
    b = idx%1000
    if a==b:
        LCCS_Transitions[idx] = LCCS_Category_Labels[a]
    else:
        LCCS_Transitions[idx] = "{a} -> {b}".format(
            a=LCCS_Category_Labels[a],
            b=LCCS_Category_Labels[b])

def LCCS_ChangeCounts(da):
    #counts = np.histogram(da, bins=[k for k in LCCS_ValueToTuple.keys()])
    unique_elements, counts_elements = np.unique(da.values, return_counts=True) # Note that this includes only non-zero values
    # TODO: Expand on this!  
    return dict(zip(unique_elements, counts_elements))

def LCCS_ChangeStats(da):
    counts = da.counts if 'counts' in da.attrs else LCCS_ChangeCounts(da)
    denominator = 100.0/np.prod(da.shape)
    denominator_valid = 100.0/ np.sum([v for k,v in counts.items() if k != da.nodata])
    df = pd.DataFrame([   
            [
                pxval, # pixel value
                pxcount, # count w/ this value
                ','.join([k for k,v in LCCS_Transition_State.items() if pxval in v]),
                LCCS_Transitions[pxval] if pxval in LCCS_Transitions else 'NoData' if pxval==da.nodata else '', # short text
                LCCS_Transition_Labels[pxval] if pxval in LCCS_Transition_Labels else 'NoData' if pxval==da.nodata else '', # long text
                pxcount*denominator,
                pxcount*denominator_valid if pxval != da.nodata else 0,
            ]
    for pxval,pxcount in counts.items()
        #if pxcount>0 # Don't list things that aren't detected
    ],
    columns=[
        'Value',
        'Count',
        'ChangeType',
        'Label',
        'Description',
        'PctOfTotal',
        'PctOfValid',
    ])
    return df.sort_values(by=['Count','ChangeType','Value'], ascending=False, na_position='last')

def LCCS_ChangeDetect(t1, t2, showonly=None, nodata=-1, name='LCCS_ChangeDetect_Result'):
    
    # Create some metadata to append
    metadata = {
        'nodata': nodata,
        # Copy CRS & transform if available
        'crs': t1.crs if 'crs' in t1.attrs else t2.crs if 'crs' in t2.attrs else None,
        'transform': t1.transform if 'transform' in t1.attrs else t2.transform if 'transform' in t2.attrs else None,
        # Value labels
        'class_labels': LCCS_Category_Labels,
        # Value descriptions
        'class_descriptions': LCCS_Category_Descriptions,
        # Change labels
        'change_labels': LCCS_Transitions,
        # Change descriptions
        'change_descriptions': LCCS_Transition_Labels,        
    }
    
    # Drop time if it exists (after adding it to metadata)
    if 'time' in t1.coords:
        metadata['time1'] = t1.time.values[0]
        t1 = t1.isel(time=0, drop=True)
    if 'time' in t2.coords: 
        metadata['time2'] = t2.time.values[0]
        t2 = t2.isel(time=0, drop=True)
    
    result = t1.astype(np.int32)*1000+t2.astype(np.int32)

    # This is INTERSECTION when given as array
    if showonly is not None:
        metadata['showonly'] = showonly
        if 'change' in showonly:
            result = result.where((result//1000)!=(result%1000), nodata)
        #if 'stable' in showonly:
        #    result = result.where((result//1000)==(result%1000), nodata)
        for state in LCCS_Transition_State:
            if state in showonly:
                result = result.where(np.isin(result.values,LCCS_Transition_State[state]), nodata)
    
    # Add the metadata to attrs
    for (k,v) in metadata.items():
        result.attrs[k] = v
        
    result.attrs['counts'] = LCCS_ChangeCounts(result)
    result.attrs['stats'] = LCCS_ChangeStats(result)

    result.name = name
    return result


def LCCS_Plot(da):
    nodata=da.nodata
    # Get all the values that were actually used so that labels aren't so crowded
    unique_vals = list(da.counts.keys()) if 'counts' in da.attrs else np.unique(da.values)
    if (nodata in unique_vals): unique_vals.remove(nodata)
    vmin = np.min(unique_vals)
    vmax = np.max(unique_vals)

    fig, ax = plt.subplots()
    fig.set_figwidth(16)
    fig.set_figheight(12)
    
    colours = "#787878 #96d564 #7af4d8 #75f4d0 #f5c7fd #faec87 #00b3de #0078c8 #d4f52c #505050 #a8fc15 #40e487 #f5c8f7 #f5d183 #60dffb #9bfbc5 #647864 #96FA64 #646464 #A7E6BE #FAC3F0 #FAEEBE #149EF4 #0FA0FA #ebf91f #1ac832 #7dedc6 #5a5a5a #e9b1e6 #feda48 #0abeee #0a9bee #cdf711 #86dad5 #d2faa4 #b4fac8 #4b4b4b #fae696 #c0effa #5087ff #f4fa13 #55e250 #03fcf8 #53fae1 #fa93f0 #6e6e6e #27c8f7 #2774f7 #f5f83e #85d964 #dbf652 #2ef7c8 #8c8c8c #f5b8c5 #3c3c3c #0c41f0 #dffa72 #64d26f #8ef8fb #64fbd8 #ccaccc #b6ae83 #fae696 #282828"
    bounds = [int(x) for x in "111111 111112 111123 111124 111215 111216 111227 111228 112111 112112 112123 112124 112215 112216 112227 112228 123111 123112 123123 123124 123215 123216 123227 123228 124111 124112 124123 124124 124215 124216 124227 124228 215111 215112 215123 215124 215215 215216 215227 215228 216111 216112 216123 216124 216215 216216 216227 216228 227111 227112 227123 227124 227215 227216 227227 227228 228111 228112 228123 228124 228215 228216 228227 228228".split(' ')]
    d = dict(zip(bounds, colours.split()))
    cols = [d[x] for x in unique_vals]
    
    cmap = colors.ListedColormap(cols)
    norm = colors.BoundaryNorm(unique_vals + [555555], cmap.N)
    im = ax.imshow(da,cmap=cmap, norm=norm)
    
    ax.set_title(da.name)
    
    cbar_ticks = unique_vals
    cbar_labels = [(LCCS_Transitions[v] if v in LCCS_Transitions else '') for v in unique_vals]

    cbar = fig.colorbar(im, ticks=cbar_ticks)
    cbar.ax.set_yticklabels(cbar_labels)
    
    return fig,ax