import io
import os
import subprocess
from pathlib import Path
from .render_mode import RenderMode


from PIL import Image, ImageDraw, ImageFont
from flask import Flask, Response, send_file

import helpers.mysql as database


class Engine:
    WIDGET_FONT_COLOR: str = "#fb5200"
    WIDGET_FONT_COLOR_STROKE: str = "none"
    WIDGET_FONT_STROKE_WIDTH: str = "0"

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

    def widget_ytd_ride_data(self, athlete_id: int) -> dict:
        # profile_info = db.load_profile(athlete_info.id)
        return {"ytd_ride": 10000, "ytd_ride_totals": 239, "achieved": 2.3, "text": "ride"}

    def load_widget_template(self, widget_type):
        pwd: str = os.path.join(Path.cwd(), "engine", "html")
        file: str = ""
        html_data: str = ""
        data = {}
        if widget_type == "ytd_ride":
            file = "widgets/ytd.html"
            data = self.widget_ytd_ride_data(1)
        if widget_type == "ride_stats":
            file = "widget-stats.html"
            data = {}
        with open(pwd + "/" + file, "r") as f:
            html_data: str = f.read()
        for key, value in data.items():
            html_data = html_data.replace('{{ ' + key + ' }}', str(value))
        return html_data

    # TODO next steps:
    # - move widgets to widgets
    # - parametrize location
    # - finish source data (ytd, stats)
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

    def render_html(self, mode: RenderMode = RenderMode.IMAGE):
        self.app.config.logger.info("render()")
        # Define the path to the HTML files
        pwd: str = os.path.join(Path.cwd(), "engine", "html")

        # Read the input file in read mode
        with open(pwd + "/page.html", "r") as f:
            self.html_data: str = f.read()

        widget_goal = self.load_widget_template("ytd_ride")

        with open(pwd + "/widget-stats.html", "r") as f:
            widget_stats: str = f.read()

        path: str = ""
        if mode == RenderMode.IMAGE:
            path = pwd
        elif mode == RenderMode.HTML:
            path = "/engine"

        # Replace the paths in the HTML data
        self.html_data = self.html_data.replace('href="./', 'href="' + path + '/')
        self.html_data = self.html_data.replace('src="./', 'src="' + path + '/')
        self.html_data = self.html_data.replace('url(./', 'url(' + path + '/')

        self.html_data =self. html_data.replace('<widget id="widget-goal.html"></widget>', widget_goal)
        self.html_data = self.html_data.replace('<widget id="widget-stats.html"></widget>', widget_stats)
        self.html_data = self.html_data.replace('{{ widget_font_color }}', self.WIDGET_FONT_COLOR)
        self.html_data = self.html_data.replace('{{ widget_font_color_stroke }}', self.WIDGET_FONT_COLOR_STROKE)
        self.html_data = self.html_data.replace('{{ widget_font_stroke_width }}', self.WIDGET_FONT_STROKE_WIDTH)
        self.html_data = self.html_data.replace('{{ canvas_width }}', str(self.CANVAS_WIDTH))
        self.html_data = self.html_data.replace('{{ canvas_height }}', str(self.CANVAS_HEIGHT))

        #self.app.config.logger.info(html_data)

    def render(self):
        self.render_html()

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
