'''
python simulator.py --host <API Gateway URL> --writeKey <Your Write Key>
'''
import logging
import argparse
import analytics
from faker import Faker
from time import sleep
from tqdm import tqdm


__name__ = 'simulator.py'
__version__ = '0.0.1'
__description__ = 'scripting simulator'

parser = argparse.ArgumentParser(description='send a segment message')

parser.add_argument('--host', help='the Clickstream host')
parser.add_argument('--writeKey', help='the Clickstream writeKey')

parser.add_argument('--iterator', type=int, default=100)
parser.add_argument('--waiting', type=int, default=1)

options = parser.parse_args()

fake = Faker(['zh_TW'])


def failed(status, msg):
    raise Exception(msg)


def track():
    analytics.track(
        user_id=fake.name(),
        anonymous_id=fake.uuid4(),
        event=fake.random_choices(elements=['Apply', 'Save', ], length=1)[0],
        properties=fake.pydict(),
        context=fake.pydict(),
    )


def page():
    analytics.page(
        user_id=fake.name(),
        anonymous_id=fake.uuid4(),
        name=fake.job(),
        properties=fake.pydict(),
        context=fake.pydict(),
    )


def screen():
    analytics.screen(
        user_id=fake.name(),
        anonymous_id=fake.uuid4(),
        name=fake.job(),
        properties=fake.pydict(),
        context=fake.pydict(),
    )


def identify():
    analytics.identify(
        user_id=fake.name(),
        anonymous_id=fake.uuid4(),
        traits=fake.pydict(),
        context=fake.pydict(),
    )


def group():
    analytics.group(
        user_id=fake.name(),
        anonymous_id=fake.uuid4(),
        group_id=fake.random_digit_not_null(),
        traits=fake.pydict(),
        context=fake.pydict(),
    )


def unknown():
    print()


analytics.host = options.host
analytics.write_key = options.writeKey
analytics.on_error = failed

log = logging.getLogger('clickstream')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)

switcher = {
    "track": track,
    "page": page,
    "screen": screen,
    "identify": identify,
    "group": group
}

total = 0
for i in tqdm(range(options.iterator)):
    func = switcher.get(
        fake.random_choices(elements=switcher.keys(), length=1)[0]
    )
    random_event_size = fake.pyint(0, 20)
    total += random_event_size
    for _ in range(random_event_size):
        func()
    sleep(options.waiting)

analytics.shutdown()

print(f'total: {total}')
