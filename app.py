from flask import Flask, render_template
from engine.engine import Engine

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/stats.png')
def stats_image():
    engine = Engine()
    return engine.render()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
