#!/usr/bin/env python3 

import yaml

def load_manifest(manifest_file_name):
    """
    Read in an arbitrary YAML manifest and return it
    """
    with open(manifest_file_name, 'r') as manifest_file:
        try:
            cfg = yaml.load(manifest_file)
        except yaml.YAMLError as e:
            print("ERROR: Failed to load YAML manifest {}: {{".format(manifest_file_name, e))
            return None
    return cfg
