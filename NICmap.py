#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Visualization of Nicaragua health care system and socio-economic indicators on map.
"""

import os, sys
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib import cm
from mpl_toolkits.basemap import Basemap
import shapefile
import numpy as np
import csv

class NICBasemap(Basemap):
    """
    A basemap of Nicaragua inherited from the Basemap class.
    Example: 
      map = NICBasemap()	
    """
    def __init__(self):
        super().__init__(projection='merc', lat_0=-85., \
                            lon_0=13., resolution='l', area_thresh=1500.0, \
                            llcrnrlon=-88., llcrnrlat=10.5, \
                            urcrnrlon=-81.89, urcrnrlat=15.33)
        
        # Figure and axis of the main map
        fig, ax = plt.subplots() 
        self.fig = fig
        self.ax = ax
        self.ax.axis("off")
        
        # Data directory
        self.data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/")
        
        # map won't show if this line is omitted
        self.drawmapboundary() 
        
        # Map's scale
        MAP_SCALE_LON = -87.423
        MAP_SCALE_LAT = 10.93
        MAP_SCALE_LON0 = -87.297
        MAP_SCALE_LAT0 = 10.93 
        MAP_SCALE_LENGTH = 100
        self.drawmapscale(MAP_SCALE_LON, MAP_SCALE_LAT, MAP_SCALE_LON0, MAP_SCALE_LAT0, 
                         MAP_SCALE_LENGTH, barstyle='fancy', fontcolor = '0.3', fillcolor2 = '0.3')
                         
    def draw_shp_polygons(self, shp_filepath, linewidths=0.2, colors='k', antialiaseds=None, linestyles='solid'):
        """
        Draw a shapefile containing polygons
        """   
        # Read the shapefile as shapes and records. For each polygon in shapes, draw its boundaries
        r = shapefile.Reader(shp_filepath)
        shapes = r.shapes()
        records = r.records()

        for record, shape in zip(records, shapes):
            lons, lats = zip(*shape.points)
            data = [(x, y) for x, y in zip(*self(lons, lats))]
            
            # shape.parts is a list containing the starting index of each part of shape (e.g. a lake inside the shape) on xy_pts. If shape contains only 1 part, a list containing 0 is returned.
            if len(shape.parts) == 1: 
                segs = [data, ]
            else:
                segs = []
                for npart in range(1, len(shape.parts)):
                    ix1 = shape.parts[npart-1]
                    ix2 = shape.parts[npart]
                    segs.append(data[ix1:ix2])
                    
                segs.append(data[ix2: ])
            
            lines = LineCollection(segs, antialiaseds = [1, ])
            lines.set_edgecolors(colors)
            lines.set_linestyle(linestyles)
            lines.set_linewidth(linewidths)
            self.ax.add_collection(lines)
   
    def draw_depts(self, source = 'gadm', linewidth=0.4, color='k', antialiaseds=None, linestyle='solid'):
        """
        Draw department boundaries.
        """
        # Load the shapefile and record
        if source == 'gadm':
            fpath = os.path.join(self.data_dir, "NIC_adm/NIC_adm1")
        elif source == 'osm':
            fpath = os.path.join(self.data_dir, "OSM/mapanica-nicaragua-departamentos-2015-01-27")
        else:
            print('Source unknown. Using GADM boundaries.')
        self.draw_shp_polygons(fpath, linewidth, color, linestyles=linestyle)
        
        
    def draw_municipalities(self, source = 'gadm', linewidth=0.2, color='k', antialiaseds=None, linestyle='--'):
        """
        Draw municipality boundaries.
        """
        # Load the shapefile and record
        if source == 'gadm':
            fpath = os.path.join(self.data_dir, "NIC_adm/NIC_adm2")
        elif source == 'osm':
            fpath = os.path.join(self.data_dir, "OSM/mapanica-nicaragua-municipios-2015-01-27")
        else:
            print('Source unknown. Using OSM boundaries.')

        self.draw_shp_polygons(fpath, linewidth, color, linestyles=linestyle)
        

    def choropleth(self, adm_num_dicts, level = 'department', source='gadm', cmap_base=plt.cm.YlOrRd, ret_colormap_and_label=True, bin_lims=None, nbins=5, linewidth=0.4):
        """
        A choropleth map by department  or municipality. The dataset for boundaries of administrative areas is taken from GADM database 
        Original code is from here: https://github.com/astivim/Nicaragua-Population-Density-Map    
        
        Input:
        - adm_num_dicts: a list of dictionaries with the following key-value pairs: {'adm' : str, 'num' : float}
        - bin_lims (optional): values of bin edges
        - nbins (optional): number of bins, default = 5. Ignored if bin_lims is specified. 
        - cmap_base: base colormap. Default is plt.cm.YlOrRd (red)  
        - ret_colormap_and_label=True. If True, return colormap_label = {'bin_labels' : bin_labels, 'colormap' : custom_cmap} used for plotting. If False, colormap_label = None  

        Return: colormap_label = {'bin_labels' : bin_labels, 'colormap' : custom_cmap}
        """	
        # Divide nums into bins. For each entry in nums, assign to which bin it belongs to, then assign a color to each bin.
        
        adms = [item['adm'] for item in adm_num_dicts]
        nums  = [item['num'] for item in adm_num_dicts]  
        
        # Define bin_lims by dividing the range of nums into equally spaced portions
        if bin_lims:
            nbins = len(bin_lims)                
        else:
            temp_nums = [num for num in nums if num]
            bin_spacing = (max(temp_nums) - min(temp_nums) + 1) / nbins                
            bin_lims = np.arange(min(temp_nums), max(temp_nums) + bin_spacing, bin_spacing)
            nbins = len(bin_lims) 
            
        # Assign each num in nums into its respective bin and assign color. Use only nbins values from the colormap (cmap)
        nums_bin_ix = np.digitize(nums, bin_lims)      
        nums_bin_ix = [idx if idx < nbins else 0 for idx in nums_bin_ix]    
        cmaplist = [cmap_base(i) for i in range(cmap_base.N)]
        del_colors = np.int(np.ceil(cmap_base.N/float(nbins-1)))
        map_colors = cmaplist[0::del_colors]
        map_colors.insert(0, (1.0, 1.0, 1.0, 1.0))             # fill with white if no data (num is None)
        
        # Load the geographical data (shapefile and record)
        if level == 'department':
            fpath = os.path.join(self.data_dir, "NIC_adm/NIC_adm1")
        elif level == 'municipality':
            fpath = os.path.join(self.data_dir, "NIC_adm/NIC_adm2")
        else:
            print("Level unrecognized. Use 'department'")
            fpath = os.path.join(self.data_dir, "NIC_adm/NIC_adm1")
            
        r = shapefile.Reader(fpath)
        shapes = r.shapes()
        records = r.records()
        
        # Extract lat and lon data from the GADM shapefile and assign a facecolor to each department 
        for record, shape in zip(records, shapes):
            lons, lats = zip(*shape.points)
            data = [(lon, lat) for lon, lat in zip(*self(lons, lats))]
            if level == 'department':
                adm_name = record[4]
            else:
                adm_name = record[6]
            
            try:
                adm_idx = adms.index(adm_name)
                adm_num = adm_num_dicts[adm_idx]['num']
                color_idx = nums_bin_ix[adm_idx] 
            except ValueError:
                adm_num = None
                color_idx = 0

            if len(shape.parts) == 1:
                segs = [data, ]
            else:
                segs = []
                for i in range(1,len(shape.parts)):
                    index = shape.parts[i-1]
                    index2 = shape.parts[i]
                    segs.append(data[index:index2])
                
                segs.append(data[index2:])
            lines = LineCollection(segs, antialiaseds=(1,))            
            
            color = map_colors[color_idx] if adm_name not in ["Lago Nicaragua", "Lago de Nicaragua"] else 'aqua'
            lines.set_facecolors(color)
            lines.set_linewidth(linewidth)
            self.ax.add_collection(lines)
        
        if ret_colormap_and_label:
            custom_cmap = mpl.colors.ListedColormap(map_colors[1: ], name='from_list')
            bins = [(i1,i2) for i1,i2 in zip(bin_lims[0:nbins], bin_lims[1:nbins+1])]
            bin_labels = ["(%d - %d)" % (b[0],b[1]) for b in bins]
            colormap_label = {'bin_labels' : bin_labels, 'colormap' : custom_cmap}
        else:
            colormap_label = None
        
        return colormap_label
        
    def add_colorbar(self, colorbar, ax_pos = [0.83, 0.1, 0.02, 0.8]):
        """
        Add a colorbar with position and dimension defined by ax_pos
        """
        
        if colorbar:
            custom_cmap = colorbar['colormap']
            bin_labels = colorbar['bin_labels']
            
            numbins = len(bin_labels)
            
            #Add the axis for the colorbar
            ax_pos = [0.83, 0.1, 0.02, 0.8]
            ax_cb = self.fig.add_axes(ax_pos)

            cb = mpl.colorbar.ColorbarBase(ax_cb, cmap = custom_cmap, spacing = 'proportional')
            
            #Position the tick labels in the middle of the respective colorbar part
            delta = 1./(2*numbins)
            TickSpacing = 1./numbins
            xticks = [TickSpacing*x-delta for x in range(1,numbins+1)]
            cb.set_ticks(xticks)
            cb.ax.tick_params(color='k',labelcolor='k')
            cb.set_ticklabels(bin_labels, update_ticks=True)
            cb.outline.set_edgecolor('k')
        
    def show_reference(self, txt_source):
        """
        Print the source of data at the bottom of the map.
        """
        txt_src_pos = (0, 0)
        self.ax.text(txt_src_pos[0], txt_src_pos[1], txt_source, 
                     transform=self.ax.transAxes, fontsize=8, 
                     ha='left', va='top')        

    def show_title(self, title_text, title_pos = (0.03, 0.95)):
        # show the locations of all health units in Nicaragua 
        self.ax.text(title_pos[0], title_pos[1], title_text, transform=self.ax.transAxes, 
        fontsize=12, fontweight='bold', color='0.3', va='top')
        
    def maternal_mortality_by_dept(self):
        """
        Plot a choropleth map of maternal mortality rate by department (per 100,000). Source:  The Nicaraguan Health System, PATH, 2011
        """
        fpath = os.path.join(self.data_dir, "PATH_Maternal_Mortality_GADM_ADM1.csv") 
        dept_num_dicts = []
        with open(fpath, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames = ['adm', 'num'], delimiter=';') 
            for nrow, row in enumerate(reader):
                if nrow > 4:
                    dept_num_dicts.append({'adm' : row['adm'], 'num' : float(row['num'])})
        
        colorbar = self.choropleth(dept_num_dicts, level='department', nbins=4)
        self.add_colorbar(colorbar)
        
        self.show_title('Nicaragua \nMaternal Mortality Rate \nper 100,000')
        self.show_reference('Sequeira M, Espinoza H, Amador JJ, Domingo G, Quintanilla M, and de los Santos T. \nThe Nicaraguan Health System, PATH, 2011')
        
    def population_density_by_municipality(self):
        """
        Plot a choropleth map of population density by municipality. Source: OpenStreetMap
        """
        fpath = os.path.join(self.data_dir, "Population/Population_Density_by_Municipality.csv") 
        dept_num_dicts = []
        with open(fpath, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames = ['adm', 'num'], delimiter=',', ) 
            for nrow, row in enumerate(reader):
                if nrow > 0:
                    dept_num_dicts.append({'adm' : row['adm'], 'num' : float(row['num']) if row['num'] else None})   
                    
        binlims = [3, 50, 100, 200, 500, 1000, 2000, 3000, 4000]
        colorbar = self.choropleth(dept_num_dicts, level='municipality', bin_lims = binlims, linewidth=0)
        self.add_colorbar(colorbar)
        
        self.show_title('Nicaragua \nPopulation Density \nper km^2')
        self.show_reference('OpenStreetMap. Retrieved: Nov 2015')
        
        
#---------- main program --------------
if __name__ == "__main__":
    
    # Figure's width and height in inches
    FIG_WIDTH_IN = 10
    FIG_HEIGHT_IN = 8  
    TITLE_POS = (0.03, 0.95)    
    
    map = NICBasemap()
    map.fig.set_size_inches((FIG_WIDTH_IN, FIG_HEIGHT_IN), forward=True)
    map.draw_municipalities(source='osm')
    map.show_title('Nicaragua \nmunicipalities', TITLE_POS)
    plt.show()