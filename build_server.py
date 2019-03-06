#!/usr/bin/env python3

import os, sys, yaml, json, subprocess, datetime

import manifest

cwd = os.getcwd()

def run_os_command(command, environment=None):
    try:
        command_output = subprocess.run(
            command.split(),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        print(e)
        print(command_output)

    return command_output.stdout.decode('utf8'), command_output.stderr.decode('utf8'), command_output.returncode

def build_server(project, package):
    # Extract our name and type
    project_name = project['name']
    project_type = project['type']

    # We don't (yet) do anything with jellyfin-web itself
    if project_name == 'jellyfin-web':
        return True

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
    project_packages = build_cfg['packages']

    packages_list = list()
    if package == 'all':
        packages_list = project_packages
    else:
        if package in project_packages:
            packages_list.append(package)
        else:
            print('ERROR: Package type {} is not valid. Valid packages are:'.format(package))
            print('\n > '.join(project_packages))
            return False

    # move into the project directory
    revdir = os.getcwd()
    # Build each package type
    for package in packages_list:
        os.chdir(project_dir)

        # We wrap `build` so we expect it to be sane and like what we send it
        subprocess.call('./build -k -b local {} all'.format(package), shell=True)

        # Move back to the previous directory
        os.chdir(revdir)
    
        # Collect artifacts
        src_dir = "{}/bin/{}".format(type_dir, package)
        target_dir = "./bin/{}".format(project_name)
        # Make the type dir if it doesn't exist
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)
        # Clean out the old target dir
        stdout, stderr, retcode = run_os_command("rm -rf {}/{}".format(target_dir, package))
        if retcode:
            print('Could not remove old archive: {}'.format(stderr))
            return False
        # Move the artifacts
        stdout, stderr, retcode = run_os_command("mv {} {}/".format(src_dir, target_dir))
        if retcode:
            print('Could not move archive: {}'.format(stderr))
            return False

        # Remove build junk
        run_os_command("rm -rf {}".format(src_dir))

    return True
