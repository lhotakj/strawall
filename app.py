from fontTools.misc.cython import returns

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
app.config.client = Client()
app.config.session_athlete_id = None
app.config.session_access_token = None

def convert_token_data_to_datetime(token_data) -> datetime:
    return datetime.fromtimestamp(int(token_data["expires_at"]))

def refresh_token():
    token_data = app.config.db.load_token(app.config.session_athlete_id)
    if token_data and datetime.now() > convert_token_data_to_datetime(token_data):
        new_token_data = app.config.client.refresh_access_token(
            client_id=app.config.strava.client_id,
            client_secret=app.config.strava.client_secret,
            refresh_token=token_data["refresh_token"]
        )
        app.config.db.save_token_cache(app.config.session_athlete_id, new_token_data)
        return new_token_data
    return token_data

def auth_application():
    if not session.__contains__('athlete_id'):
        return redirect(url_for('authorize_strava'))

def auth_strava():
    app.config.session_athlete_id = session.get('athlete_id')
    if not app.config.session_athlete_id:
        return redirect(url_for('authorize_strava'))
    token_data = app.config.db.load_token(app.config.session_athlete_id)
    app.config.session_access_token_expires = convert_token_data_to_datetime(token_data)

    if not token_data or datetime.now() > app.config.session_access_token_expires:
        token_data = refresh_token()
    app.config.client.access_token = token_data["access_token"]
    app.config.session_access_token = token_data["access_token"]


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
    auth_strava()
    engine = Engine(app)
    return engine.render()


@app.route('/authorize_strava')
def authorize_strava():
    auth_url = app.config.client.authorization_url(client_id=app.config.strava.client_id,
                                        redirect_uri=app.config.strava.redirect_uri,
                                        approval_prompt='auto',
                                        scope=['read_all', 'profile:read_all', 'activity:read_all']
                                        )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_data = app.config.client.exchange_code_for_token(client_id=app.config.strava.client_id, client_secret=app.config.strava.client_secret, code=code)
    athlete = app.config.client.get_athlete()
    app.config.db.save_token_cache(athlete.id, token_data)
    session['athlete_id'] = athlete.id
    app.config.session_athlete_id = athlete.id
    return redirect(url_for('activities'))

@app.route('/profile')
def profile():
    auth_strava()
    athlete_info = app.config.client.get_athlete()
    app.logger.warning("profile / athlete: " + str(athlete_info))
    athlete_stats = app.config.client.get_athlete_stats(athlete_info.id)
    profile_info = app.config.db.load_profile(athlete_info.id)
    return render_template('profile.html', athlete_stats=athlete_stats, athlete=athlete_info, profile=profile_info)


def refresh_activities():
    auth_strava()
    cached_activities = app.config.db.load_activities_cache(app.config.session_athlete_id)
    # Fetch new activities if needed
    last_cached_time = max([a['start_date'] for a in cached_activities], default=None)
    last_cached_time_date = datetime.fromisoformat(last_cached_time)
    app.logger.warning("last:" + str(last_cached_time))
    app.logger.warning("timestamp:" + str(last_cached_time))

    new_activities = []
    for activity in app.config.client.get_activities(after=last_cached_time_date):
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
    # app.logger.warning("loaded:" + str(new_activities))
    cached_activities.extend(new_activities)
    cached_activities.sort(key=lambda x: x['start_date'], reverse=True)
    app.config.db.save_activities_cache(app.config.session_athlete_id, new_activities)


@app.route('/activities_js')
def activities_js():
    return render_template('activities_js.html')

@app.route('/api/activities.json')
def api_activities():
    auth_strava()
    cached_activities = {"data": app.config.db.load_activities_cache(app.config.session_athlete_id)}

    return cached_activities


@app.route('/activities')
def activities():
    auth_strava()
    cached_activities = app.config.db.load_activities_cache(app.config.session_athlete_id)
    # Fetch new activities if needed
    last_cached_time = max([a['start_date'] for a in cached_activities], default=None)
    last_cached_time_date = datetime.fromisoformat(last_cached_time)
    app.logger.warning("last:" + str(last_cached_time))
    app.logger.warning("timestamp:" + str(last_cached_time))

    new_activities = []
    for activity in app.config.client.get_activities(after=last_cached_time_date):
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
    cached_activities.extend(new_activities)
    cached_activities.sort(key=lambda x: x['start_date'], reverse=True)
    app.config.db.save_activities_cache(app.config.session_athlete_id, new_activities)
    return render_template('activities.html', activities=cached_activities)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
