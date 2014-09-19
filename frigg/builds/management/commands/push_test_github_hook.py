# -*- coding: utf8 -*-

from django.core.management.base import BaseCommand
import requests
from frigg.builds.models import Build
import json


class Command(BaseCommand):
    def handle(self, *args, **options):
        data_from_github = {
            "ref": "refs/heads/master",
            "after": "6ebe61b9e030ff7f23d514f9f9ee7b1760b548c8",
            "before": "8163d92c511bbfaa7777b99ad2341c3344d8a10f",
            "created": False,
            "deleted": False,
            "forced": False,
            "compare": "https://github.com/tind/tind.io/compare/8163d92c511b...6ebe61b9e030",
            "commits": [
                {
                    "id": "6ebe61b9e030ff7f23d514f9f9ee7b1760b548c8",
                    "distinct": True,
                    "message": "add shebang line",
                    "timestamp": "2014-05-31T12:56:10+02:00",
                    "url": "https://github.com/tind/tind.io/commit/"
                           "6ebe61b9e030ff7f23d514f9f9ee7b1760b548c8",
                    "author": {
                        "name": "Fredrik Nygård Carlsen",
                        "email": "me@frecar.no",
                        "username": "frecar"
                    },
                    "committer": {
                        "name": "Fredrik Nygård Carlsen",
                        "email": "me@frecar.no",
                        "username": "frecar"
                    },
                    "added": [

                    ],
                    "removed": [

                    ],
                    "modified": [
                        "deploy.sh"
                    ]
                }
            ],
            "head_commit": {
                "id": "6ebe61b9e030ff7f23d514f9f9ee7b1760b548c8",
                "distinct": True,
                "message": "add shebang line",
                "timestamp": "2014-05-31T12:56:10+02:00",
                "url": "https://github.com/tind/tind.io/commit/"
                       "6ebe61b9e030ff7f23d514f9f9ee7b1760b548c8",
                "author": {
                    "name": "Fredrik Nygård Carlsen",
                    "email": "me@frecar.no",
                    "username": "frecar"
                },
                "committer": {
                    "name": "Fredrik Nygård Carlsen",
                    "email": "me@frecar.no",
                    "username": "frecar"
                },
                "added": [

                ],
                "removed": [

                ],
                "modified": [
                    "deploy.sh"
                ]
            },
            "repository": {
                "id": 11238350,
                "name": "tind.io",
                "url": "https://github.com/tind/tind.io",
                "description": "",
                "watchers": 0,
                "stargazers": 0,
                "forks": 0,
                "fork": False,
                "size": 11072,
                "owner": {
                    "name": "tind",
                    "email": "team@tind.io"
                },
                "private": True,
                "open_issues": 2,
                "has_issues": True,
                "has_downloads": True,
                "has_wiki": True,
                "language": "JavaScript",
                "created_at": 1373223637,
                "pushed_at": 1401533786,
                "master_branch": "master",
                "organization": "tind"
            },
            "pusher": {
                "name": "frecar",
                "email": "me@frecar.no"
            }
        }

        r = requests.post("http://localhost:8000/github-webhook/",
                          data=json.dumps(data_from_github),
                          headers={'X-GitHub-Event': "push"})
        print(r.text)