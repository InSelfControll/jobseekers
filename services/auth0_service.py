from functools import wraps
from flask import request, jsonify
from jose import jwt
from urllib.request import urlopen
import json

class Auth0Service:
    def __init__(self, domain, api_audience):
        self.domain = domain
        self.api_audience = api_audience
        self.algorithms = ['RS256']
        
    def get_token_auth_header(self):
        auth = request.headers.get('Authorization', None)
        if not auth:
            raise AuthError('Authorization header is missing', 401)
            
        parts = auth.split()
        if parts[0].lower() != 'bearer':
            raise AuthError('Authorization header must start with Bearer', 401)
            
        if len(parts) == 1:
            raise AuthError('Token not found', 401)
            
        token = parts[1]
        return token
        
    def verify_token(self, token):
        jsonurl = urlopen(f'https://{self.domain}/.well-known/jwks.json')
        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(token)
        
        rsa_key = {}
        for key in jwks['keys']:
            if key['kid'] == unverified_header['kid']:
                rsa_key = {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'n': key['n'],
                    'e': key['e']
                }
                
        if rsa_key:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=self.algorithms,
                audience=self.api_audience,
                issuer=f'https://{self.domain}/'
            )
            return payload
            
        raise AuthError('Unable to find appropriate key', 401)

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = auth0_service.get_token_auth_header()
        payload = auth0_service.verify_token(token)
        return f(*args, **kwargs)
    return decorated
