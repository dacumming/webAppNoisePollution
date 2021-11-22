#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#packages import
from flask import (
    Flask, render_template
)
from flask_debugtoolbar import DebugToolbarExtension
from bokeh.layouts import column,row
from bokeh.resources import INLINE
from bokeh.embed import server_document
from bokeh.models.widgets import DateRangeSlider
from bokeh.models import (
    MultiSelect, RangeSlider, ColumnDataSource, Div, PolyDrawTool,
    CDSView, RadioButtonGroup, Panel, Tabs, HoverTool
)
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.plotting import figure
import datetime
from sqlalchemy import create_engine
from bokeh.server.server import Server
from bokeh.themes import Theme
import pandas as pd
from tornado.ioloop import IOLoop
from getStats import getStats
from isInside import isInside
import numpy as np
from getMeshgrid import getMeshgrid
from threading import Thread

app = Flask(__name__, template_folder="templates")
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# add debugging tool (not visible)
app.debug = False
toolbar = DebugToolbarExtension(app)

# import dataframe from database
engine = create_engine('postgresql://postgres:password@localhost:5432/se4g')
df = pd.read_sql_table("enp", con=engine)

def modify_doc(doc):
    ngrid = 20  # grid for HeatMap
    source = ColumnDataSource(data=df)  # data source for plotting
    tile_provider = get_provider(CARTODBPOSITRON)  # get basemap
    TOOLTIPS = [  # information displayed with hovertool
        ("Longitude", "@lon{0,0.00000}\u00B0"),
        ("Latitude", "@lat{0,0.00000}\u00B0"),
        ("Date", "@dt"),
        ("Time", "@t"),
        ("Land Use", "@landuse"),
        ("ENP", "@enp{0,0.0} dB"),
        ("Picture", ""),
        ("", '''<img 
                        src="@pic" height="160" alt="@pic" width="210"
                        style="float: left; margin: 0px 15px 15px 0px;"
                        border="2"
                        ></img>''')
    ]
    # menu selection of classes
    LU_classes = df['landuse'].drop_duplicates().sort_values().reset_index(drop=True)
    menu = [(cl, cl) for _, cl in LU_classes.iteritems()]
    # different figures availabel in tabs
    plot1 = figure(x_range=(df['x'].min(), df['x'].max()), y_range=(df['y'].min(), df['y'].max()),
                   x_axis_type="mercator", y_axis_type="mercator", tools="pan,wheel_zoom,box_zoom,reset,save",
                   plot_width=1000, plot_height=1800, tooltips=TOOLTIPS,x_axis_label='Longitude',
                   y_axis_label='Latitude')
    plot2 = figure(x_range=(df['x'].min(), df['x'].max()), y_range=(df['y'].min(), df['y'].max()),
                   x_axis_type="mercator", y_axis_type="mercator", tools="pan,wheel_zoom,box_zoom,reset,save",
                   plot_width=1000, plot_height=1800, tooltips=TOOLTIPS[:6],x_axis_label='Longitude',
                   y_axis_label='Latitude')
    plot3 = figure(x_range=(df['x'].min(), df['x'].max()), y_range=(df['y'].min(), df['y'].max()),
                   x_axis_type="mercator", y_axis_type="mercator", tools="pan,wheel_zoom,box_zoom,reset,save",
                   plot_width=1000, plot_height=1800, tooltips=[("Mean Noise Pollution", "@image{0,0.0} dB")],
                   x_axis_label='Longitude',y_axis_label='Latitude')
    plot4 = figure(x_range=(df['x'].min(), df['x'].max()), y_range=(df['y'].min(), df['y'].max()),
                   x_axis_type="mercator", y_axis_type="mercator", tools="pan,wheel_zoom,box_zoom,reset,save",
                   plot_width=1000, plot_height=1800,x_axis_label='Longitude',y_axis_label='Latitude')
    # add basemap to each plot
    # add basemap to each plot
    plot1.add_tile(tile_provider)
    plot2.add_tile(tile_provider)
    plot3.add_tile(tile_provider)
    plot4.add_tile(tile_provider)
    # the view is defined to apply filters
    view = CDSView(source=source)
    # circles in plot 1
    plot1.circle(x="x", y="y", size=7, fill_color="navy", alpha=0.8, source=source,
                 view=view, nonselection_alpha=0)

    tab1 = Panel(child=plot1, title="Data Points")
    # circles with colors in plot 2
    plot2.circle(x="x", y="y", size=7, alpha=0.8, source=source,
                 view=view, nonselection_alpha=0, fill_color='colors',
                 line_width=.2, line_color='black')
    tab2 = Panel(child=plot2, title="Colored Scatter")
    # image in plot 3
    d = getMeshgrid(df, ngrid)  # function that provides data to be plotted by heatmap
    im = plot3.image(image=d, x=df['x'].min(), y=df['y'].min(), dw=df['x'].max() - df['x'].min(),
                     dh=df['y'].max()-df['y'].min(), palette="Spectral11", level="image",alpha=0.4)

    tab3 = Panel(child=plot3, title="Heat Map")
    im.level = 'overlay'  # make heatmap visible
    # hexbin in plot 4
    r, bins = plot4.hexbin(df['x'], df['y'], size=100, hover_color="pink", alpha=0.8, hover_alpha=0.6)
    circles = plot4.circle(x="x", y="y", size=2, fill_color="white", source=ColumnDataSource(data=df),
                           line_width=.2, nonselection_alpha=0, line_color='black')
    tab4 = Panel(child=plot4, title="Hex Bins")
    plot4.add_tools(HoverTool(  # data displayed in hexbin by means of hover tool
        tooltips=[("N° of data points", "@c")],
        mode="mouse", point_policy="follow_mouse", renderers=[r]
    ))
    # make bins visible
    bins.level = 'overlay'
    circles.level='overlay'

    n_data = df.shape[0]  # get number of data
    new_data = df.copy()  # this will be the data after the filters
    geo_select = pd.Series([True for i in range(n_data)])  # index boolean definition for spatial filtering

    def callback(attr, old, new):  # CALLBACK FOR BUTTONS
        global new_data
        global geo_select
        if button1.active == 0: # APPLY GEOSPATIAL FILTER

            # get filtering user preferences
            button1.active = None
            select_lu = multi_select.value
            start_dt = int(dt_slider.value[0]/1000)-3600
            end_dt = int(dt_slider.value[1]/1000)-3600
            start_t = int(t_slider.value[0]/1000)-3600
            end_t = int(t_slider.value[1]/1000)-3600
            min_np = range_slider.value[0]
            max_np = range_slider.value[1]
            msg.text,geo_select=isInside(draw_tool.renderers[0].data_source.data,df,n_data)

            if len(select_lu) == 0:
                selected_lu = ["Commercial", "Industrial", "Institutional","Mixed (Resi+Comm)", "PSP",
                               "Recreational", "Residential", "Transportation", "Vacant"]
            else:
                selected_lu = select_lu

            df2 = df[# do the filter
                (df['dt_ts'] >= start_dt) & (df['dt_ts'] <= end_dt) &
                (df['t_ts'] >= start_t) & (df['t_ts'] <= end_t) &
                (df['enp'] >= min_np) & (df['enp'] <= max_np) &
                (df['landuse'].isin(selected_lu)) &
                geo_select
            ]

            # update data source of plots
            new_data = df2.reset_index()
            source2 = ColumnDataSource(data=new_data)
            source.data = dict(source2.data)

            # new gridding for heatmap
            try:
                ngrid2 = int(
                    ngrid * np.min([(new_data['x'].max() - new_data['x'].min()) / (df['x'].max() - df['x'].min()),
                                    (new_data['y'].max() - new_data['y'].min()) / (df['y'].max() - df['y'].min())]))
            except:
                ngrid2 = 5
            try:
                im.data_source.data = {'image': getMeshgrid(new_data, ngrid2)}
                im.glyph.x = new_data['x'].min()
                im.glyph.y = new_data['y'].min()
                im.glyph.dw = new_data['x'].max() - new_data['x'].min()
                im.glyph.dh = new_data['y'].max() - new_data['y'].min()
            except: #empty heatmap if there are no enough filtered data
                im.data_source.data = {'image': [np.array([[0, 0], [0, 0]])]}
                im.glyph.x = 0
                im.glyph.y = 0
                im.glyph.dw = 1
                im.glyph.dh = 1

            # erase all polygons
            draw_tool.renderers[0].data_source.data = {'xs': [], 'ys': []}

        elif button2.active == 0: # RESET

            # all default values
            button2.active = None
            df2=df.copy()
            multi_select.value=[]
            dt_slider.value=(dt_min, dt_max)
            t_slider.value=(t_min, t_max)
            range_slider.value=(30,100)
            stats.text=''
            msg.text=''
            draw_tool.renderers[0].data_source.data={'xs':[],'ys':[]}
            geo_select = pd.Series([True for i in range(n_data)])
            new_data = df2.reset_index()
            source2 = ColumnDataSource(data=new_data)
            source.data = dict(source2.data)

            # default heatmap
            im.data_source.data = {'image': getMeshgrid(df, ngrid)}
            im.glyph.x = new_data['x'].min()
            im.glyph.y = new_data['y'].min()
            im.glyph.dw = new_data['x'].max() - new_data['x'].min()
            im.glyph.dh = new_data['y'].max() - new_data['y'].min()

        elif button3.active == 0:  # STATISTICS
            button3.active = None
            try: #statistics of filtered data
                stats_div = getStats(new_data)
            except: #statistics of the whole data
                stats_div = getStats(pd.DataFrame(source.data))
            stats.text = stats_div

    def callback2(attr, old, new): #CALLBACK FOR WIDGETS
        global new_data
        global geo_select

        # get filtering user preferences
        select_lu = multi_select.value
        start_dt = int(dt_slider.value[0] / 1000) - 3600
        end_dt = int(dt_slider.value[1] / 1000) - 3600
        start_t = int(t_slider.value[0] / 1000) - 3600
        end_t = int(t_slider.value[1] / 1000) - 3600
        min_np = range_slider.value[0]
        max_np = range_slider.value[1]

        if len(select_lu) == 0:
            selected_lu = ["Commercial", "Industrial", "Institutional", "Mixed (Resi+Comm)", "PSP",
                           "Recreational", "Residential", "Transportation", "Vacant"]
        else:
            selected_lu = select_lu
        try:
            geo_select=geo_select
        except:
            geo_select=pd.Series([True for i in range(n_data)])

        df2 = df[ # do the filter
            (df['dt_ts'] >= start_dt) & (df['dt_ts'] <= end_dt) &
            (df['t_ts'] >= start_t) & (df['t_ts'] <= end_t) &
            (df['enp'] >= min_np) & (df['enp'] <= max_np) &
            (df['landuse'].isin(selected_lu)) &
            geo_select
            ]

        # update data source of plots
        new_data = df2.reset_index()
        source2 = ColumnDataSource(data=new_data)
        source.data = dict(source2.data)

        # new gridding for heatmap
        try:
            ngrid2 = int(ngrid * np.min([(new_data['x'].max() - new_data['x'].min()) / (df['x'].max() - df['x'].min()),
                                        (new_data['y'].max() - new_data['y'].min()) / (df['y'].max() - df['y'].min())]))
        except:
            ngrid2=5
        try: #empty heatmap if there are no enough filtered data
            im.data_source.data = {'image': getMeshgrid(new_data, ngrid2)}
            im.glyph.x = new_data['x'].min()
            im.glyph.y = new_data['y'].min()
            im.glyph.dw = new_data['x'].max() - new_data['x'].min()
            im.glyph.dh = new_data['y'].max() - new_data['y'].min()
        except:
            im.data_source.data = {'image': [np.array([[0,0],[0,0]])]}
            im.glyph.x = 0
            im.glyph.y = 0
            im.glyph.dw = 1
            im.glyph.dh = 1

    # get default values of time and date
    dt_min = datetime.datetime.strptime(df['dt'].min(), '%d/%m/%Y')
    dt_max = datetime.datetime.strptime(df['dt'].max(), '%d/%m/%Y')
    max_ts = df['t_ts'].max()
    min_ts = df['t_ts'].min()
    t_min = datetime.datetime.fromtimestamp(min_ts)
    t_max = datetime.datetime.fromtimestamp(max_ts)

    # define widgets with their default values
    dt_slider = DateRangeSlider(start=dt_min, end=dt_max, value=(dt_min, dt_max),
                                step=24 * 60 * 60 * 1000, title="Date Range",
                                tooltips=False, width=300)
    
    t_slider = DateRangeSlider(title="Time Range: ", start=t_min, end=t_max,
                               value=(t_min, t_max), step=1000, format="%X",
                               tooltips=False)
    
    range_slider = RangeSlider(start=30, end=100, value=(30, 100),
                               step=.1, title="Noise Pollution Range [dB]")
    
    multi_select = MultiSelect(title="Land Use Classification:", value=[],
                               options=menu, height=170)

    # define draw tool for spatial filtering
    p1 = plot1.patches([], [], line_width=0, alpha=0.4)
    draw_tool = PolyDrawTool(renderers=[p1])
    draw_tool.renderers.level = 'overlay' #make drawings visible
    plot1.add_tools(draw_tool)
    plot1.toolbar.active_drag = draw_tool
    msg = Div(text=""" """, width=200, height=20)  # messages from spatial filtering function
    stats = Div(text=""" """, width=300, height=20)  # statistics
    empty_space = Div(text=""" """, width=30, height=20)
    tabs = Tabs(tabs=[tab1, tab2, tab3, tab4])  # all the plots are available in tabs

    # buttons definition
    button1 = RadioButtonGroup(labels=["Apply Spatial Filter"])
    button2 = RadioButtonGroup(labels=["Reset"])
    button3 = RadioButtonGroup(labels=["Get Statistics"])

    # callback on changes of widgets
    dt_slider.on_change('value', callback2)
    t_slider.on_change('value', callback2)
    range_slider.on_change('value', callback2)
    multi_select.on_change('value', callback2)

    # callbacks on clicks of buttons
    button1.on_change('active',callback)
    button2.on_change('active', callback)
    button3.on_change('active', callback)

    # layout of objects
    manager = column(dt_slider, t_slider, multi_select, range_slider,
                     button1,button2,button3, msg)
    dashboard = row(tabs, manager,empty_space, stats)

    # all the layout is added to the document
    doc.add_root(dashboard)
    doc.theme = Theme(filename = "theme.yaml") #style of the layout
    
    return(doc)

@app.route('/')
def home(): # home page
    return render_template('index.html')

@app.route('/maps', methods=['GET'])
def bkapp_page(): # application page
    script = server_document('http://localhost:5006/bkapp')
    css_resources = INLINE.render_css()
    
    return render_template(
        "embeded.html", 
        relative_urls=False,
        script=script, 
        template="Flask",
        css_resources=css_resources
        )

def bk_worker(): # funtion to define and start the server from the application script
    server = Server({'/bkapp': modify_doc}, io_loop=IOLoop(), 
                    allow_websocket_origin=["localhost:8000", "127.0.0.1:8000"])
    server.start()
    server.io_loop.start()

#start of the thread in which the server runs
Thread(target=bk_worker).start()


  
@app.route('/epicollect5')
def epicollect5():
    return render_template('epicollect5.html')

if __name__ == '__main__':
    app.run(port=8000)
    
