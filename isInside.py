import numpy as np
import pandas as pd
from shapely.geometry import Polygon
from shapely.wkt import loads

def isInside(coords,df,n):
    '''Check which point of the dataframe are inside the drawn by the user
    and returns a boolean series specifying the indexes that fulfil the filtering and a message'''
    if len(coords['xs'])==0:
        return 'WARNING: There is no polygon drawing',pd.Series([True for i in range(n)])
    else:
        bools = pd.DataFrame([],dtype='bool')
        j=1
        for xpoly,ypoly in zip(coords['xs'],coords['ys']):
            list_of_tuples=[(x,y) for x,y in zip(xpoly,ypoly)]
            try:
                polygon=Polygon(list_of_tuples)
            except:
                return 'ERROR: please draw a valid polygon',pd.Series([True for i in range(n)])
            for i,r in df.iterrows():
                p=loads('POINT('+str(r['x'])+' '+str(r['y'])+')')
                bools.loc[i,str(j)]=p.within(polygon)
            j+=1
        aux=pd.Series([False for i in range(n)],dtype='bool')
        for column in bools:
            aux=np.logical_or(aux, bools[column].values)
        return 'Spatial Filtering Succesful',pd.Series(aux,dtype='bool')

