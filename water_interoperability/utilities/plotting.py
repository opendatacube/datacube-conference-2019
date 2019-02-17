from calendar import month_name
import numpy as np
import xarray as xr
from pathlib import Path
from bokeh.plotting import figure, output_file, show
from bokeh.io import output_notebook
from bokeh.core.properties import value
from bokeh.transform import dodge
from bokeh.models import Label
from bokeh.palettes import Accent6, Dark2, Category10
from bokeh.colors.named import darkgray

from typing import Dict

def init_bokeh():
    output_notebook()

def plot_availability(data: Dict[str, xr.Dataset]):
    coords={'month': range(1, 13)}
    months_str = [m[:3] for m in list(month_name)[1:]]
    frequencies = {}
    for name, dataset in data.items():
        freq = dataset.time.groupby('time.month').count('time')
        all_months = xr.DataArray(data = [0]*12, coords=coords, dims=coords, name='time')
        frequencies[name] = freq.combine_first(all_months).assign_coords(month=months_str)
        # Generate the bar chart on a new figure
    aggregated = np.sum([freq.values for freq in frequencies.values()], axis=0)

    
    
    
    
    
    data = {name: freq.values for name, freq in frequencies.items()}
    data['months'] = months_str
    data['aggregated'] = aggregated

    # Calculate the max frequency to scale the Y-axis automatically
    max_freq = max([freq.values.max() for freq in frequencies.values()] + [aggregated.max()])

    p = figure(x_range=months_str,
               y_range=(0, max_freq),
               plot_width=800,
               plot_height=400,
               title="Monthly data points",
               toolbar_location=None,
               tools="")

    # Calculate offsets and widths for the bars
    inter_group = 0.4
    width = (1 - inter_group / 2) / len(frequencies)
    offset = (width + inter_group / 2 - 1) / 2

    # Plot the aggregate bar
    p.vbar(x=dodge('months', 0, range=p.x_range), 
           top='aggregated', 
           width=(1 - inter_group + width / 2), 
           source=data,
           color='#000000', 
           legend=value('aggregated'), 
           fill_alpha=0, 
           line_color='lightgray', 
           line_width=2.0)

    # Plot the raw data bars, one per dataset
    for count, name in enumerate(frequencies.keys()):
        p.vbar(x=dodge('months', count*width+offset, range=p.x_range), 
               top=name, 
               width=width-0.1, 
               source=data,
               color=Category10[10][count],
               legend=value(name), 
               fill_alpha=.4)

    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"
    show(p)