#!/usr/bin/env python3

import os, sys, yaml, json, subprocess, datetime

import manifest

cwd = os.getcwd()

def run_os_command(command, environment=None, shell=False):
    if shell:
        cmd = command
    else:
        cmd = command.split()

    try:
        command_output = subprocess.run(
            cmd,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell
        )
    except Exception as e:
        print(e)
        print(command_output)

    return command_output.stdout.decode('utf8'), command_output.stderr.decode('utf8'), command_output.returncode

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

    project_version = "{}.0".format(build_cfg['version'])

    # move into the project directory
    revdir = os.getcwd()
    os.chdir(project_dir)

    if build_cfg['build_type'] == 'dotnet':
        restore_command = "dotnet restore --no-cache"
        stdout, stderr, retcode = run_os_command(restore_command)
        if retcode:
            print(stdout)
            print(stderr)
            exit(1)

        build_command = "dotnet publish --configuration {} --framework {} --output ./bin/".format(
            build_cfg['dotnet_configuration'],
            build_cfg['dotnet_framework']
        )
        stdout, stderr, retcode = run_os_command(build_command)
        if retcode:
            print(stdout)
            print(stderr)
            exit(1)
        print(stdout)
    elif build_cfg['build_type'] == 'build.py':
        build_command = "python3 build.py"
        stdout, stderr, retcode = run_os_command(build_command)
        if retcode:
            print(stdout)
            print(stderr)
            exit(1)
    else:
        print("ERROR: Unsupported build type.")
        return False

    raw_bin_dir = "{}/bin".format(project_dir)
    os.chdir(raw_bin_dir)

    # Get a sensible name
    new_name = "{}_{}.zip".format(project_name, project_version)
    # Move out the artifacts
    artifacts_list = list()
    for artifact in build_cfg['artifacts']:
        artifacts_list.append("{}".format(artifact))
    stdout, stderr, retcode = run_os_command("zip {} {}".format(new_name, ' '.join(artifacts_list)))
    if retcode:
        print('Could not archive artifacts: {}'.format(stderr))
        return False

    # Move back to the previous directory
    os.chdir(revdir)
    
    # Collect artifacts
    src_dir = "{}/bin".format(project_dir)
    target_dir = "./bin/plugin/{}".format(project_name)
    # Make the type dir if it doesn't exist
    if not os.path.isdir(target_dir):
        os.makedirs(target_dir)

    stdout, stderr, retcode = run_os_command("mv {}/{} {}/".format(src_dir, new_name, target_dir))
    if retcode:
        print('Could not move archive: {}'.format(stderr))
        return False

    # Remove build junk
    run_os_command("rm -rf {}".format(src_dir))

    bin_md5sum = run_os_command("md5sum {}/{}".format(target_dir, new_name))[0].split()[0]

    generate_plugin_manifest(project, build_cfg, bin_md5sum)

    return True

def generate_plugin_manifest(project, build_cfg, bin_md5sum):
    # Extract our name, type, and plugin_id
    project_name = project['name']
    project_type = project['type']
    project_plugin_id = project['plugin_id']
    project_plugin_guid = build_cfg['guid']
    project_plugin_nicename = build_cfg['nicename']
    project_plugin_overview = build_cfg['overview']
    project_plugin_description = build_cfg['description']
    project_plugin_category = build_cfg['category']
    project_plugin_owner = build_cfg['owner']
    project_version = "{}.0".format(build_cfg['version'])

    jellyfin_version = build_cfg['jellyfin_version']

    build_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    target_dir = "./bin/plugin/{}".format(project_name)
    manifest_fragment_file_name = "{}/{}.manifest.json".format(target_dir, project_name)

    plugin_manifest_versions = list()
    plugin_manifest_existing_version_fragments = list()
    if os.path.isfile(manifest_fragment_file_name):
        with open(manifest_fragment_file_name, 'r') as manifest_fragment_file:
            old_config = json.load(manifest_fragment_file)
            for version in old_config['versions']:
                if version['versionStr'] != project_version:
                    plugin_manifest_existing_version_fragments.append(version)

    plugin_manifest_new_version_fragment = [{
        "name": project_plugin_nicename,
        "versionStr": project_version,
        "classification": "Release",
        "description": "Release",
        "requiredVersionStr": jellyfin_version,
        "sourceUrl": "https://repo.jellyfin.org/releases/plugin/{0}/{0}_{1}.zip".format(project_name, project_version),
        "targetFilename": "{0}_{1}.zip".format(project_name, project_version),
        "checksum": bin_md5sum,
        "timestamp": build_date,
        "runtimes": "netframework,netcore"
    }]
    plugin_manifest_versions = plugin_manifest_new_version_fragment + plugin_manifest_existing_version_fragments

    plugin_manifest_fragment = {
        "id": project_plugin_id,
        "packageId": project_plugin_id,
        "name": project_plugin_nicename,
        "shortDescription": project_plugin_description,
        "overview": project_plugin_overview,
        "isPremium": False,
        "richDescUrl": "",
        "thumbImage": "",
        "previewImage": "",
        "type": "UserInstalled",
        "owner": project_plugin_owner,
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
        "versions": plugin_manifest_versions
    }
    with open(manifest_fragment_file_name, 'w') as manifest_fragment_file:
        json.dump(plugin_manifest_fragment, manifest_fragment_file, sort_keys=True, indent=4)
    print("Wrote plugin manifest fragment to {}".format(manifest_fragment_file_name))
