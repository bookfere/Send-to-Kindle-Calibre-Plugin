from calibre.utils.config import JSONConfig


preferences = JSONConfig('plugins/send_to_kindle')

preferences.defaults = {
    'kindle_emails': [],
    'preferred_format': None,
    'delete_from_library': False,
}


def init_config():
    for key, value in preferences.defaults.items():
        if key not in preferences:
            preferences[key] = value
    return preferences


def get_config(key, default=None):
    if key in preferences:
        return preferences[key]
    return default


def set_config(key, value):
    preferences[key] = value
