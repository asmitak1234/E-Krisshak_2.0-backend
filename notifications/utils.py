import os
from pywebpush import webpush, WebPushException

def send_push_notification(subscription_info, message):
    try:
        webpush(
            subscription_info=subscription_info,
            data=message,
            vapid_private_key=os.getenv("VAPID_PRIVATE_KEY"),
            vapid_public_key=os.getenv("VAPID_PUBLIC_KEY"),
            vapid_claims={"sub": os.getenv("VAPID_SUBJECT")}
        )
    except WebPushException as ex:
        print(f"Push failed: {ex}")
