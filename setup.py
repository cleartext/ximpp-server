from setuptools import setup, find_packages

setup(
    name = 'cleartext-microblog',
    version = '0.1.0',
    description = 'Cleartext microblogging XMPP bot',
    author = 'Alexander Artemenko',
    packages = find_packages(),
    entry_points = {
        'console_scripts': [
            'bot = microblog.server:main',
        ]
    },
    zip_safe = True,
)

