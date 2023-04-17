import json
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

batch = {
    "batch": [
        {
            "timestamp": "2022-08-26T09:34:12.028Z",
            "integrations": {},
            "anonymousId": "0603629a-4f93-4c63-9464-06bc8a24dfae",
            "event": "hi",
            "type": "track",
            "properties": {},
            "context": {
                "page": {
                    "path": "/",
                    "referrer": "",
                    "search": "?writeKey=default",
                    "title": "",
                    "url": "http://localhost/?writeKey=default"
                },
                "userAgent": "user-agent",
                "locale": "en-US",
                "library": {"name": "analytics.js", "version": "next-1.42.3"},
                "campaign": {}
            },
            "messageId": "ajs-next-391a4cc49cb833762daa05c3c0ba8198",
            "writeKey": "default",
            "userId": None,
            "sentAt": "2022-08-26T09:34:12.037Z",
            "_metadata": {
                "bundled": ["Segment.io"],
                "unbundled": [],
                "bundledIds": []
            }
        },
        {
            "timestamp": "2022-08-26T09:34:12.624Z",
            "integrations": {},
            "userId": "hi",
            "anonymousId": "0603629a-4f93-4c63-9464-06bc8a24dfae",
            "type": "identify",
            "traits": {},
            "context": {
                "page": {
                    "path": "/",
                    "referrer": "",
                    "search": "?writeKey=default",
                    "title": "",
                    "url": "http://localhost/?writeKey=default"
                },
                "userAgent": "user-agent",
                "locale": "en-US",
                "library": {"name": "analytics.js", "version": "next-1.42.3"},
                "campaign": {}
            },
            "messageId": "ajs-next-cd1980c376d80065c87c2ee2302d2404",
            "writeKey": "default",
            "sentAt": "2022-08-26T09:34:12.627Z",
            "_metadata": {
                "bundled": ["Segment.io"],
                "unbundled": [],
                "bundledIds": []
            }
        }
    ],
    "writeKey": "default"
}


def test_batch():
    response = client.post('/v1/batch', data=json.dumps(batch))
    assert response.status_code == 200

def test_batch():
    response = client.post('/v1/batch', json=batch)
    assert response.status_code == 200
