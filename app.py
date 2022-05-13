from flask import Flask, render_template, Response,make_response
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
import altair as alt


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
    station_id = request.get_json()
    return  make_response(getAltiarChar(station_id), 200)

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


def prepareDateForPlot(id):
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
    return df

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


def getAltiarChar(station_id):
    df= prepareDateForPlot(station_id)
    pl=alt.Chart(df).mark_line().encode(
    x='dateTime',
    y='value',
    color='measure',
    strokeDash='measure')
    pl.properties(width=200, height=150)
    return pl.to_json()









