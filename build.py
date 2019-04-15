#!/usr/bin/env python3

# build.py: Collect components of Jellyfin and build them.

import os, sys, argparse, json

import manifest
import build_plugin
import build_server
import build_ffmpeg
import build_client

cwd = os.getcwd()

# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "project",
    help="Jellyfin project(s) to fetch and build. Must be 'all', a project type, or an individual project defined in 'projects_manifest.yaml'.",
    nargs='?'
)
parser.add_argument(
    "package",
    help="Package type(s) to build. Must be 'all' or a package type defiled in the project 'build.yaml'. Used by server and client build types.",
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
    help="List all valid projects in 'projects_manifest.yaml' and exit.",
    action='store_true'
)
parser.add_argument(
    "--clone-only",
    help="Clone the specified projects but don't attempt a build.",
    action='store_true'
)
parser.add_argument(
    "--web-target",
    help="For supported projects, the jellyfin-web branch/tag to use.",
    default=['master'], nargs=1
)
args = parser.parse_args()

# Parse out the manifest sections
cfg = manifest.load_manifest('{}/projects_manifest.yaml'.format(cwd))
jellyfin_projects = cfg['jellyfin-manifest']

full_projects_list = list()
full_types_list = list()
for project in jellyfin_projects:
    full_projects_list.append(project['name'])
    full_types_list.append(project['type'])

if args.list_projects:
    print("Project types:")
    print(" > " + " \n > ".join(set(full_types_list)))
    print("All projects:")
    print("   {name: <40} {ptype: <10}".format(name='Name', ptype='Type'))
    for project in jellyfin_projects:
        print(" > {name: <40} {ptype: <10}".format(name=project['name'], ptype=project['type']))

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
    print("ERROR: Project or type '{project}' is not in the manifest.".format(project=args.project))
    sys.exit(1)

# Check if we built any plugins to update final manifest
updated_plugin = False

def clone_project(project):
    """
    Clone a project from its Git URL.
    """
    # Extract our name and type
    project_name = project['name']
    project_type = project['type']
    project_url = project['url']
    print("-> Cloning project '{name}'".format(name=project_name))
    # Set out the directories
    type_dir = "{cwd}/projects/{ptype}".format(cwd=cwd, ptype=project_type)
    project_dir = "{cwd}/projects/{ptype}/{name}".format(cwd=cwd, ptype=project_type, name=project_name)
    # Determine our clone command
    if args.method[0] == 'ssh':
        clone_cmd = "git clone git@{url} {pdir}".format(url=project_url, pdir=project_dir)
    else:
        clone_cmd = "git clone https://{url} {pdir}".format(url=project_url, pdir=project_dir)
    # Make the type dir if it doesn't exist
    if not os.path.isdir(type_dir):
        os.makedirs(type_dir)
    # Clone the project if it doesn't exist
    if not os.path.isdir(project_dir):
        try:
            os.system(clone_cmd)
        except Exception as e:
            print("ERROR: Failed to clone project {name}: {err}".format(name=project_name, err=e))
            return False
    else:
        print("Project is already cloned.")

    return True

def build_project(project):
    global updated_plugin
    # Extract our name and type
    project_name = project['name']
    project_type = project['type']
    if not args.package:
        package = 'all'
    else:
        package = args.package
    print("-> Building project '{name}'".format(name=project_name))
    # Build the project
    if project['type'] == 'plugin':
        result = build_plugin.build_plugin(project)
        if result:
            updated_plugin = True
    elif project['type'] == 'client':
        result = build_client.build_client(project, package, args.web_target[0])
    elif project['type'] == 'server':
        result = build_server.build_server(project, package)
    elif project['type'] == 'ffmpeg':
        result = build_ffmpeg.build_ffmpeg(project, package)
    elif project['type'] == 'meta':
        # Meta projects have no build component
        pass
    else:
        print("ERROR: Invalid project type.")

# Clone and build each project in turn
for project in jellyfin_projects:
    # Continue if project is not chosen
    if not project['name'] in projects_list:
        continue
    # Clone the project
    result = clone_project(project)
    if not result or args.clone_only:
        continue
    # Build the project
    result = build_project(project)
    if not result:
        continue
    print("Successfully processed project {name}".format(name=project['name']))

# Update the plugin manifest
if updated_plugin:
    plugin_manifest_list = list()
    for project in jellyfin_projects:
        if project['type'] == 'plugin':
            # Read in the fragment
            project_manifest_fragment_file = "{cwd}/bin/{name}/{name}.manifest.json".format(cwd=cwd, name=project['name'])
            if not os.path.exists(project_manifest_fragment_file):
                continue

            with open(project_manifest_fragment_file) as project_manifest_fragment:
                project_manifest_fragment = json.load(project_manifest_fragment)
            plugin_manifest_list.append(project_manifest_fragment)

    output_manifest_file_name = "{cwd}/bin/jellyfin-plugin_manifest.json".format(cwd=cwd)
    with open(output_manifest_file_name, 'w') as output_manifest_file:
        json.dump(plugin_manifest_list, output_manifest_file, sort_keys=True, indent=4)
    print("Wrote updated combined plugin manifest to {}".format(output_manifest_file_name))
