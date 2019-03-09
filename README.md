# Jellyfin Build Infrastructure

This repository contains a unified build infrastructure, written in Python 3, for the Jellyfin project. It can be used to clone down, build, and release (to the server of your choosing) the various packages and components of Jellyfin.

This infrastructure is not 100% complete. Currently it's able to build:

* The main Jellyfin server by wrapping its BASH `build` script. This includes the Jellyfin WebUI as an integrated submodule.
* The Jellyfin Android and AndroidTV apps by wrapping their BASH `build` scripts.
* The Jellyfin Debian/Ubuntu FFMPEG by wrapping its BASH `build` script.
* Various Jellyfin plugins, described in `projects_manifest.yaml`, including their plugin repository metadata.

This project is primarily created and maintained by Joshua Boniface to facilitate making official Jellyfin releases as well as test various development efforts. Feedback is welcome but this must always conform to its primary usecase.

## Prerequisites

Every project build by this infrastructure requires:

1. An entry in the `projects_manifest.yaml` file.
2. A `build.yaml` configuration inside the target repository.

All officially supported repositories will have these configurations. To add your own, see the various `build.yaml.*.sample` files in this repository, copy one into your repository, then submit a pull request.

As a user of this infrastructure, you should note:

1. The repositories under the `projects/` directory are safe to develop in, and in fact is designed to facilitate organizing them for heavy, multi-repository contributors.
2. If you have existing repositories, you may move them directly to the required location and use them immediately.

## Installation

1. Clone this project onto your system.

1. Install the required Python `yaml` dependency via your package manager of choice.

1. Install Docker, as this is used by many of the automated build setups.

1. Install the Microsoft .NET Core SDK for your system.

1. Initialize one or more projects.

1. Build the projects.

## Usage Examples

Obtain a full help:

```
./build.py -h
```

List the available projects and their type:

```
./build.py --list-projects
```

Clone a copy of all projects into the `projects/` directory:

```
./build.py --clone-only all
```

Clone only the plugins category:

```
./build.py --clone-only plugins
```

Build a single plugin, outputting the resulting binary packages into the `bin/` directory:

```
./build.py jellyfin-plugin-anime
```

The resulting full plugin manifest is in `bin/plugin_manifest.json`. Output ZIP packages are in `bin/jellyfin-plugin-anime/`.

Build the Jellyfin server package for Debian, from the `master` branch:

```
./build.py server debian-package-x64
```

Build the Jellyfin server packages for all supported architectures and systems, from the `v10.2.2` tag:

```
pushd projects/server/jellyfin
git checkout tags/v10.2.2
git submodule update --init
popd
./build.py server all
```

Note that the `build.py` script uses the current active branche of the project under the `projects/` directory.

Build the Jellyfin Android debug APK:

```
./build.py jellyfin-android debug
```
