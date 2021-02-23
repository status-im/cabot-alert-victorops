import redis
from requests import request
from os import environ as env
from cabot.cabotapp.alert import AlertPlugin, AlertPluginUserData
from django.db import models
from django.conf import settings
from django.template import Context, Template
from celery.utils.log import get_task_logger

log = get_task_logger(__name__)

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
        # Redis is used to store existing incidents,
        # so that multiple Celery workers can resolve them
        r = redis.from_url(env.get('VICTOROPS_REDIS_URL'))

        details = Template(details_template).render(Context({
            'service': service,
            'host': settings.WWW_HTTP_HOST,
            'scheme': settings.WWW_SCHEME
        }))

        for user in users:
            vc_login = self._get_vc_login(user)

            for check in service.all_failing_checks():
                check, message = self._gen_check_message(service, check)
                log.info('Sending VictorOps Incident for %s: %s', vc_login, message)
                incident = self._create_victorops_incident(vc_login, message, details)
                r.set(check, incident)

            for check in service.all_passing_checks():
                check, message = self._gen_check_message(service, check)
                if r.get(check) is None:
                    continue
                log.info('Resolving VictorOps Incident for %s: %s', vc_login, message)
                self._resolve_victorops_incident(vc_login, message, r.get(check))
                r.delete(check)

    def _gen_check_message(self, service, check):
        check = "{}/{}".format(service.name, check.name)
        message = "{}: {}".format(service.overall_status, check)
        return check, message

    # Cabot username doesn't have to be the same as VictorOps one
    def _get_vc_login(self, user):
        results = VictorOpsAlertPluginUserData.objects.filter(user__user__exact=user)
        if results.first() is not None and results.first().victorops_login != "":
            return results.first().victorops_login
        else:
            return user.username

    def _create_victorops_incident(self, user, message, details):
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
        return resp.json()["incidentNumber"]

    def _resolve_victorops_incident(self, user, message, incident_number):
        data = {
            "userName": user,
            "message": message,
            "incidentNames": [incident_number],
        }
        resp = self._query('PATCH', 'incidents/resolve', data)
        return resp.json()

    def _get_policy(self):
        resp = self._query('GET', 'policies')
        # Return Infrastructure policy
        for policy in resp.json()["policies"]:
            if policy["team"]["name"] == "Infrastructure":
                return policy["policy"]

        # TODO: Naive fallback to first policy available
        return policies[0]["policy"]

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
        log.debug('JSON Response: %s', resp.json())
        resp.raise_for_status()
        return resp

class VictorOpsAlertPluginUserData(AlertPluginUserData):
    name = "VictorOps Plugin"
    victorops_login = models.CharField(max_length=30, blank=True)

    def serialize(self):
        return {
            "victorops_login": self.victorops_login
        }
