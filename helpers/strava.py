import os

from flask import Flask


# from stravalib import Client
# from stravalib.model import Athlete
# from stravalib.protocol import AccessInfo
# from stravalib.strava_model import ActivityStats, SummaryActivity

class Strava():
    client_id: int
    client_secret: str
    redirect_uri: str

    def __init__(self, application: Flask):
        self.client_id = int(os.environ.get("STRAVA_CLIENT_ID"))
        self.client_secret = os.environ.get("STRAVA_CLIENT_SECRET")
        self.redirect_uri = 'http://home:5000/callback'
        if not self.client_id:
            application.config.logger.error("STRAVA_CLIENT_ID environment variable not set")
            return
        if not self.client_secret:
            application.config.logger.error("STRAVA_CLIENT_SECRET environment variable not set")
            return

# def revalidate_strava_client(strava_client) -> Client:
#     config = Configuration.Configuration()
#     now_timestamp = datetime.now().timestamp()
#     expires_at = int(redis.hget(f"user:{session['username']}", "expires_at")) - (5 * 60 * 1000)  # -5min
#     if now_timestamp > expires_at:
#         app.logger.debug(f"revalidate_strava_client() : start : revalidating")
#         token_response: AccessInfo = strava_client.refresh_access_token(
#             client_id=config.strava_client_id,
#             client_secret=config.strava_client_secret,
#             refresh_token=redis.hget(f"user:{session['username']}", "refresh_token"))
#         access_token = token_response['access_token']
#         refresh_token = token_response['refresh_token']
#         expires_at = token_response['expires_at']
#         strava_client.access_token = access_token
#         strava_client.refresh_token = refresh_token
#         strava_client.token_expires_at = expires_at
#         redis.client().hset(f"user:{session['username']}", "strava_client", helper.pickle_object(strava_client))
#         redis.client().hset(f"user:{session['username']}", "access_token", access_token)
#         redis.client().hset(f"user:{session['username']}", "refresh_token", refresh_token)
#         redis.client().hset(f"user:{session['username']}", "expires_at", expires_at)
#         app.logger.debug(f"revalidate_strava_client() : end : revalidated - new token expires at: {expires_at}")
#     return strava_client
#
#
# def get_client_from_redis() -> Client:
#     app.logger.debug(
#         f"get_client_from_redis() : start : session['username']='{session['username'] if 'username' in session else ''}'")
#     if session:
#         if session['username']:
#             if session['username'] != "":
#                 username: str = session['username']
#                 data = redis.hgetall(f"user:{username}")
#                 if "strava_client" in data:
#                     app.logger.debug(f"get_client_from_redis() : contains 'strava_client'")
#                     return helper.depickle_object(data.get("strava_client"))
#                 else:
#                     app.logger.debug(f"get_client_from_redis() : doesn't contain 'strava_client'")
#                     flash("Re-authorization required", category='warning')
#     return None
#
#
# def get_activities(before: datetime | None, after: datetime | None, limit: int | None) -> list[SummaryActivity]:
#     app.logger.debug(
#         f"get_activities() : start : session['username']='{session['username'] if 'username' in session else ''}'")
#     strava_client = get_client_from_redis()
#     strava_client = revalidate_strava_client(strava_client)
#     summary_activities: list[SummaryActivity] = strava_client.get_activities(before=before,
#                                                                              after=after,
#                                                                              limit=limit)
#     return summary_activities
#
#
# def get_athlete(fresh: bool = False) -> Athlete:
#     app.logger.debug(
#         f"get_athlete(fresh={fresh}) : start : session['username']='{session['username'] if 'username' in session else ''}'")
#     strava_client = get_client_from_redis()
#     if fresh:
#         if strava_client:
#             strava_client = revalidate_strava_client(strava_client)
#             athlete: Athlete = strava_client.get_athlete()
#             if athlete:
#                 app.logger.debug(f"get_athlete({fresh}) : athlete info fetched, updating redis, returning fresh")
#                 redis.client().hset(f"user:{session['username']}", "strava_athlete", helper.pickle_object(athlete))
#                 redis.client().hset(f"user:{session['username']}", "strava_id", athlete.id)
#                 return athlete
#     else:
#         if session:
#             if session['username']:
#                 if session['username'] != "":
#                     data = redis.hgetall(f"user:{session['username']}")
#                     if "strava_client" in data:
#                         app.logger.debug(f"get_athlete({fresh}) : reading from redis, returning cached data")
#                         return helper.depickle_object(data.get("strava_athlete"))
#                     else:
#                         app.logger.debug(f"get_athlete({fresh}) : strava_client missing, getting fresh")
#                         return get_athlete(fresh=True)
#     app.logger.debug(f"get_athlete({fresh}) : fallback")
#     return None
#
#
# def get_athlete_stats(athlete_id) -> ActivityStats:
#     app.logger.debug(
#         f"get_athlete_stats(athlete_id={athlete_id}) : start : session['username']='{session['username'] if 'username' in session else ''}'")
#     strava_client = get_client_from_redis()
#     if strava_client:
#         app.logger.debug(f"get_athlete_stats(athlete_id={athlete_id}) : data_read")
#         strava_client = revalidate_strava_client(strava_client)
#         return strava_client.get_athlete_stats(athlete_id)
#     return None
