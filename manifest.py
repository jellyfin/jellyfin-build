#!/usr/bin/env python3 

import yaml

# Load in the manifest file
def load_manifest():
    manifest_file = "manifest.yaml"
    with open(manifest_file, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)['jellyfin-manifest']

    server_packages = cfg['server-packages']
    jellyfin_projects = cfg['projects']

    return server_packages, jellyfin_projects
