
from datetime import datetime
from .strava_goals import StatsType as strava_goals
import os

from _decimal import Decimal
from flask import Flask


# from stravalib import Client
# from stravalib.model import Athlete
# from stravalib.protocol import AccessInfo
# from stravalib.strava_model import ActivityStats, SummaryActivity



class Strava:
    client_id: int
    client_secret: str
    redirect_uri: str
    app: Flask

    def __init__(self, app: Flask):
        self.client_id = int(os.environ.get("STRAVA_CLIENT_ID"))
        self.client_secret = os.environ.get("STRAVA_CLIENT_SECRET")
        self.redirect_uri = 'http://home:5000/callback'
        self.app = app
        if not self.client_id:
            self.app.config.logger.error("STRAVA_CLIENT_ID environment variable not set")
            return
        if not self.client_secret:
            self.app.config.logger.error("STRAVA_CLIENT_SECRET environment variable not set")
            return


    def refresh_activities_with_progress(self, athlete_id):
        self.app.config.logger.info("refresh_activities_with_progress()")
        yield {"progress": 10, "message": "Logging to Strava."}
        # Use athlete_id instead of session data
        yield {"progress": 20, "message": "Loading all activities. This may take some time"}
        cached_activities = self.app.config.db.load_activities_cache(athlete_id)
        yield {"progress": 30, "message": f"Cached activities loaded ({len(cached_activities)})."}

        last_cached_size: int = 0
        new_cached_size: int = 0

        new_activities = []
        fresh_activities = []
        if not cached_activities:
            self.app.config.logger.info("cached_activities: NONE FOUND")
            yield {"progress": 40, "message": "Fetching all your activities from Strava. It may take some time, do not close this page"}
            fresh_activities = self.app.config.client.get_activities()
            yield {"progress": 50, "message": "All activities from Strava successfully fetched."}
        else:
            yield {"progress": 50, "message": "Incremental fetching activities from Strava. . It may take some time, do not close this page"}
            last_cached_size = len(cached_activities)
            last_cached_timestamp: float = max([a['start_date'] for a in cached_activities], default=None)
            self.app.config.logger.info("last (timestamp):" + str(last_cached_timestamp))
            last_cached_time = datetime.fromtimestamp(float(last_cached_timestamp))
            self.app.config.logger.info("last (datetime):" + str(last_cached_time))
            fresh_activities = self.app.config.client.get_activities(after=last_cached_time)
            yield {"progress": 60, "message": f"All new activities fetched from Strava"}

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
        yield {"progress": 70, "message": f"Refreshing stats"}

        cached_activities.extend(new_activities)
        cached_activities.sort(key=lambda x: float(x['start_date']), reverse=True)
        self.app.config.db.save_activities_cache(self.app.config.session_athlete_id, new_activities)

        # Re-calculate ytd_ride_current
        current_year = datetime.now().year
        ytd_ride_current = sum(
            Decimal(activity['distance']) for activity in cached_activities
            if datetime.fromtimestamp(float(activity['start_date'])).year == current_year
            and activity['type'] in ['Ride']
        )
        ytd_ride_elev_current = sum(
            Decimal(activity['total_elevation_gain']) for activity in cached_activities
            if datetime.fromtimestamp(float(activity['start_date'])).year == current_year
            and activity['type'] in ['Ride']
            and activity['total_elevation_gain'] is not None
        )

        yield {"progress": 80, "message": f"Computing goals ..."}

        # Get the current week number (Monday as the first day)
        # W - Monday U - Sunday
        current_week = datetime.now().strftime("%W")
        # Calculate the total distance and total elevation gain for the current week
        wtd_ride_current = sum(
            activity['distance'] for activity in cached_activities
            if datetime.fromtimestamp(float(activity['start_date'])).strftime("%W") == current_week
            and datetime.fromtimestamp(float(activity['start_date'])).year == current_year
            and activity['type'] in ['Ride']
        )


        wtd_ride_elev_current = sum(
            activity['total_elevation_gain'] for activity in cached_activities
            if datetime.fromtimestamp(float(activity['start_date'])).strftime("%W") == current_week
            and datetime.fromtimestamp(float(activity['start_date'])).year == current_year
            and activity['type'] in ['Ride']
            and activity['total_elevation_gain'] is not None
        )

        self.app.config.db.save_athlete_stats(self.app.config.session_athlete_id,
                                     {
                                         strava_goals.yord.name: ytd_ride_current,
                                         strava_goals.yore.name: ytd_ride_elev_current,
                                         strava_goals.word.name: wtd_ride_current,
                                         strava_goals.wore.name: wtd_ride_elev_current,
                                     })

        yield {"progress": 100, "message": f"Completed. Total {new_cached_size} activities, {new_cached_size - last_cached_size} newly fetched."}
