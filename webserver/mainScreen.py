from flask import Flask, redirect, url_for, render_template
from urllib.parse import quote
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def generate_cognito_url(client_id, redirect_uri, scope, response_type="code"):
    base_url = "https://audioclientserver.auth.us-east-2.amazoncognito.com/oauth2/authorize"
    encoded_redirect_uri = quote(redirect_uri, safe='')
    url = f"{base_url}?client_id={client_id}&response_type={response_type}&redirect_uri={encoded_redirect_uri}&scope={scope}"
    return url

@app.route('/')
def home():
    cognito_url = generate_cognito_url(
        client_id="60cnfmeqsto6f6td9i83qrn7ii",
        response_type="token",
        redirect_uri="https://jwt.io",
        scope="email+openid+phone+profile"
    )
    return render_template("index.html", cognito_url=cognito_url)

@app.route('/go-to-google', methods=['POST'])
def go_to_google():
    return redirect(generate_cognito_url(
        client_id="60cnfmeqsto6f6td9i83qrn7ii",
        response_type="token",
        redirect_uri="https://jwt.io",
        scope="email+openid+phone+profile"  # Added scope
    ))

@app.route('/success_login', methods=['POST','GET'])
def success_login():
    return "<h1> successful login </h1>"

@app.route('/cognito_login')
def cognito_login():
    return render_template('cognito_login.html')


if __name__ == '__main__':
    app.run()

