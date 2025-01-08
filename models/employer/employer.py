from flask_login import UserMixin
from extensions import db

class Employer(db.Model, UserMixin):
    """
    Employer model representing company/organization accounts in the system.
    """
    __tablename__ = 'employer'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    company_name = db.Column(db.String(120), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def __init__(self, **kwargs):
        super(Employer, self).__init__(**kwargs)

    def __repr__(self):
        return f'<Employer {self.company_name}>'
