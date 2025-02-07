from flask import send_from_directory
import os

import json
import logging
from datetime import datetime
from functools import wraps

import flask.wrappers
from flask import Flask, redirect, url_for, render_template, request, session, jsonify
from stravalib.client import Client

import helpers.mysql as database
import helpers.strava as strava
from engine.engine import Engine
from engine.render_mode import RenderMode

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app.config.logger = logging.getLogger(__name__)

app.secret_key = 'your_secret_key'  # Replace with a secure secret key
app.config.db = database.Database(app)
app.config.strava = strava.Strava(app)
app.config.client = Client()
app.config.session_athlete_id = None
app.config.session_access_token = None
app.config.logger.info('== Start app ==')


def auth_route(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_result = auth_strava()
        if isinstance(auth_result, flask.Response):
            session['next_url'] = request.url
            return auth_result
        return f(*args, **kwargs)

    return decorated_function


def convert_token_data_to_datetime(token_data) -> datetime:
    """
    Converts token expiration timestamp to datetime object.
    Args:
        token_data: Dictionary containing token information including expires_at timestamp
    Returns:
        datetime: Token expiration datetime
    """
    return datetime.fromtimestamp(int(token_data["expires_at"]))


def refresh_token():
    """
    Refreshes the Strava access token if expired.
    Returns the new token data if refreshed, or existing token data if still valid.
    """
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


# Returns true
def auth_strava() -> flask.Response | bool:
    """
    Authenticates the Strava session. Checks if user is logged in and token is valid.
    Returns True if authentication successful, or redirects to Strava authorization if not authorized.
    """
    app.config.session_athlete_id = session.get('athlete_id')
    if not app.config.session_athlete_id:
        app.config.logger.warning("Not authorized (no athlete)! Login needed")
        return redirect(url_for('authorize_strava'))
    token_data = app.config.db.load_token(app.config.session_athlete_id)
    if not token_data:
        app.config.logger.warning("Not authorized (no token)! Login needed")
        return redirect(url_for('authorize_strava'))
    app.config.session_access_token_expires = convert_token_data_to_datetime(token_data)

    if not token_data or datetime.now() > app.config.session_access_token_expires:
        token_data = refresh_token()
    app.config.client.access_token = token_data["access_token"]
    app.config.session_access_token = token_data["access_token"]
    return True


@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@app.route('/engine/<path:filename>')
def serve_engine_html(filename):
    """
    Serves static files from the /engine/html directory.
    """
    engine_html_dir: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'engine', 'html')
    return send_from_directory(engine_html_dir, filename)

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
@auth_route
def stats_image():
    engine = Engine(app)
    return engine.render()

@app.route('/stats_html')
@auth_route
def stats_html():
    engine = Engine(app)
    engine.render_html(RenderMode.HTML)
    return flask.Response(engine.html_data, mimetype='text/html')


@app.route('/authorize_strava')
def authorize_strava():
    """
    Initiates Strava OAuth2 authorization flow by redirecting user to Strava login page.
    Requests read access for user profile and activity data.
    Returns:
        Response: Redirect to Strava authorization URL
    """
    auth_url = app.config.client.authorization_url(client_id=app.config.strava.client_id,
                                                   redirect_uri=app.config.strava.redirect_uri,
                                                   approval_prompt='auto',
                                                   scope=['read_all', 'profile:read_all', 'activity:read_all']
                                                   )
    return redirect(auth_url)


@app.route('/callback')
def callback():
    """
    Handles OAuth callback from Strava. Exchanges authorization code for access token,
    stores token in database, and initiates activity refresh.
    Returns:
        Response: Redirect to original requested URL or main page
    """
    next_url = session.pop('next_url', url_for('main'))
    code = request.args.get('code')
    token_data = app.config.client.exchange_code_for_token(client_id=app.config.strava.client_id,
                                                           client_secret=app.config.strava.client_secret, code=code)
    athlete = app.config.client.get_athlete()
    app.config.db.save_token_cache(athlete.id, token_data)
    session['athlete_id'] = athlete.id
    app.config.session_athlete_id = athlete.id
    return redirect(next_url)


@app.route('/profile')
@auth_route
def profile():
    """
    Displays user profile page with athlete information and stats.
    Requires authentication via @auth_route decorator.
    Returns:
        Response: Rendered profile template with athlete data
    """
    app.config.logger.info("profile()")
    athlete_info = app.config.client.get_athlete()
    app.config.logger.debug("profile / athlete: " + str(athlete_info))
    athlete_stats = app.config.client.get_athlete_stats(athlete_info.id)
    profile_info = app.config.db.load_profile(athlete_info.id)
    return render_template('profile.html', athlete_stats=athlete_stats, athlete=athlete_info, profile=profile_info)



