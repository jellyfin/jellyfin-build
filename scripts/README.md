# Jellyfin autobuild scripts

This section contains the scripts used to automate releases at `build.jellyfin.org`. The supporting infrastructure makes use of [Carlos Jenkins' GitHub webhooks tool](https://github.com/carlos-jenkins/python-github-webhooks) to call the `release` and, in the background, `release.d/release` scripts, which based on the passed webhook configuration decides which `build.d` script to execute.
