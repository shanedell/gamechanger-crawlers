import os
import json
import urllib.request as urq


def send_notification(message: str, SLACK_HOOK_CHANNEL_ID=None, SLACK_HOOK_URL=None, use_env_vars=True):
    headers = {"Content-Type": "application/json"}
    method = "POST"

    if use_env_vars:
        should_send = os.environ.get("SEND_NOTIFICATIONS")
        channel_id = os.environ.get("SLACK_HOOK_CHANNEL_ID")

        data = json.dumps({
            "channel": channel_id,
            "text": message
        }).encode("utf-8")

        if should_send:
            url = os.environ.get("SLACK_HOOK_URL")

            req = urq.Request(
                url=url,
                method=method,
                data=data,
                headers=headers
            )

            res = urq.urlopen(url=req)
        else:
            print("SEND_NOTIFICATIONS env not set, did not send:\n", data)

    else:
        print("SENDING NOTIFICATIONS!!")
        data = json.dumps({
            "channel": SLACK_HOOK_CHANNEL_ID,
            "text": message
        }).encode("utf-8")

        req = urq.Request(
            url=SLACK_HOOK_URL,
            method=method,
            data=data,
            headers=headers
        )

        res = urq.urlopen(url=req)
