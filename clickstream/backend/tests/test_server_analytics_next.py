import json
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

identify = {
    "timestamp": "2022-08-05T07:18:38.355Z",
    "integrations": {"Segment.io": True},
    "userId": "user-id-123",
    "anonymousId": "4bef259b-3cbd-487c-bcc1-c9d128786824",
    "type": "identify",
    "traits": {},
    "context": {
            "page": {
                "path": "localhost/index.html",
                "referrer": "",
                "search": "",
                "title": "",
                "url": "http://localhost/index.html"
            },
        "userAgent": "user-agent",
        "locale": "zh-TW",
        "library": {"name": "analytics.js", "version": "next-1.41.0"}
    },
    "messageId": "ajs-next-3af857cf18b4c5e63ec5c62be36d614d",
    "writeKey": "writeKey-123",
    "sentAt": "2022-08-05T07:18:38.374Z",
    "_metadata": {"bundled": ["Segment.io"], "unbundled": [], "bundledIds": []}
}
track = {
    "timestamp": "2022-08-05T07:18:38.360Z",
    "integrations": {"Segment.io": True},
    "userId": "user-id-123",
    "anonymousId": "4bef259b-3cbd-487c-bcc1-c9d128786824",
    "event": "hello",
    "type": "track",
    "properties": {},
    "context": {
            "page": {
                "path": "localhost/index.html",
                "referrer": "",
                "search": "",
                "title": "",
                "url": "http://localhost/index.html"
            },
        "userAgent": "user-agent",
        "locale": "zh-TW",
        "library": {"name": "analytics.js", "version": "next-1.41.0"}
    },
    "messageId": "ajs-next-95bf39c22d65a476515afb3021e9b9c7",
    "writeKey": "writeKey-123",
    "sentAt": "2022-08-05T07:18:38.377Z",
    "_metadata": {"bundled": ["Segment.io"], "unbundled": [], "bundledIds": []}
}
page = {
    "timestamp": "2022-08-05T07:18:38.363Z",
    "integrations": {"Segment.io": True},
    "userId": "user-id-123",
    "anonymousId": "4bef259b-3cbd-487c-bcc1-c9d128786824",
    "type": "page",
    "properties": {
            "path": "localhost/index.html",
            "referrer": "",
            "search": "",
            "title": "",
            "url": "http://localhost/index.html"
    },
    "context": {
        "page": {
            "path": "localhost/index.html",
            "referrer": "",
            "search": "",
            "title": "",
            "url": "http://localhost/index.html"
        },
        "userAgent": "user-agent",
        "locale": "zh-TW",
        "library": {"name": "analytics.js", "version": "next-1.41.0"}
    },
    "messageId": "ajs-next-1d57c00238fb09d7c04cb0411158c979",
    "writeKey": "writeKey-123",
    "sentAt": "2022-08-05T07:18:38.380Z",
    "_metadata": {"bundled": ["Segment.io"], "unbundled": [], "bundledIds": []}
}
group = {
    "timestamp": "2022-08-05T07:18:38.368Z",
    "integrations": {"Segment.io": True},
    "userId": "user-id-123",
    "anonymousId": "4bef259b-3cbd-487c-bcc1-c9d128786824",
    "type": "group",
    "traits": {},
    "groupId": "group-id-321",
    "context": {
            "page": {
                "path": "localhost/index.html",
                "referrer": "",
                "search": "",
                "title": "",
                "url": "http://localhost/index.html"
            },
        "userAgent": "user-agent",
        "locale": "zh-TW",
        "library": {"name": "analytics.js", "version": "next-1.41.0"}
    },
    "messageId": "ajs-next-72c2a971c21e119374854c735936af43",
    "writeKey": "writeKey-123",
    "sentAt": "2022-08-05T07:18:38.385Z",
    "_metadata": {"bundled": ["Segment.io"], "unbundled": [], "bundledIds": []}
}
alias = {
    "timestamp": "2022-08-05T07:18:38.370Z",
    "integrations": {"Segment.io": True},
    "userId": "alias-user-323211",
    "anonymousId": "4bef259b-3cbd-487c-bcc1-c9d128786824",
    "type": "alias",
    "context": {
            "page": {
                "path": "localhost/index.html",
                "referrer": "",
                "search": "",
                "title": "",
                "url": "http://localhost/index.html"
            },
        "userAgent": "user-agent",
        "locale": "zh-TW",
        "library": {"name": "analytics.js", "version": "next-1.41.0"}
    },
    "messageId": "ajs-next-ddaf61f752603d02f3c1100cd28fc143",
    "previousId": "user-id-123",
    "writeKey": "writeKey-123",
    "sentAt": "2022-08-05T07:18:38.399Z",
    "_metadata": {"bundled": ["Segment.io"], "unbundled": [], "bundledIds": []}
}


def test_identify():
    response = client.post('/i', data=json.dumps(identify))
    assert response.status_code == 200


def test_track():
    response = client.post('/t', data=json.dumps(track))
    assert response.status_code == 200


def test_page():
    response = client.post('/p', data=json.dumps(page))
    assert response.status_code == 200


def test_group():
    response = client.post('/g', data=json.dumps(group))
    assert response.status_code == 200


def test_alias():
    response = client.post('/a', data=json.dumps(alias))
    assert response.status_code == 200


def test_batch():
    response = client.post('/b', data=json.dumps({
        "batch": [
            identify,
            track,
            page,
            group,
            alias,
        ],
        "writeKey": "writeKey-123"
    }
    ))
    assert response.status_code == 200
