from requests import request
from os import environ as env
from cabot.cabotapp.alert import AlertPlugin

VICTOROPS_URL = 'https://api.victorops.com/api-public/v1'

class VictorOpsAlertPlugin(AlertPlugin):
    name = "VictorOps"
    slug = "cabot_alert_victorops"
    author = "Jakub Sokolowski"
    version = "0.1.0"

    def send_alert(self, service, users, duty_officers):
        message = "TODO"
        for user in users:
            print('Notification for: {} - {}'.format(user, message))
            self._send_victorops_alert(user, message, "DETAILS")

        return True

    def _send_victorops_alert(self, user, message, details):
        self.username = env.get('VICTOROPS_USERNAME')
        if self.username is None:
            raise Exception("VICTOROPS_USERNAME env variable not found!")

        policy = self._get_policy()
        data = {
            "summary": message,
            "details": details,
            "userName": self.username,
            "targets": [{
                "type": "EscalationPolicy",
                "slug": policy["slug"],
            }],
        }
        resp = self._query('POST', 'incidents', data)
        resp.raise_for_status()
        return True

    def _get_policy(self):
        resp = self._query('GET', 'policies')
        return resp.json()["policies"][0]["policy"]

    def _query(self, method, path, data={}):
        self.app_id = env.get('VICTOROPS_APP_ID')
        self.api_key = env.get('VICTOROPS_API_KEY')
        if self.app_id is None:
            raise Exception("VICTOROPS_APP_ID env variable not found!")
        if self.api_key is None:
            raise Exception("VICTOROPS_API_KEY env variable not found!")

        headers = {
            "X-VO-Api-Id": self.app_id,
            "X-VO-Api-Key": self.api_key,
        }
        resp = request(method, VICTOROPS_URL+'/'+path, json=data, headers=headers)
        resp.raise_for_status()
        return resp