@app.route('/activities_js')
@auth_route
def activities_js():
    return render_template('activities_js.html')


@app.route('/api/activities.json')
def api_activities():
    app.config.logger.info("api_activities()")
    auth_strava()
    loaded_activities: list = app.config.db.load_activities_cache(app.config.session_athlete_id)

    def convert_start_date(activity):
        activity["start_date"] = datetime.fromtimestamp(float(activity["start_date"])).strftime('%Y-%m-%d %H:%M:%S')
        return activity  # Use map to apply the conversion

    loaded_activities = list(map(convert_start_date, loaded_activities))
    cached_activities = {"data": loaded_activities}
    return cached_activities

###

@app.route('/refresh_activities')
@auth_route
def refresh_activities_page():
    """
    Renders the refresh activities page with a loader.
    """
    return render_template('refresh_activities.html')


def refresh_activities_with_progress(athlete_id):
    app.config.logger.info("refresh_activities_with_progress()")
    yield {"progress": 10, "message": "Logging to Strava."}
    # Use athlete_id instead of session data
    yield {"progress": 20, "message": "Loaded cached activities."}
    cached_activities = app.config.db.load_activities_cache(athlete_id)
    yield {"progress": 20, "message": f"Cached activities loaded (${len(cached_activities)})."}

    last_cached_size: int = 0
    new_cached_size: int = 0

    new_activities = []
    fresh_activities = []
    if not cached_activities:
        app.config.logger.info("cached_activities: NONE FOUND")
        yield {"progress": 50, "message": "Fetching all your activities from Strava. It may take some time, do not close this page"}
        fresh_activities = app.config.client.get_activities()
        yield {"progress": 50, "message": "All activities from Strava successfully fetched."}
    else:
        last_cached_size = len(cached_activities)
        last_cached_timestamp: float = max([a['start_date'] for a in cached_activities], default=None)
        app.config.logger.info("last (timestamp):" + str(last_cached_timestamp))
        last_cached_time = datetime.fromtimestamp(float(last_cached_timestamp))
        app.config.logger.info("last (datetime):" + str(last_cached_time))
        fresh_activities = app.config.client.get_activities(after=last_cached_time)
        yield {"progress": 50, "message": f"All new activities fetched from Strava"}

    for activity in fresh_activities:
        new_activities.append({
            "activity_id": activity.id,
            "athlete_id": activity.athlete.id,
            "name": activity.name,
            "distance": activity.distance,
            "total_elevation_gain": activity.total_elevation_gain,
            "type": activity.type.root,
            "sport_type": activity.sport_type.root,
            "moving_time": activity.moving_time,
            "start_date": activity.start_date.timestamp(),
        })

    new_cached_size: int = len(cached_activities)
    yield {"progress": 70, "message": f"Total new activities ${new_cached_size - last_cached_size}."}

    cached_activities.extend(new_activities)
    cached_activities.sort(key=lambda x: float(x['start_date']), reverse=True)
    app.config.db.save_activities_cache(app.config.session_athlete_id, new_activities)

    # Re-calculate ytd_ride_current
    current_year = datetime.now().year
    ride_types = ['Ride']  # Include all ride types from Strava
    ytd_ride_current = sum(
        activity['distance'] for activity in cached_activities
        if datetime.fromtimestamp(float(activity['start_date'])).year == current_year and activity['type'] in ride_types
    )
    ytd_ride_elev_current = sum(
        activity['total_elevation_gain'] for activity in cached_activities
        if datetime.fromtimestamp(float(activity['start_date'])).year == current_year
        and activity['type'] in ride_types
        and activity['total_elevation_gain'] is not None
    )
    app.config.db.save_athlete_stats(app.config.session_athlete_id, ytd_ride_current, ytd_ride_elev_current)

    yield {"progress": 100, "message": f"Completed. Total {new_cached_size} activities, {new_cached_size - last_cached_size} newly fetched."}

##
@app.route('/api/refresh_activities', methods=['GET'])
@auth_route
def api_refresh_activities():
    athlete_id = session.get('athlete_id')

    def generate():
        try:
            for progress_update in refresh_activities_with_progress(athlete_id):
                # Convert dictionary to JSON string and properly format for SSE
                if isinstance(progress_update, dict):
                    yield f"data: {json.dumps(progress_update)}\n\n"
                else:
                    # Handle case where progress_update is already a Response object
                    yield f"data: {json.dumps(progress_update.json)}\n\n"
        except Exception as e:
            app.config.logger.error(f"Error refreshing activities: {e}, {e.__context__}")
            yield f"data: {json.dumps({'progress': 100, 'message': 'Error occurred'})}\n\n"

    return flask.Response(generate(), mimetype='text/event-stream')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
