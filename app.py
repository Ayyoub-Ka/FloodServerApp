from flask import Flask, render_template, redirect, url_for ,Response,make_response
from flask import request,jsonify
from requests import post
import requests
import pandas as pd
from pandas import json_normalize
from datetime import datetime, timedelta
import vincent
import random
import io
import json
import mpld3
from mpld3 import plugins
from matplotlib import pyplot as plt
import base64

app = Flask(__name__)

api_root = "http://environment.data.gov.uk/flood-monitoring";

locations =[];
stations=[]
@app.route("/" )
def home():
    stations = getDataX()
    locations = getLocations(stations)
    return render_template("index.html", title="Map", locations=json.dumps(locations))


@app.route('/', methods=['POST'])
def getSelectedStation():
    output = request.get_json()
    print(output)
    code=getHtmlPlot(output)
    #return redirect(url_for('/plot.png', result_id=output))
    #return  make_response(jsonify(plot_png(1)), 200)
    return  make_response(plot_png64(), 200)

def getDataX():
    # if (stations or stations!=[]) :
    #     print('data existe')
    #     return
    # print('getting data')
    response = requests.get(api_root+"/id/stations")
    stations_Data = response.json()
    stations_List = json_normalize(stations_Data, 'items')
    return stations_List.dropna(subset=["lat", "long", "stationReference"])


def getLocations(stations):
    filtered_stations = stations[stations[[
        'lat', 'long', 'notation']].notnull().all(1)]
    return filtered_stations[['lat', 'long', 'notation']].to_dict("records")

def getPlot(id):
    df ,_= preparePlot(id)
    line = vincent.Line(df)
    line.axis_titles(x='dateTime', y='value')
    line.legend(title='Categories')
    return line.to_json()

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

def preparePlot(id):
    if id=='':
        return 

    last_24hour_date_time = (datetime.now() - timedelta(hours = 24)).strftime("%Y-%m-%dT%H:%M:%SZ")

    stationReading = api_root+"/id/stations/"+id+"/readings?since="+last_24hour_date_time
    stationMeasure=api_root+"/id/stations/"+id+"/measures"
    response = requests.get(stationReading)
    if response. status_code != 200:
        return
    stationData=response.json()
    response = requests.get(stationMeasure)
    if response. status_code != 200:
        return
    stationMeasures=response.json()
    sd = json_normalize(stationData, 'items')
    sm = json_normalize(stationMeasures, 'items')
    df=sd.copy()
    if df.empty:
        return
    df['dateTime']=pd.to_datetime(df['dateTime'])
    # get the measure name
    #parameter=sm.loc[sm['@id'] == 30000, 'parameterName'].iloc[0]
    #df['measure']=df['measure'].map(lambda m: m[m.rfind('/'):] ).map(lambda m: m[m.find('-')+1:])
    df['measure']=df['measure'].map(lambda m:sm.loc[sm['@id'] == m, ['parameterName','qualifier']].iloc[0].str.cat(sep='-'))
    x=df.pivot(index='dateTime', columns='measure', values='value').reset_index()
    return df, x

def create_figure():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    xs = range(100)
    ys = [random.randint(1, 50) for x in xs]
    axis.plot(xs, ys)
    return fig

def plot_png(result_id):
    fig = create_figure()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')



def plot_png64():
    my_stringIObytes = io.BytesIO()
    create_figure().savefig(my_stringIObytes, format='jpg')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read())
    return my_base64_jpgData

def getHtmlPlot(id):
    _,x =preparePlot(id)
    fig= plt.figure()
    #ax = fig.add_subplot(1,1,1)
    ax=x.plot(x='dateTime', fontsize=15)
    # Additional customizations
    ax.set_xlabel('Date')
    ax.legend(fontsize=14)
    return mpld3.fig_to_html(fig)



