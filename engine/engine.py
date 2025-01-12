from flask import Flask, Response
import subprocess
import os
from pathlib import Path


class Engine:
    WIDGET_FONT_COLOR: str = "#fb5200"
    WIDGET_FONT_COLOR_STROKE: str = "none"
    WIDGET_FONT_STROKE_WIDTH: str = "0"

    CANVAS_WIDTH: int  = 1920
    CANVAS_HEIGHT: int = 1080


    def __init__(self):
        pass

    def render(self):
        # Define the path to the HTML files
        pwd: str = os.path.join(Path.cwd(), "engine", "html")

        # Read the input file in read mode
        with open(pwd + "/page.html", "r") as f:
            html_data: str = f.read()

        with open(pwd + "/widget-goal.html", "r") as f:
            widget_goal: str = f.read()

        with open(pwd + "/widget-stats.html", "r") as f:
            widget_stats: str = f.read()

        # Replace the paths in the HTML data
        html_data = html_data.replace('href="./', 'href="' + pwd + '/')
        html_data = html_data.replace('src="./', 'src="' + pwd + '/')
        html_data = html_data.replace('url(./', 'url(' + pwd + '/')

        html_data = html_data.replace('<widget id="widget-goal.html"></widget>', widget_goal)
        html_data = html_data.replace('<widget id="widget-stats.html"></widget>', widget_stats)
        html_data = html_data.replace('{{ widget_font_color }}', self.WIDGET_FONT_COLOR)
        html_data = html_data.replace('{{ widget_font_color_stroke }}', self.WIDGET_FONT_COLOR_STROKE)
        html_data = html_data.replace('{{ widget_font_stroke_width }}', self.WIDGET_FONT_STROKE_WIDTH)
        html_data = html_data.replace('{{ canvas_width }}', str(self.CANVAS_WIDTH))
        html_data = html_data.replace('{{ canvas_height }}', str(self.CANVAS_HEIGHT))

        print(html_data)

        # Add --local-file-access to the options
        options = ['--quality', '100',
                   '--width', str(self.CANVAS_WIDTH),
                   '--height', str(self.CANVAS_HEIGHT),
                   '--images',
                   '--enable-local-file-access']

        # Run the command with the updated options and capture the output
        result = subprocess.run(
            ['wkhtmltoimage'] + options + ['-', '-'],
            input=html_data.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Save the output to a variable
        png_output = result.stdout

        return Response(png_output, mimetype='image/png')
