import numpy as np
import matplotlib.pyplot as plt

def getStats(df):
    '''this function computes and generate the div string object
    to be used as a statistics display on filtered points'''
    mean=df['enp'].mean()
    std=df['enp'].std()
    median = df['enp'].median()
    minVal = df['enp'].min()
    maxVal = df['enp'].max()

    group_df = df.groupby(df['landuse']).mean()
    fig_stats = plt.figure()
    # ax1 = fig_stats.add_subplot(111)
    # ax1.bar(df['landuse'], df['enp'])
    # ax1.tick_params(rotation = 60, length = 2, axis = 'x')
    # ax1.set_title('Noise Pollution per Landuse Type')
    # ax1.set(ylabel='Noise Pollution (dB)')

    # fig_stats.savefig('img/stats.png', bbox_inches='tight')

    string = ("<font size='3'><p>" + 
        "</p><p>"+ 'Noise Pollution Statistics on filtered points' + "</p>" +
        "<table style='width: 80%; border-collapse: collapse;' border='3' cellpadding='4'>"
        "<tbody>"
        "<tr>"
        "<td>" + "&nbsp;" + 'Mean' + "</td>"
        "<td>"+"&nbsp;"+ str(round(mean,1)) + ' dB' + "</td>"
        "</tr>"
        "<tr>"
        "<td>"+"&nbsp;"+ 'Median' +"</td>"
        "<td>"+"&nbsp;"+ str(round(median,1)) + ' dB'+"</td>"
        "</tr>"
        "<tr>"
        "<td>"+"&nbsp;"+ 'Min' +"</td>"
        "<td>"+"&nbsp;"+ str(round(minVal,1)) + ' dB' +"</td>"
        "</tr>"
        "<tr>"
        "<td>"+"&nbsp;"+ 'Max'+"</td>"
        "<td>"+"&nbsp;"+ str(round(maxVal,1)) + ' dB'+"</td>"
        "</tr>"
        "<tr>"
        "<td>"+"&nbsp;"+ 'Std. Deviation'+"</td>"
        "<td>"+"&nbsp;"+ str(round(std,1)) + ' dB'+"</td>"
        "</tr>"
        "</tbody>"
        "</table>")

    return string
