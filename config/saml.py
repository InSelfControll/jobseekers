
import os

SAML_SETTINGS = {
    'strict': True,
    'debug': True,
    'sp': {
        'entityId': os.environ.get('SAML_SP_ENTITY_ID', 'jobseekr-app'),
        'assertionConsumerService': {
            'url': os.environ.get('SAML_ACS_URL', 'https://jobseekr.example.com/auth/saml/callback'),
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
        },
        'singleLogoutService': {
            'url': os.environ.get('SAML_SLO_URL', 'https://jobseekr.example.com/auth/saml/logout'),
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
        },
        'NameIDFormat': 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
        'x509cert': os.environ.get('SAML_SP_CERT', ''),
        'privateKey': os.environ.get('SAML_SP_PRIVATE_KEY', '')
    },
    'idp': {
        'entityId': os.environ.get('SAML_IDP_ENTITY_ID', 'https://login.microsoftonline.com/tenant-id/saml2'),
        'singleSignOnService': {
            'url': os.environ.get('SAML_SSO_URL', 'https://login.microsoftonline.com/tenant-id/saml2'),
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
        },
        'singleLogoutService': {
            'url': os.environ.get('SAML_IDP_SLO_URL', 'https://login.microsoftonline.com/tenant-id/saml2'),
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
        },
        'x509cert': os.environ.get('SAML_IDP_CERT', '')
    }
}
