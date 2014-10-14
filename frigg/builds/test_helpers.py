# -*- coding: utf8 -*-
from unittest import TestCase
from frigg.builds.helpers import _detect_test_runners


class SmokeTestCase(TestCase):

    def test__detect_test_runners(self):
        self.assertEqual(_detect_test_runners([]), [])
        files = ['package.json', 'manage.py', 'setup.py', 'tox.ini', 'Makefile']
        self.assertEqual(_detect_test_runners(files), ['make test'])
        del files[4]
        self.assertEqual(_detect_test_runners(files), ['tox', 'flake8'])
        del files[3]
        self.assertEqual(_detect_test_runners(files), ['python setup.py test', 'flake8'])
        del files[2]
        self.assertEqual(_detect_test_runners(files), ['python manage.py test', 'flake8'])
        del files[1]
        self.assertEqual(_detect_test_runners(files), ['npm test'])
