# Jellyfin autobuild scripts

This section contains the scripts used to automate releases at `build.jellyfin.org`. The supporting infrastructure makes use of [Carlos Jenkins' GitHub webhooks tool](https://github.com/carlos-jenkins/python-github-webhooks) to call the `release` and, in the background, `release.d/release` scripts, which based on the passed webhook configuration decides which `build.d` script to execute.

## TL;DR flow

* The main repo, ffmpeg, and plugin repos have a Webhook that hits https://build.jellyfin.org/github-webhooks (with a secure password) when a Release action occurrs, with JSON payload
* Listening on that server is an instance of https://github.com/carlos-jenkins/python-github-webhooks running as a systemd service, which listens for the Release actions, and calls https://github.com/joshuaboniface/jellyfin-build/blob/master/scripts/release when one occurrs
* https://github.com/joshuaboniface/jellyfin-build/blob/master/scripts/release calls https://github.com/joshuaboniface/jellyfin-build/blob/master/scripts/release.d/release in the background in order to let the webhook return immediately.
* https://github.com/joshuaboniface/jellyfin-build/blob/master/scripts/release.d/release parses the webhook response, determining which repo and repo type it is, what command to run, whether another build job is running (they will wait indefinitely), and sets up logging
* That script calls one of the scripts in https://github.com/joshuaboniface/jellyfin-build/tree/master/scripts/build.d depending on the repo
* These scripts are mostly the same, for instance this is the main one: https://github.com/joshuaboniface/jellyfin-build/blob/master/scripts/build.d/build-jellyfin
* The scripts call the respective build scripts in the repos, then handle collecting and renaming the artifacts, uploading them to github, pushing them via rsync to the repo.jellyfin.org server, and then finally calling another set of scripts on that side which move the files into place (i.e. under /srv/releases/server/versions/blah)
* Docker image builds occurr as separate steps in separate scripts for clarity, which are called in the best location in their respective mail build.d scripts
