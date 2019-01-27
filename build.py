#!/usr/bin/env python3

# build.py: Collect components of Jellyfin and build them.

import os, sys, argparse, yaml, re

import manifest

# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "project",
    help="Jellyfin project(s) to fetch. Must be 'all', a project type, or an individual project defined in 'manifest.yaml'.",
    nargs='?'
)
parser.add_argument(
    "--method",
    help="GitHub fetch method. Either 'https' [default] or 'ssh'.",
    choices=['https', 'ssh'],
    default=['https'], nargs=1,
)
parser.add_argument(
    "--list-projects",
    help="List all valid projects in 'manifest.json' and exit.",
    action='store_true'
)
parser.add_argument(
    "--clone-only",
    help="Clone the specified projects but don't attempt a build.",
    action='store_true'
)
args = parser.parse_args()

# Parse out the manifest sections
server_packages, jellyfin_projects = manifest.load_manifest()

full_projects_list = list()
full_types_list = list()
full_descriptions_list = list()
for project in jellyfin_projects:
    full_projects_list.append(project['name'])
    full_types_list.append(project['type'])

if args.list_projects:
    print("Project types:")
    print(" > " + " \n > ".join(set(full_types_list)))
    print("All projects:")
    for project in jellyfin_projects:
        print(" > {}: {}".format(project['name'], project['description']))

    sys.exit(0)

if not args.project:
    print("Please specify a valid project, type, or 'all'. Use '-h' for help.")
    sys.exit(1)

# Handle getting the proper project(s) list
projects_list = list()
if args.project == 'all':
    projects_list = full_projects_list
elif args.project in full_types_list:
    projects_list = [project['name'] for project in jellyfin_projects if project['type'] == args.project]
elif args.project in full_projects_list:
    projects_list = [args.project]

if not projects_list:
    print("ERROR: Project or type '{}' is not in the manifest.")
    sys.exit(1)

# Ensure all the chosen projects are cloned
for project in jellyfin_projects:
    # Continue if project is not chosen
    if not project['name'] in projects_list:
        continue
    # Extract our name and type
    project_name = project['name']
    project_type = project['type']
    print("Cloning project '{}':".format(project_name))
    # Set out the directories
    type_dir = "./projects/{}".format(project_type)
    project_dir = "./projects/{}/{}".format(project_type, project_name)
    # Determine our clone command
    if args.method == 'ssh':
        clone_cmd = "git clone git@github.com:jellyfin/{}.git {}".format(project_name, project_dir)
    else:
        clone_cmd = "git clone https://github.com/jellyfin/{}.git {}".format(project_name, project_dir)
    # Make the type dir if it doesn't exist
    if not os.path.isdir(type_dir):
        os.makedirs(type_dir)
    # Clone the project if it doesn't exist
    if not os.path.isdir(project_dir):
        os.system(clone_cmd)
    else:
        print("Project is already cloned.")

if args.clone_only:
    sys.exit(0)

def build_project(project):
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
    type_dir = "./projects/{}".format(project_type)
    project_dir = "./projects/{}/{}".format(project_type, project_name)
    # Check if a build configuration exists and load it
    manifest_file = project_dir + '/build.yaml'
    if not os.path.exists(manifest_file):
        print("ERROR: Project {} does not contain a valid 'build.yaml' file.".format(project['name']))
        sys.exit(1)
    with open(manifest_file, 'r') as ymlfile:
        build_cfg = yaml.load(ymlfile)

    # move into the project directory
    revdir = os.getcwd()
    os.chdir(project_dir)

    if build_cfg['build_type'] == 'dotnet':
        build_command = "dotnet publish --self-contained --runtime {} --configuration {} --framework {} --output ../bin/".format(
            build_cfg['dotnet_runtime'],
            build_cfg['dotnet_configuration'],
            build_cfg['dotnet_framework']
        )
        os.system(build_command)

    # Move back to the previous directory
    os.chdir(revdir)
    
    # Collect artifacts
    src_dir = "{}/bin".format(project_dir)
    target_dir = "./bin/{}/".format(project_name)
    # Make the type dir if it doesn't exist
    if not os.path.isdir(target_dir):
        os.makedirs(target_dir)
    os.system("mv {}/{} {}/".format(src_dir, build_cfg['artifacts'], target_dir))

# Attempt to perform a build for each specified project
for project in jellyfin_projects:
    # Continue if project is not chosen
    if not project['name'] in projects_list:
        continue

    # Build the project
    build_project(project)


