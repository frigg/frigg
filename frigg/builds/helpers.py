# -*- coding: utf8 -*-
from os import listdir
from os.path import isfile, join


def detect_test_runners(build):
    files = _list_files(build.working_directory)
    return _detect_test_runners(files)


def _detect_test_runners(files):
    if 'Makefile' in files:
        return ['make test']
    if 'tox.ini' in files:
        return ['tox', 'flake8']
    if 'setup.py' in files:
        return ['python setup.py test', 'flake8']
    if 'manage.py' in files:
        return ['python manage.py test', 'flake8']
    if 'package.json' in files:
        return ['npm test']
    return []


def _list_files(path):
    return [f for f in listdir(path) if isfile(join(path, f))]
