from flask import Flask, render_template  # Added render_template here
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

# Other code






