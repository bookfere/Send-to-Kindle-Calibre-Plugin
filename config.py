from calibre.utils.config import JSONConfig


preferences = JSONConfig('plugins/send_to_kindle')
preferences.defaults['kindle_email'] = []


def get_config(key, default=None):
    if key in preferences:
        return preferences[key]
    return default


def set_config(key, value):
    preferences[key] = value
