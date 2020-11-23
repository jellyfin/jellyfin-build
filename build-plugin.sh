#!/bin/bash
#
# Copyright (c) 2020 - Odd Strabo <oddstr13@openshell.no>
#
#
# The Unlicense
# =============
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org/>
#

set -o errexit

MY=$(dirname $(realpath -s "${0}"))
JPRM="jprm"

DEFAULT_REPO_DIR="/srv/repository/releases/plugin/manifest-stable.json"
DEFAULT_REPO_URL="https://repo.jellyfin.org/releases/plugin/"

JELLYFIN_REPO=${JELLYFIN_REPO:-${DEFAULT_REPO_DIR}}
JELLYFIN_REPO_URL=${JELLYFIN_REPO_URL:-${DEFAULT_REPO_URL}}

PLUGIN="${1}"
UNSTABLE="${2}"

if [[ -z ${PLUGIN} ]]; then
    exit 1
fi
if [[ -z ${UNSTABLE} ]]; then
    UNSTABLE=""
else
    UNSTABLE="unstable"
fi

META_VERSION=$(grep -Po '^ *version: * "*\K[^"$]+' "${PLUGIN}/build.yaml")

if [[ -n ${UNSTABLE} ]]; then
    dotnet nuget add source -n jellyfin-unstable https://pkgs.dev.azure.com/jellyfin-project/jellyfin/_packaging/unstable%40Local/nuget/v3/index.json > /dev/null
    dotnet nuget enable source jellyfin-unstable
    VERSION_SUFFIX="$( date -u '+%y%m.%d%H.%M%S' )"
    VERSION=$( echo $META_VERSION | sed 's/\.[0-9]*\.[0-9]*\.[0-9]*$/.'"$VERSION_SUFFIX"'/' )
else
    VERSION=${META_VERSION}
fi

pushd "${PLUGIN}"
    git reset --hard
    git clean -fd
    find . -type d -name obj -exec rm -r {} \; || true
    find . -type d -name bin -exec rm -r {} \; || true
    git fetch --all --tags
    git checkout -f $(git tag --ignore-case --sort=-version:refname --list 'v*' | head -n 1)
    dotnet clean --configuration=Release
popd

ARTIFACT_DIR=${ARTIFACT_DIR:-"${MY}/artifacts"}
mkdir -p "${ARTIFACT_DIR}"

if [[ ! -f ${JELLYFIN_REPO} ]]; then
    jprm repo init ${JELLYFIN_REPO}
fi

zipfile=$($JPRM --verbosity=debug plugin build "${PLUGIN}" --output="${ARTIFACT_DIR}" --version="${VERSION}") && {
    $JPRM --verbosity=debug repo add --url=${JELLYFIN_REPO_URL} "${JELLYFIN_REPO}" "${zipfile}"
}
retcode=$?

if [[ -n ${UNSTABLE} ]]; then
    dotnet nuget disable source jellyfin-unstable
fi

exit $retcode
