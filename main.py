import datetime

from flask import Flask, redirect, render_template, request, session
from json import loads
import sqlite3
import sys
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


API_KEY = "13e7e9ea1a500f91f7410aff224e1bd4"


WEATHER_MAIN = {
    'Rain': 'Дождь',
    'Thunderstorm': 'Гроза',
    'Drizzle': 'Морось',
    'Snow': 'Снег',
    'Mist': 'Туман',
    'Smoke': 'Дым',
    'Haze': 'Дымка',
    'Dust': 'Пылевая буря',
    'Fog': 'Туман',
    'Sand': 'Песчаная буря',
    'Ash': 'Пепел',
    'Squall': 'Шквал',
    'Tornado': 'Ураган',
    'Clear': 'Ясно',
    'Clouds': 'Облачно'
}
TOWNS = [
    'Москва',
    'Санкт-Петербург',
    'Новосибирск',
    'Екатеринбург',
    'Казань',
    'Нижний Новгород',
    'Омск',
    'Челябинск'
]


def parseWeather(json):
    weather = WEATHER_MAIN[json['weather'][0]['main']]
    description = json['weather'][0]['description']
    description = description[0].upper() + description[1:len(description)]
    dt = datetime.datetime.fromtimestamp(json['dt'])
    temp = {
        'temp': int(json['main']['temp'] - 273),
        'feels_like': int(json['main']['feels_like'] - 273)
    }
    pressure = round(json['main']['pressure'] / 1.333224, 2)
    humidity = json['main']['humidity']
    icon = f"https://openweathermap.org/img/wn/{json['weather'][0]['icon']}@2x.png"

    data = {
        'dt': dt,
        'main': weather,
        'description': description,
        'temp': temp,
        'pressure': pressure,
        'humidity': humidity,
        'icon': icon,
        'time': dt.time().strftime('%H:%M:%S'),
        'day': dt.date().strftime('%d.%m.%Y')
    }
    return data


def getData(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&lang=ru"
    json = loads(requests.get(url).text)
    return parseWeather(json)


def getForecast(city):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&lang=ru"
    json = loads(requests.get(url).text)
    days = dict()
    counter = 0
    for day in json['list']:
        data = parseWeather(day)
        data['active'] = ''
        if data['day'] not in days:
            days[data['day']] = []
            data['active'] = 'active'
        data['id'] = counter
        days[data['day']].append(data)
        counter += 1

    return days


@app.route('/')
def index():
    with sqlite3.connect("visits.db") as con:
        cur = con.cursor()
        visit = False
        if 'visited' in session:
            if session['visited'] != datetime.datetime.now().strftime('%d.%m.%Y'):
                session['visited'] = datetime.datetime.now().strftime('%d.%m.%Y')
                visit = True
        else:
            session['visited'] = datetime.datetime.now().strftime('%d.%m.%Y')
            visit = True
        if visit:
            sql = f"""
            SELECT id FROM visits WHERE date = '{datetime.datetime.now().strftime('%d.%m.%Y')}'
            """
            result = cur.execute(sql).fetchall()
            print(result)
            if len(result) == 0:
                sql = f"""
                INSERT INTO visits (date) VALUES ('{datetime.datetime.now().strftime('%d.%m.%Y')}')
                """
                cur.execute(sql)

            sql = f"""
            UPDATE visits 
            SET visits = visits + 1
            WHERE date = '{datetime.datetime.now().strftime('%d.%m.%Y')}'
            """

            cur.execute(sql)
            con.commit()

        sql = f"""
               SELECT visits FROM visits WHERE date = '{datetime.datetime.now().strftime('%d.%m.%Y')}'
               """
        visits = 0
        result = cur.execute(sql).fetchall()
        if result:
            visits = result[0][0]
    return render_template('index.html', visits=visits)


@app.route('/weather', methods=['GET'])
def getWeather():
    city = request.args['city']
    try:
        weather = getData(city)
        forecast = getForecast(city)
        return render_template('weather.html', weather=weather, city=city, forecast=forecast)
    except Exception:
        return render_template('sorry.html', city=city)


@app.route('/towns')
def getTowns():
    cities = []
    for city in TOWNS:
        cities.append({
            "name": city,
            "weather": getData(city),
        })
    return render_template('towns.html', cities=cities)


def main():
    app.run()


main()
