import numpy as np
import geopandas as gpd
from shapely.geometry import MultiLineString
from shapely.ops import polygonize
from geopandas.tools import sjoin
def getMeshgrid(df,s):
    '''from the dataframe, this function computes the data needed to plot the heat Map'''
    gridx = np.linspace(df['x'].min(), df['x'].max(), s)
    gridy = np.linspace(df['y'].min(), df['y'].max(),s)
    points = gpd.GeoDataFrame(df[['enp']], geometry=gpd.points_from_xy(df.x, df.y))
    hlines = [((x1, yi), (x2, yi)) for x1, x2 in list(zip(gridx[:-1], gridx[1:])) for yi in gridy]
    vlines = [((xi, y1), (xi, y2)) for y1, y2 in zip(gridy[:-1], gridy[1:]) for xi in gridx]
    polys = list(polygonize(MultiLineString(hlines + vlines)))
    id = [i for i in range((len(gridx)-1)*(len(gridy)-1))]
    grid = gpd.GeoDataFrame({"id": id, "geometry": polys})
    pointInPolys = sjoin(points, grid, how='left')
    z=np.zeros((grid.shape[0]))
    for i,r in grid.iterrows():
        z[i]=pointInPolys.loc[pointInPolys['id']==r['id']]['enp'].mean()
    z=z.reshape(len(gridx)-1,len(gridy)-1,order='A').T
    return [z]