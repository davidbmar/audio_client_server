from flask import Flask, request, jsonify
from jose import jwt, JWSError
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Fetch the JWKS
jwks_url = "https://cognito-idp.us-east-2.amazonaws.com/us-east-2_k3HWNzgIw/.well-known/jwks.json"
jwks = requests.get(jwks_url).json()

@app.route('/authenticated/', methods=['GET'])
def authenticated():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token.split('Bearer ')[1]
    else:
        return jsonify({"message": "Token is missing!"}), 401

    # Validate the token using the JWKS
    try:
        payload = jwt.decode(token, jwks, algorithms=['RS256'])

        # Extract user groups
        user_groups = payload.get('cognito:groups', [])

        return jsonify({"message": "Token is valid!", "data": payload}), 200
    except (jwt.ExpiredSignatureError, jwt.JWTClaimsError, jwt.JWTError, JWSError) as e:
        return jsonify({"message": "Token is invalid!", "error": str(e)}), 401



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

