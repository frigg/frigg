# frigg-hq [![Build status](https://ci.frigg.io/frigg/frigg-hq.svg)](https://ci.frigg.io/frigg/frigg-hq/last/) [![Coverage status](https://ci.frigg.io/frigg/frigg-hq/coverage.svg)](https://ci.frigg.io/frigg/frigg-hq/last/) [![Requirements Status](https://requires.io/github/frigg/frigg-hq/requirements.svg?branch=master)](https://requires.io/github/frigg/frigg-hq/requirements/?branch=master)

[![Join the chat at https://gitter.im/frigg/frigg-hq](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/frigg/frigg-hq?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

## Setup
```
make
```

### Settings that need to be setup
Add these to `frigg.settings.local`.

* `PROJECT_TMP_DIRECTORY` - The location you want frigg to clone and test projects.
* `SERVER_ADDRESS` - To get the correct domain in comments on Github etc.
* `GITHUB_ACCESS_TOKEN` - Token needed to make the project able to post comments on Github.

### Install sass (compass) dependency
```
gem update --system
gem install compass
```

### Install Redis
```
apt-get install redis
```

### Webhooks through frigg-dispatcher
The webhooks will work out with just this project. However, it is possible to use [frigg-dispatcher](https://github.com/frigg/frigg-dispatcher) as a broker. In order to do so, the management command `fetch_webhook_payload` needs to be setup with supervisor.

## Add projects
Add `http://<your frigg domain>/github-webhook` to the projects webhooks on Github.

### Config file
Frigg supports config file to give details about what kind of tasks to perform. The file
should be named `.frigg.yml` and placed in the root of the project. More information about
the config file can be found in the documentation on [frigg.io](https://frigg.io/).
