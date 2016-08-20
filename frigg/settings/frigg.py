# -*- coding: utf8 -*-

PROJECT_TMP_DIRECTORY = '/home/ubuntu/builds/frigg_working_dir/'
SERVER_ADDRESS = '127.0.0.1:8000'
GITHUB_ACCESS_TOKEN = ''

# Available options:
# assigned, unassigned, labeled, unlabeled, opened, closed, reopened, or synchronized.
IGNORED_PULL_REQUEST_ACTIONS = ['closed', 'assigned', 'unassigned', 'labeled', 'unlabeled']

FRIGG_WORKER_QUEUE = 'frigg:queue'
FRIGG_WEBHOOK_QUEUE = 'frigg:webhooks'
FRIGG_WEBHOOK_FAILED_QUEUE = 'frigg:webhooks:failed'

FRIGG_PREVIEW_IMAGE = 'frigg/frigg-test-base'

REDIS_SETTINGS = {
    'host': '127.0.0.1',
    'port': '6379',
    'db': 2
}

AUTO_APPROVE_OWNERS = ['frigg', 'frecar', 'relekang']

OVERVIEW_PAGINATION_COUNT = 100

DEFAULT_BUILD_IMAGE = "frigg/frigg-test-base"

FRIGG_KEEP_BUILD_LOGS_TIMEDELTA = 30 * 24
