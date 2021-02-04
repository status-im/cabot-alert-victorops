# Description

This is a [Cabot Alert Plugin](https://cabotapp.com/dev/writing-alert-plugins.html) for sending alerts to [VictorOps](https://victorops.com/).

# Installation

The simplest way is to just use:
```sh
pip install git+git://github.com/status-im/cabot-alert-victorops.git
```
Edit conf/production.env in your Cabot clone to include the plugin:
```
CABOT_PLUGINS_ENABLED=cabot_alert_victorops,<other plugins>
```

# Configuration

This plugin requries the following environment variables to be set:
```sh
VICTOROPS_APP_ID=<your_victorops_app_id>
VICTOROPS_API_KEY=<your_victorops_api_key>
VICTOROPS_REDIS_URL=redis://<host>:<port>/<db>
```

See the [redis-py docs](https://redis-py.readthedocs.io/en/stable/#redis.Redis.from_url) for more info about the supported URL schemes for Redis.

# Known Issues / TODO

This plugin needs to be able to update existing incidents instead of creating new ones for each state change.
