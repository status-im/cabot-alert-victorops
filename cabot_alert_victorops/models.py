import requests
from os import environ as env
from cabot.plugins.models import AlertPlugin

from logging import getLogger
logger = getLogger(__name__)

VICTOROPS_URL = 'https://api.victorops.com/api-public/v1'

class VictorOpsAlertPlugin(AlertPlugin):
    name = "VictorOps"
    slug = "cabot_alert_victorops"
    author = "Jakub Sokołowski"
    version = "0.1.0"

    def send_alert(self, service, users, duty_officers):
        message = service.get_status_message()
        for user in users:
            logger.info('{} - {} - This is bad for your {}.'.format(
                user, message,
                u.cabot_alert_victorops_settings.favorite_bone))

            _send_victorops_alert(user, message, "DETAILS")

        return True

    def _send_victorops_alert(self, user, message, details):
        app_id = env.get('VICTOROPS_APP_ID')
        api_key = env.get('VICTOROPS_API_KEY')

        data = {
            "summary": message,
            "details": details,
            "userName": user,
            "isMultiResponder": true,
            "targets": [],
        }
        headers = {
            "X-VO-Api-Id": app_id,
            "X-VO-Api-Key": api_key,
        }

        resp = requests.post(
            '{}/api-public/v1/incidents'.format(VICTOROPS_URL),
            data, headers
        )
        resp.raise_for_status()
        return True
