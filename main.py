import dash
import dash_html_components as html
import dash_core_components as dcc
import requests
import bs4
import pandas as pd
import numpy as np
import os
from geopy.geocoders import Nominatim
from plotly import graph_objs as go
import cufflinks as cf
cf.go_offline()
import plotly
import json


r=requests.get('https://www.mohfw.gov.in')

mohfw=r.content



soup = bs4.BeautifulSoup(r.content, 'html5lib') 

table = soup.findAll(lambda tag: tag.name=='table') 
#rows = table.findAll(lambda tag: tag.name=='tr')

intended_table = table[-1]
rows = intended_table.findAll(lambda tag: tag.name=='tr')

Rows=[]
for idx,row in enumerate(rows):
    if not idx:
        Rows.append(list(map(lambda item:item.text,row.findAll(lambda tag: tag.name=='th'))))
    else:
        Rows.append(list(map(lambda item:item.text,row.findAll(lambda tag: tag.name=='td'))))


df = pd.DataFrame(data=Rows[1:-1],columns=Rows[0])
df.drop(['S. No.'],axis=1,inplace=True)
df['Total Confirmed cases (Indian National)']=df['Total Confirmed cases (Indian National)'].str.strip('#').astype(int)
df['Total Confirmed cases ( Foreign National )']=df['Total Confirmed cases ( Foreign National )'].str.strip('#').astype(int)
df['Cured/Discharged/Migrated']=df['Cured/Discharged/Migrated'].str.strip('#').astype(int)
df['Death']=df['Death'].str.strip('#').astype(int)

df_last = ['Total',df['Total Confirmed cases (Indian National)'].sum(),df['Total Confirmed cases ( Foreign National )'].sum(),df['Cured/Discharged/Migrated'].sum(),df['Death'].sum()]
df=df.append(pd.Series(df_last,index=df.columns),ignore_index=True)



geolocator = Nominatim(user_agent="dipmukherg")

Lat=[]
Lon=[]
Location_Sentiment=[]
for idx,loc in enumerate(df['Name of State / UT']):
    try:
        location = geolocator.geocode(loc,timeout=4)
        Lat.append(location.latitude)
        Lon.append(location.longitude)
        Location_Sentiment.append(Sentiments[idx])
    except:
        continue


# sched = BackgroundScheduler(daemon=True)
# df=sched.add_job(get_dataframe,'interval',minutes=30)
# sched.start()
# df=get_dataframe()
df['Latitude']=Lat
df['Longitude']=Lon




mapbox_access_token = '''pk.eyJ1IjoiZGlwbXVraGVyZyIsImEiOiJjazB5d2x2NDYwOGkzM25vN3loYTVvYWxnIn0.Vo20HKeddzOjEKhPGcbN0g'''
# Coordinates = list(map(lambda tweet:tweet.coordinates, Tweets_Status))
# Location_Shared = len(list(filter(lambda x:bool(x),Coordinates)))
# coordinates=list(map(lambda ls:ls['coordinates'],(filter(lambda x:bool(x),Coordinates))))
lats = list(map(lambda x:round(x,2),df.ix[:22,'Latitude']))
lons = list(map(lambda x:round(x,2),df.ix[:22,'Longitude']))
coordinate_counts = df.ix[:22,'Total Confirmed cases (Indian National)']
state = df.ix[:22,'Name of State / UT']

df_daily = pd.read_csv('COVID_Daily.csv')

import datetime

today=datetime.date.today().strftime('%d-%m-%Y')
today_total=df.iloc[-1,1]+df.iloc[-1,2]

if df_daily.iloc[-1,0]!=today:
    df_daily=df_daily.append(pd.Series([today,today_total],index=df_daily.columns),ignore_index=True)
    df_daily.to_csv('COVID_Daily.csv',index=False)
elif df_daily.iloc[-1,1]!=today_total:
    df_daily.iloc[-1,1]=today_total
    df_daily.to_csv('COVID_Daily.csv',index=False)
else:
    pass

df_daily['Date']=pd.to_datetime(df_daily['Date'],format='%d-%m-%Y')
trace_curve_1 =  go.Scatter(name='Daywise Status', x=df_daily['Date'], y=df_daily['Total_Cases'],mode='lines')

df_daily['Daily_New_Case']=(df_daily['Total_Cases'].diff()).fillna(df_daily.iloc[0,1]).astype(int)
trace_curve_2=go.Bar(name='Daily New Case', x=df_daily['Date'], y=df_daily['Daily_New_Case'])




app = dash.Dash()

trace_mapbox = go.Scattermapbox(
        name='',
        lat=lats,
        lon=lons,
        text=state,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=20,
            color='rgb(0, 0, 0)',
            opacity=0.7
        ),
        showlegend=False,
#         hoverinfo='lat+lon+text',
#         hovertext=coordinate_counts,
#         hovertemplate='%{text} %{hovertext}',
        
            
        )

trace_2 = go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode='markers',
        text=state,
        marker_color=coordinate_counts,
        marker_showscale = True,
        marker=dict(
            size=15,
            opacity=0.7,
        ),
        hovertext=coordinate_counts,
        showlegend=False,
        hovertemplate='%{text} %{hovertext}')

app.layout = html.Div([

    html.Div([
        html.H2("COVID-19 Status India"),
        html.Img(src='/assets/corona.jpg')
    ],
    className='banner'),

    html.Div([
        html.H4("Total Confirmed Cases (Indian National): {}          ".format(df.iloc[-1,1])+"\t\t\t\tTotal Confirmed cases ( Foreign National ): {}".format(df.iloc[-1,2])),
        html.H4("Cured/Discharged/Migrated: {}          ".format(df.iloc[-1,3])+"\t\t\t\tTotal_Death: {}".format(df.iloc[-1,4])),
    ]),

    html.Div(
        [   
            html.Div([
                dcc.Graph(
                    id='MapBox',
                    figure={
                        "data":[trace_mapbox,trace_2],
                        "layout":{
                            'title':'State Wise Picture',
                            'hovermode':'closest',
                            'mapbox':go.layout.Mapbox(
                                accesstoken=mapbox_access_token,
                                bearing=0,
                                center=go.layout.mapbox.Center(
                                    lat=22.97,
                                    lon=78.65
                                ),
                            pitch=0,
                            zoom=2.6
                            ),
                        'width':500,
                        'height':500,
                        },
                        
                        
                    },
                className='six columns'
                )
            ]),
            html.Div([dcc.Graph(
                    id='Curve_1',
                    figure={
                        "data":[trace_curve_1],
                        "layout":{
                            'title':'Day Wise Status',
                            'hovermode':'closest',
                        'width':500,
                        'height':500,
                        },
                        
                        
                    },
                className='six columns'
                )
            ]),
            html.Div([dcc.Graph(
                    id='Curve_2',
                    figure={
                        "data":[trace_curve_2],
                        "layout":{
                            'title':'Daily New Case Count',
                            'hovermode':'closest',
                        'width':1000,
                        'height':500,
                        },
                        
                        
                    },
                
                )
            ])
        ]
    )
    
]
)

app.css.append_css({
    "external_url":'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

if __name__=="__main__":
    app.run_server(debug=True)
