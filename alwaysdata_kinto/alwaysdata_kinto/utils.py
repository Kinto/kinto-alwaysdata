import hashlib
import hmac
import six


def hmac_digest(secret, message, encoding='utf-8'):
    """Return hex digest of a message HMAC using secret"""
    if isinstance(secret, six.text_type):
        secret = secret.encode(encoding)
    return hmac.new(secret,
                    message.encode(encoding),
                    hashlib.sha256).hexdigest()
