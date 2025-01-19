
from engine.engine import Engine
from flask import Flask, redirect, url_for, render_template, request, session
from stravalib.client import Client
from datetime import datetime, date

import helpers.mysql as database
import helpers.strava as strava

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key
app.config.db = database.Database(app)
app.config.strava = strava.Strava(app)
client: Client = Client()

athlete_id: int | None = None
token_date: dict | None = None

# def auth(func):
#     def wrapper(*args, **kwargs):
#         athlete_id = session.get('athlete_id')
#         if not athlete_id:
#             return redirect(url_for('login'))
#
#         token_data = db.load_token(athlete_id)
#
#         if not token_data or datetime.now() > datetime.fromtimestamp(int(token_data["expires_at"])):
#             token_data = refresh_token(client, athlete_id)
#
#         client.access_token = token_data["access_token"]
#         return func(*args, **kwargs)
#     return wrapper

def auth():
    athlete_id = session.get('athlete_id')

    if not athlete_id:
        return redirect(url_for('login'))
    app.logger.warning("AUTH =============== athlete_id: " + str(athlete_id))
    token_data = app.config.db.load_token(athlete_id)
    app.logger.warning("AUTH =============== token_data: " + str(token_data))

    if not token_data or datetime.now() > datetime.fromtimestamp(int(str(token_data["expires_at"]))):
        token_data = refresh_token(client, athlete_id)

    client.access_token = token_data["access_token"]


@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}
@app.route('/')
def main():
    return render_template('index.html', user='aaaa')

@app.route('/dummy.html')
def dummy():
    return render_template('dummy.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/stats.png')
#@auth
def stats_image():
    auth()
    engine = Engine(app)
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
    token_data = app.config.db.load_token(athlete_id)
    if token_data and datetime.now() > datetime.fromtimestamp(int(token_data["expires_at"])):
        new_token_data = client.refresh_access_token(
            client_id=app.config.strava.client_id,
            client_secret=app.config.strava.client_secret,
            refresh_token=token_data["refresh_token"]
        )
        app.config.db.save_token_cache(athlete_id, new_token_data)
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
    auth_url = client.authorization_url(client_id=app.config.strava.client_id,
                                        redirect_uri=app.config.strava.redirect_uri,
                                        approval_prompt='auto',
                                        scope=['read_all', 'profile:read_all', 'activity:read_all']
                                        )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_data = client.exchange_code_for_token(client_id=app.config.strava.client_id, client_secret=app.config.strava.client_secret, code=code)
    athlete = client.get_athlete()
    app.config.db.save_token_cache(athlete.id, token_data)
    session['athlete_id'] = athlete.id
    return redirect(url_for('activities'))



@app.route('/profile')
#@auth
def profile():
    auth()
    athlete_info = client.get_athlete()
    app.logger.warning("profile / athlete: " + str(athlete_info))

    athlete_stats = client.get_athlete_stats(athlete_info.id)
    profile_info = app.config.db.load_profile(athlete_info.id)
    return render_template('profile.html', athlete_stats=athlete_stats, athlete=athlete_info, profile=profile_info)


@app.route('/activities')
#@auth
def activities():
    auth()
    cached_activities = app.config.db.load_activities_cache(athlete_id)

    # Fetch new activities if needed
    last_cached_time = max([a['start_date'] for a in cached_activities], default=None)

    last_cached_time_date = datetime.fromisoformat(last_cached_time)
    app.logger.warning("last:" + str(last_cached_time))
    app.logger.warning("timestamp:" + str(last_cached_time))

    new_activities = []
    for activity in client.get_activities(after=last_cached_time_date):
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
    app.logger.warning("loaded:" + str(new_activities))

    cached_activities.extend(new_activities)
    cached_activities.sort(key=lambda x: x['start_date'], reverse=True)
    app.config.db.save_activities_cache(athlete_id, new_activities)

    return render_template('activities.html', activities=cached_activities)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
