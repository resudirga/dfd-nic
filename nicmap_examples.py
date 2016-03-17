# -*- coding: utf-8 -*-

"""
Plotting using NICmap 
"""
import os
import NICmap
import csv

FIG_WIDTH_IN = 10
FIG_HEIGHT_IN = 8 
map = NICmap.NICBasemap()     
map.fig.set_size_inches((FIG_WIDTH_IN, FIG_HEIGHT_IN), forward=True)

# Maternal mortality rate per 100,000 
# map.maternal_mortality_by_dept()

# Population Density by Municipality
map.population_density_by_municipality()

# Show municipality boundaries
#map.draw_municipalities(source='gadm')

# Show the figure and save
map.fig.show()
fdir = os.path.dirname(os.path.realpath(__file__))
map.fig.savefig(os.path.join(fdir,"Population_Density_by_Municipality.png"), bbox_inches='tight', dpi=200) 