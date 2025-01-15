from datetime import datetime

from engine.engine import Engine
from flask import Flask, redirect, url_for, render_template, request, session
from stravalib.client import Client
import time

import helpers.mysql as database
import helpers.strava as strava

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

db = database.Database(app)
s = strava.Strava(app)

@app.route('/')
def home():
    return render_template('index.html', user='aaaa')

@app.route('/stats.png')
def stats_image():
    engine = Engine()
    return engine.render()


# def save_token_cache(athlete_id, token_data):
#     connection = mysql_server.connect()
#     cursor = connection.cursor()
#     cursor.execute(
#         "REPLACE INTO token_cache (athlete_id, access_token, refresh_token, expires_at) VALUES (%s, %s, %s, %s)",
#         (athlete_id, token_data['access_token'], token_data['refresh_token'], token_data['expires_at'])
#     )
#     connection.commit()
#     cursor.close()
#     connection.close()

# def load_token_cache(athlete_id):
#     connection = mysql_server.connect()
#     cursor = connection.cursor()
#     cursor.execute("SELECT access_token, refresh_token, expires_at FROM token_cache WHERE athlete_id = %s", (athlete_id,))
#     result = cursor.fetchone()
#     cursor.close()
#     connection.close()
#     if result:
#         return {"access_token": result[0], "refresh_token": result[1], "expires_at": result[2]}
#     return None

def refresh_token(client, athlete_id):
    token_data = db.load_token(athlete_id)
    if token_data and datetime.now() > datetime.fromtimestamp(int(token_data["expires_at"])):
        new_token_data = client.refresh_access_token(
            client_id=s.client_id,
            client_secret=s.client_secret,
            refresh_token=token_data["refresh_token"]
        )
        db.save_token_cache(athlete_id, new_token_data)
        return new_token_data
    return token_data

# def save_activities_cache(athlete_id, activities):
#     connection = mysql_server.connect()
#     cursor = connection.cursor()
#     cursor.execute("DELETE FROM activities_cache WHERE athlete_id = %s", (athlete_id,))
#     for activity in activities:
#         cursor.execute(
#             "INSERT INTO activities_cache (athlete_id, activity_id, name, distance, moving_time, start_date) VALUES (%s, %s, %s, %s, %s, %s)",
#             (athlete_id, activity['id'], activity['name'], activity['distance'], activity['moving_time'], activity['start_date'])
#         )
#     connection.commit()
#     cursor.close()
#     connection.close()
#
# def load_activities_cache(athlete_id):
#     connection = mysql_server.connect()
#     cursor = connection.cursor()
#     cursor.execute("SELECT activity_id, name, distance, moving_time, start_date FROM activities_cache WHERE athlete_id = %s", (athlete_id,))
#     activities = []
#     for row in cursor.fetchall():
#         activities.append({
#             "id": row[0],
#             "name": row[1],
#             "distance": row[2],
#             "moving_time": row[3],
#             "start_date": row[4],
#         })
#     cursor.close()
#     connection.close()
#     return activities

@app.route('/login')
def login():
    client = Client()
    auth_url = client.authorization_url(client_id=s.client_id,
                                        redirect_uri=s.redirect_uri,
                                        approval_prompt='auto',
                                        scope=['read_all', 'profile:read_all', 'activity:read_all']
                                        )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    client = Client()
    token_data = client.exchange_code_for_token(client_id=s.client_id, client_secret=s.client_secret, code=code)
    athlete = client.get_athlete()
    db.save_token_cache(athlete.id, token_data)
    session['athlete_id'] = athlete.id
    return redirect(url_for('activities'))

@app.route('/profile')
def profile():
    athlete_id = session.get('athlete_id')
    if not athlete_id:
        return redirect(url_for('login'))

    token_data = db.load_token(athlete_id)
    client = Client()

    if not token_data or datetime.now() > datetime.fromtimestamp(int(token_data["expires_at"])):
        token_data = refresh_token(client, athlete_id)

    client.access_token = token_data["access_token"]
    athlete = client.get_athlete()
    athlete_stats = client.get_athlete_stats(athlete.id)
    profile = db.load_profile(athlete.id)
    return render_template('profile.html', athlete_stats=athlete_stats, athlete=athlete, profile=profile)


@app.route('/activities')
def activities():
    athlete_id = session.get('athlete_id')
    if not athlete_id:
        return redirect(url_for('login'))

    token_data = db.load_token(athlete_id)
    client = Client()

    if not token_data or datetime.now() > datetime.fromtimestamp(int(token_data["expires_at"])):
        token_data = refresh_token(client, athlete_id)

    client.access_token = token_data["access_token"]

    activities = db.load_activities_cache(athlete_id)

    # Fetch new activities if needed
    last_cached_time = max([a['start_date'] for a in activities], default=None)
    new_activities = []

    for activity in client.get_activities(after=last_cached_time):
        new_activities.append({
            "activity_id": activity.id,
            "athlete_id": activity.athlete.id,
            "name": activity.name,
            "distance": activity.distance,
            "type": activity.type.root,
            "sport_type": activity.sport_type.root,
            "moving_time": activity.moving_time,
            "start_date": str(activity.start_date),
        })

    activities.extend(new_activities)
    # db.save_activities_cache(athlete_id, activities)

    return render_template('profile.html', activities=activities)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
