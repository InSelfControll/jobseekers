import os

AUTH_SETTINGS = {
    'auth0': {
        'domain': os.environ.get('AUTH0_DOMAIN'),
        'client_id': os.environ.get('AUTH0_CLIENT_ID'),
        'client_secret': os.environ.get('AUTH0_CLIENT_SECRET'),
        'callback_url': os.environ.get('AUTH0_CALLBACK_URL', 'https://jobseekr.example.com/auth/auth0/callback')
    },
    'github': {
        'client_id': os.environ.get('GITHUB_CLIENT_ID'),
        'client_secret': os.environ.get('GITHUB_CLIENT_SECRET'),
        'callback_url': os.environ.get('GITHUB_CALLBACK_URL', 'https://jobseekr.example.com/auth/github/callback')
    }
}
