'''
nohup locust -f benchmark/main.py --web-port 8089 > locust.log
'''
import logging

from requests.auth import HTTPBasicAuth
from datetime import datetime
from dateutil.tz import tzutc
import analytics
from faker import Faker
from locust import HttpUser, between, tag, task

# create logger
_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
_logger = logging.getLogger('benchmark')
_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)
_ch.setFormatter(logging.Formatter(_format))
_logger.addHandler(_ch)

HOST = '<API Gateway URL>'
WRITE_KEY = '<Your Write Key>'

fake = Faker(locale=['zh_TW'])


class WebUser(HttpUser):
    user_id = None
    cookie_id = fake.unique.uuid4()
    ip = fake.ipv4()
    user_agent = fake.user_agent()
    wait_time = between(1, 5)
    weight = 1

    current = None
    referrer = None

    def on_start(self):
        """
        Called when a User starts running.
        """
        self.tracker = analytics.Client(
            write_key=WRITE_KEY,
            send=False,
        )

    @tag('view_page')
    @task(3)
    def view_page(self):
        self.referrer = self.current
        self.current = fake.job()

        (_, msg) = self.tracker.page(
            user_id=self.user_id or '',
            anonymous_id=self.cookie_id,
            name=self.current,
            properties={
                'page_title': f'{self.current}',
                'url': f'https://www.dummy.com/{self.current}',
                'referrer': f'https://www.dummy.com/{self.referrer}' if self.referrer else '',
            },
            context={
                "page": {
                    "title": f'{self.current}',
                    "path": f"/{self.current}",
                    'url': f'https://www.dummy.com/{self.current}',
                    'referrer': f'https://www.dummy.com/{self.referrer}' if self.referrer else '',
                },
                "ip": self.ip,
                "userAgent": self.user_agent
            }
        )
        self._send(msg)

    @tag('view_and_save_job')
    @task(1)
    def view_and_save_job(self):
        self.view_page()
        if self.user_id is None:
            self.referrer = self.current
            self.current = 'login'

            self.user_id = fake.unique.uuid4()
            (_, msg) = self.tracker.track(
                user_id=self.user_id or '',
                anonymous_id=self.cookie_id,
                event='Login',
                context={
                    "page": {
                        "title": f'{self.current}',
                        "path": f"/{self.current}",
                        'url': f'https://www.dummy.com/{self.current}',
                        'referrer': f'https://www.dummy.com/{self.referrer}' if self.referrer else '',
                    },
                    "ip": self.ip,
                    "userAgent": self.user_agent
                },
            )
            self._send(msg)

            self.current = self.referrer
            self.referrer = 'login'

        (_, msg) = self.tracker.track(
            user_id=self.user_id or '',
            anonymous_id=self.cookie_id,
            event='saveJob',
            context={
                "page": {
                    "title": f'{self.current}',
                    "path": f"/{self.current}",
                    'url': f'https://www.dummy.com/{self.current}',
                    'referrer': f'https://www.dummy.com/{self.referrer}' if self.referrer else '',
                },
                "ip": self.ip,
                "userAgent": self.user_agent
            },
        )
        self._send(msg)

    def _send(self, msg):
        self.client.post(
            '/v1/batch',
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'analytics-python/1.4.0'
            },
            auth=HTTPBasicAuth(WRITE_KEY, ''),
            json={
                'sentAt': datetime.utcnow().replace(tzinfo=tzutc()).isoformat(),
                'batch': [msg]
            }
        )


class AnonymousUser(HttpUser):
    cookie_id = fake.unique.uuid4()
    ip = fake.ipv4()
    user_agent = fake.user_agent()
    wait_time = between(1, 5)
    weight = 3

    current = None
    referrer = None

    def on_start(self):
        """
        Called when a User starts running.
        """
        self.tracker = analytics.Client(
            write_key=WRITE_KEY,
            send=False,
        )

    @tag('view_page')
    @task
    def view_page(self):
        self.referrer = self.current
        self.current = fake.job()

        (_, msg) = self.tracker.page(
            anonymous_id=self.cookie_id,
            name=self.current,
            properties={
                'page_title': f'{self.current}',
                'url': f'https://www.dummy.com/{self.current}',
                'referrer': f'https://www.dummy.com/{self.referrer}' if self.referrer else '',
            },
            context={
                "page": {
                    "title": f'{self.current}',
                    "path": f"/{self.current}",
                    'url': f'https://www.dummy.com/{self.current}',
                    'referrer': f'https://www.dummy.com/{self.referrer}' if self.referrer else '',
                },
                "ip": self.ip,
                "userAgent": self.user_agent
            }
        )
        self._send(msg)

    def _send(self, msg):
        self.client.post(
            '/v1/batch',
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'analytics-python/1.4.0'
            },
            auth=HTTPBasicAuth(WRITE_KEY, ''),
            json={
                'sentAt': datetime.utcnow().replace(tzinfo=tzutc()).isoformat(),
                'batch': [msg]
            }
        )
