from requests import request
from os import environ as env
from cabot.cabotapp.alert import AlertPlugin, AlertPluginUserData
from django.db import models
from django.conf import settings
from django.template import Context, Template

VICTOROPS_URL = 'https://api.victorops.com/api-public/v1'

details_template = """Service {{ service.name }} {{ scheme }}://{{ host }}{% url 'service' pk=service.id %} {% if service.overall_status != service.PASSING_STATUS %}alerting with status: {{ service.overall_status }}{% else %}is back to normal{% endif %}.
{% if service.overall_status != service.PASSING_STATUS %}
CHECKS FAILING:{% for check in service.all_failing_checks %}
  FAILING - {{ check.name }} - Type: {{ check.check_category }} - Importance: {{ check.get_importance_display }}{% endfor %}
{% else %}
ALL CHECKS PASSING
{% endif %}
"""

class VictorOpsAlertPlugin(AlertPlugin):
    name = "VictorOps"
    slug = "cabot_alert_victorops"
    author = "Jakub Sokolowski"
    version = "0.1.0"

    def send_alert(self, service, users, duty_officers):
        message = "{} status for service {}".format(service.overall_status, service.name)
        details = Template(details_template).render(Context({
            'service': service,
            'host': settings.WWW_HTTP_HOST,
            'scheme': settings.WWW_SCHEME
        }))
        for user in users:
            vc_login = self._get_vc_login(user)
            print('Sending VictorOps Alert to {}: {}'.format(vc_login, message))
            self._send_victorops_alert(vc_login, message, details)

    # Cabot username doesn't have to be the same as VictorOps one
    def _get_vc_login(self, user):
        results = VictorOpsAlertPluginUserData.objects.filter(user__user__exact=user)
        if results.first() is not None and results.first().victorops_login != "":
            return results.first().victorops_login
        else:
            return user.username

    def _send_victorops_alert(self, user, message, details):
        policy = self._get_policy()
        data = {
            "summary": message,
            "details": details,
            "userName": user,
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
        # TODO: Possibly pick based on name?
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

class VictorOpsAlertPluginUserData(AlertPluginUserData):
    name = "VictorOps Plugin"
    victorops_login = models.CharField(max_length=30, blank=True)

    def serialize(self):
        return {
            "victorops_login": self.victorops_login
        }
