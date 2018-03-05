from flask_unchained import AppConfig


class BaseConfig(AppConfig):
    SECRET_KEY = 'not-secret-key'

    BUNDLES = [
        'flask_sqlalchemy_bundle',
    ]


class TestConfig(BaseConfig):
    TESTING = True
    DEBUG = True
