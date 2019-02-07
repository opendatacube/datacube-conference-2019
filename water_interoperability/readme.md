# Dask Implementation
## Outcomes
Jupyter Notebook
## Description
Develop a notebook that uses more than one dataset to yield a single water product. Use Landsat (WOFS), Sentinel-1 (WASARD) and S2 (water QA band) to detect water over time and produce a WOFS-like result.
* Consider differences in spatial resolution of missions, as Landsat (30m), Sentinel-2 (10m,20m) and Sentinel-1 (20m) are different. Do we reproject into the same grid or use some other clever approach?
* Develop WOFS-like products (# water / # clear) for individual missions and also mission combinations. 
