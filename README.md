# Jellyfin Build Infrastructure (Preview)

Very *very* WIP.

Goal: build any or all components of Jellyfin.

## What works?

* Cloning all repositories.
* Building plugins including manifest.json

## Basics

Cloned repos go into the `projects/` directory organized by `type` in `manifest.yaml`. Output binaries go into the `bin/` directory, organized by name.

To get started, clone all repos:

```
./build.py --list-projects
./build.py --clone-only all
```

Clone only plugins:

```
./build.py --clone-only plugins
```

Build a single plugin:

```
cp build.yaml.sample projects/plugin/jellyfin-plugin-anime/build.yaml
$EDITOR projects/plugin/jellyfin-plugin-anime/build.yaml
<change values as appropriate>
./build.py jellyfin-plugin-anime
```

Resulting full manifest in `bin/plugin_manifest.json`. Output DLL in `bin/jellyfin-plugin-anime/`.

Makes tons of assumptions right now, will fix.
