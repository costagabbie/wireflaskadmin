import os
from dotenv import load_dotenv

# Setting the paths
APP_ROOT = os.path.join(os.path.dirname(__file__), "..")
DOTENV_PATH = os.path.join(APP_ROOT, ".env")
load_dotenv(DOTENV_PATH)

class Config:
    SECRET_KEY = os.getenv('WFADMIN_SECRET_KEY')
    HCAPTCHA_ENABLE = os.getenv('WFADMIN_HCAPTCHA_ENABLE') == 'Y'
    HCAPTCHA_API_KEY = os.getenv('WFADMIN_HCAPTCHA_API_KEY')
    HCAPTCHA_SITE_KEY = os.getenv('WFADMIN_HCAPTCHA_SITE_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('WFADMIN_SQLALCHEMY_DATABASE_URI')
    ENDPOINT_AUTOIP = os.getenv('WFADMIN_ENDPOINT_AUTOIP')
    DAEMON_HOST = os.getenv('WFADMIN_DAEMON_HOST')
    DAEMON_PORT = os.getenv('WFADMIN_DAEMON_PORT')
