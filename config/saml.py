
import os

SAML_SETTINGS = {
    'strict': True,
    'debug': True,
    'sp': {
        'entityId': os.environ.get('SAML_SP_ENTITY_ID', 'your-app-entity-id'),
        'assertionConsumerService': {
            'url': os.environ.get('SAML_ACS_URL', 'https://your-app/auth/saml/callback'),
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
        },
        'singleLogoutService': {
            'url': os.environ.get('SAML_SLO_URL', 'https://your-app/auth/saml/logout'),
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
        },
        'x509cert': '',
        'privateKey': ''
    },
    'idp': {
        'entityId': os.environ.get('SAML_IDP_ENTITY_ID', ''),
        'singleSignOnService': {
            'url': os.environ.get('SAML_SSO_URL', ''),
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
        },
        'singleLogoutService': {
            'url': os.environ.get('SAML_IDP_SLO_URL', ''),
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
        },
        'x509cert': os.environ.get('SAML_IDP_CERT', '')
    }
}
