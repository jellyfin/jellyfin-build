#!/usr/bin/env python3

import os, sys, yaml, json, subprocess, datetime

import manifest

cwd = os.getcwd()

def run_os_command(command, environment=None):
    command_output = subprocess.run(
        command.split(),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return command_output.stdout.decode('utf8'), command_output.returncode

def build_plugin(project):
    # Schema:
    # build_type: dotnet|docker|script
    # dotnet_runtime: the runtime for dotnet builds
    # dotnet_configuration: the configuration for dotnet builds
    # dotnet_framework: the framework for dotnet builds
    # docker_file: the Dockerfile for docker builds
    # script_path: the path for script builds

    # Extract our name and type
    project_name = project['name']
    project_type = project['type']
    # Set out the directories
    type_dir = "{}/projects/{}".format(cwd, project_type)
    project_dir = "{}/projects/{}/{}".format(cwd, project_type, project_name)
    # Check if a build configuration exists and load it
    manifest_file = '{}/build.yaml'.format(project_dir)
    if not os.path.exists(manifest_file):
        print("ERROR: Project {} does not contain a valid 'build.yaml' file.".format(project['name']))
        return False
    build_cfg = manifest.load_manifest(manifest_file)

    project_version = build_cfg['version']

    # move into the project directory
    revdir = os.getcwd()
    os.chdir(project_dir)

    if build_cfg['build_type'] == 'dotnet':
        build_command = "dotnet publish --self-contained --runtime {} --configuration {} --framework {} --output ../bin/".format(
            build_cfg['dotnet_runtime'],
            build_cfg['dotnet_configuration'],
            build_cfg['dotnet_framework']
        )
        run_os_command(build_command)
    else:
        print("ERROR: Unsupported build type.")
        return False

    # Move back to the previous directory
    os.chdir(revdir)
    
    # Collect artifacts
    src_dir = "{}/bin".format(project_dir)
    target_dir = "./bin/{}".format(project_name)
    # Get a sensible name
    new_name = "{}_{}.dll".format(project_name, project_version)
    # Make the type dir if it doesn't exist
    if not os.path.isdir(target_dir):
        os.makedirs(target_dir)

    stdout, retcode = run_os_command("mv {}/{} {}/{}".format(src_dir, build_cfg['artifacts'], target_dir, new_name))
    if retcode:
        return False

    bin_md5sum = run_os_command("md5sum {}/{}".format(target_dir, new_name))[0].split()[0]

    generate_plugin_manifest(project, build_cfg, bin_md5sum)

    return True

def generate_plugin_manifest(project, build_cfg, bin_md5sum):
    # Extract our name, type, and plugin_id
    project_name = project['name']
    project_type = project['type']
    project_description = project['description']
    project_plugin_nicename = project['plugin_nicename']
    project_plugin_overview = project['plugin_overview']
    project_plugin_id = project['plugin_id']
    project_plugin_category = project['plugin_category']
    project_plugin_guid = project['plugin_guid']
    project_version = build_cfg['version']

    build_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    plugin_manifest_fragment = {
        "id": project_plugin_id,
        "name": project_plugin_nicename,
        "shortDescription": project_description,
        "overview": project_plugin_overview,
        "isPremium": False,
        "richDescUrl": "",
        "thumbImage": "",
        "previewImage": "",
        "type": "UserInstalled",
        "targetFilename": "{0}_{1}.dll".format(project_name, project_version),
        "owner": "jellyfin",
        "category": project_plugin_category,
        "titleColor": "#FFFFFF",
        "featureId": project_plugin_nicename,
        "regInfo": "",
        "price": 0.00,
        "targetSystem": "Server",
        "guid": project_plugin_guid,
        "adult": 0,
        "totalRatings": 1,
        "avgRating": 5,
        "isRegistered": False,
        "expDate": None,
        "installs": 0,
        "versions": [
            {
                "name": project_plugin_nicename,
                "versionStr": project_version,
                "classification": "Release",
                "description": "Release",
                "requiredVersionStr": "10.1.0",
                "sourceUrl": "https://repo.jellyfin.org/releases/plugin/{0}/{0}_{1}.dll".format(project_name, project_version),
                "targetFilename": "{0}_{1}.dll".format(project_name, project_version),
                "checksum": bin_md5sum,
                "packageId": project_plugin_id,
                "timestamp": build_date,
                "runtimes": "netframework,netcore"
            }
        ]
    }
    target_dir = "./bin/{}".format(project_name)
    manifest_fragment_file_name = "{}/{}.manifest.json".format(target_dir, project_name)
    with open(manifest_fragment_file_name, 'w') as manifest_fragment_file:
        json.dump(plugin_manifest_fragment, manifest_fragment_file, sort_keys=True, indent=4)
    print("Wrote plugin manifest fragment to {}".format(manifest_fragment_file_name))
