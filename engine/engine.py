import io
import os
import subprocess
from pathlib import Path
from unicodedata import decimal

from helpers.strava_goals import StatsType
from .render_mode import RenderMode


from PIL import Image, ImageDraw, ImageFont
from flask import Flask, Response, send_file

import helpers.mysql as database
import helpers.strava_goals as strava_goals


class Engine:
    WIDGET_FONT_COLOR: str = "white"
    WIDGET_FONT_COLOR_HIGHLIGHT: str = "#fc4c02"
    WIDGET_FONT_COLOR_STROKE: str = "#222"
    WIDGET_FONT_STROKE_WIDTH: str = "1"

    CANVAS_WIDTH: int = 1920
    CANVAS_HEIGHT: int = 1080

    app: Flask
    html_data: str

    def __init__(self, app: Flask):
        self.app = app
        self.db = database.Database(app)
        self.app.config.logger.info("Engine.__init__()")
        self.app.config.logger.info(app.config.db)
        pass

    def widget_distance_elevation(self, activity_type: str, distance: StatsType, elevation: StatsType) -> dict:
        athlete_id: int = self.app.config.session_athlete_id
        stats: dict = self.db.load_athlete_stats(athlete_id)
        print(stats)
        goal_yord: dict = stats[distance.name]
        goal_yore: dict = stats[elevation.name]
        goal_yord_unit: str = distance.value["unit"]
        goal_yore_unit: str = elevation.value["unit"]
        return {"goal_yord_plan": goal_yord["plan"],
                "goal_yord_stat": goal_yord["stat"],
                "goal_yore_plan": goal_yore["plan"],
                "goal_yore_stat": goal_yore["stat"],
                "goal_yord_unit": goal_yord_unit,
                "goal_yore_unit": goal_yore_unit,
                "achieved": round(float(goal_yord["stat"]) / float(goal_yord["plan"]) * 1000) / 10,
                "activity_type": activity_type}

    def load_widget_template(self, widget_type, widget_name, widget_id, left, top, width, height):
        pwd: str = os.path.join(Path.cwd(), "engine", "html")
        template: str = ""
        html_data: str = ""

        # read .template file
        with open(pwd + "/widgets/.template.html", "r") as f:
            template = f.read()

        file: str = ""

        data = {}
        if widget_type == "ytd_ride":
            file = "widgets/ytd-simple.html"
            data = self.widget_distance_elevation(activity_type="ride",
                                                  distance=strava_goals.StatsType.yord,
                                                  elevation=strava_goals.StatsType.yore)
        if widget_type == "ride_stats":
            file = "widgets/widget-ytd-ride-totals-simple.html"
            data = self.widget_distance_elevation(activity_type="ride",
                                                  distance=strava_goals.StatsType.yord,
                                                  elevation=strava_goals.StatsType.yore)
        print('== data ==')
        print(data)
        print('== data ==')
        print('== reading ----' + pwd + "/" + file)

        with open(pwd + "/" + file, "r") as f:
            html_data = f.read()
        for key, value in data.items():
            html_data = html_data.replace('{{ ' + key + ' }}', str(value))

        print('== content html_data ----')
        print(html_data)
        print('== content html_data ----')

        # place the html to the template, there are
        template = template.replace('{{ widget_left }}', str(left))
        template = template.replace('{{ widget_top }}', str(top))
        template = template.replace('{{ widget_width }}', str(width))
        template = template.replace('{{ widget_height }}', str(height))
        template = template.replace('{{ widget_id }}', str(widget_id))
        template = template.replace('{{ widget_name }}', str(widget_name))
        template = template.replace('{{ widget_content }}', str(html_data))

        print('load_widget_template NEW ----')
        print(template)
        print('load_widget_template NEW ----')

        return template

    # TODO next steps:
    # - move widgets to widgets
    # - parametrize location
    # - optimize token handling

    def serve_error(self, message: str):
        # Open the image using Pillow
        image = Image.open('engine/html/error.png').convert("RGBA")

        # Create a drawing context
        draw = ImageDraw.Draw(image)

        # Specify the font and size (you may need to download a ttf font and provide the path)
        font = ImageFont.load_default(15)

        # Add text to the image
        draw.text((20, 213), message, font=font, fill=(224, 64, 6, 255))  # White color with full opacity

        # Create a bytes buffer to hold the image data
        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)

        # Serve the image
        return send_file(img_io, mimetype='image/png')

    def render_html_new(self, guid: str, mode: RenderMode = RenderMode.IMAGE):
        self.app.config.logger.info("render_html_new!")
        # Define the path to the HTML files
        pwd: str = os.path.join(Path.cwd(), "engine", "html")

        # Read the input file in read mode
        with open(pwd + "/page.html", "r") as f:
            self.html_data: str = f.read()

        widget_goal = self.load_widget_template("ytd_ride","Year to now", "1", "0%", top="0%", width="40%", height="20%")
        widget_stats: str = self.load_widget_template("ride_stats","Stats", "2", "70%", top="30%", width="40%", height="20%")

        path: str = ""
        if mode == RenderMode.IMAGE:
            path = pwd
        elif mode in (RenderMode.HTML, RenderMode.EDIT):
            path = "/engine"

        # Replace the paths in the HTML data
        self.html_data = self.html_data.replace('href="./', 'href="' + path + '/')
        self.html_data = self.html_data.replace('src="./', 'src="' + path + '/')
        self.html_data = self.html_data.replace('url(./', 'url(' + path + '/')

        self.html_data =self. html_data.replace('<widget id="widget-goal.html"></widget>', widget_goal)
        self.html_data = self.html_data.replace('<widget id="widget-stats.html"></widget>', widget_stats)
        self.html_data = self.html_data.replace('{{ widget_font_color }}', self.WIDGET_FONT_COLOR)
        self.html_data = self.html_data.replace('{{ widget_font_color_highlight }}', self.WIDGET_FONT_COLOR_HIGHLIGHT)
        self.html_data = self.html_data.replace('{{ widget_font_color_stroke }}', self.WIDGET_FONT_COLOR_STROKE)
        self.html_data = self.html_data.replace('{{ widget_font_stroke_width }}', self.WIDGET_FONT_STROKE_WIDTH)
        self.html_data = self.html_data.replace('{{ canvas_width }}', str(self.CANVAS_WIDTH))
        self.html_data = self.html_data.replace('{{ canvas_height }}', str(self.CANVAS_HEIGHT))

        #self.app.config.logger.info(html_data)


    # def render_html(self, mode: RenderMode = RenderMode.IMAGE):
    #     self.app.config.logger.info("render()")
    #     # Define the path to the HTML files
    #     pwd: str = os.path.join(Path.cwd(), "engine", "html")
    #
    #     # Read the input file in read mode
    #     with open(pwd + "/page.html", "r") as f:
    #         self.html_data: str = f.read()
    #
    #     widget_goal = self.load_widget_template("ytd_ride")
    #     widget_stats: str = self.load_widget_template("ride_stats")
    #
    #     path: str = ""
    #     if mode == RenderMode.IMAGE:
    #         path = pwd
    #     elif mode == RenderMode.HTML:
    #         path = "/engine"
    #
    #     # Replace the paths in the HTML data
    #     self.html_data = self.html_data.replace('href="./', 'href="' + path + '/')
    #     self.html_data = self.html_data.replace('src="./', 'src="' + path + '/')
    #     self.html_data = self.html_data.replace('url(./', 'url(' + path + '/')
    #
    #     self.html_data =self. html_data.replace('<widget id="widget-goal.html"></widget>', widget_goal)
    #     self.html_data = self.html_data.replace('<widget id="widget-stats.html"></widget>', widget_stats)
    #     self.html_data = self.html_data.replace('{{ widget_font_color }}', self.WIDGET_FONT_COLOR)
    #     self.html_data = self.html_data.replace('{{ widget_font_color_highlight }}', self.WIDGET_FONT_COLOR_HIGHLIGHT)
    #     self.html_data = self.html_data.replace('{{ widget_font_color_stroke }}', self.WIDGET_FONT_COLOR_STROKE)
    #     self.html_data = self.html_data.replace('{{ widget_font_stroke_width }}', self.WIDGET_FONT_STROKE_WIDTH)
    #     self.html_data = self.html_data.replace('{{ canvas_width }}', str(self.CANVAS_WIDTH))
    #     self.html_data = self.html_data.replace('{{ canvas_height }}', str(self.CANVAS_HEIGHT))
    #
    #     #self.app.config.logger.info(html_data)

    def render(self):
        self.render_html_new()

        # Add --local-file-access to the options
        options = ['--quality', '100',
                   '--width', str(self.CANVAS_WIDTH),
                   '--height', str(self.CANVAS_HEIGHT),
                   '--images',
                   '--enable-local-file-access']

        # Run the command with the updated options and capture the output
        result = subprocess.run(
            ['wkhtmltoimage'] + options + ['-', '-'],
            input=self.html_data.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        error_code: int = result.returncode
        if error_code != 0:
            stderr_output: str = result.stderr.decode('utf-8')
            self.app.config.logger.error(stderr_output)
            return self.serve_error("Error while processing: " + stderr_output)

        # Save the output to a variable
        png_output = result.stdout

        return Response(png_output, mimetype='image/png')
