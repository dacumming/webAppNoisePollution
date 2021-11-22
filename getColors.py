from bokeh.palettes import Spectral11
def getCode(i):
    return Spectral11[i]

def getColors(df):
    indices=(11*((df['enp']-df['enp'].min())/(df['enp'].max()-df['enp'].min()))).apply(int)
    indices=indices.replace(11,10)
    df['colors']=indices.apply(getCode)
    return df