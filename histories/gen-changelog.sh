#!/bin/bash
branch="${1}"
prev_minor="${2}"
cur_minor="${3}"

if [[ -z ${prev_minor} || -z ${cur_minor} ]]; then
    echo "Specify previous and current minor release tags (e.g. 'v10.4.0' and 'v10.5.0')"
    exit 1
fi

curdir="$( pwd )"

for repo in jellyfin jellyfin-web; do

pushd ../projects/server/${repo} &>/dev/null
cur_branch="$( git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1 /' )"
git checkout upstream/${branch} &>/dev/null

if git tag | grep -q ${cur_minor}; then
    target="${cur_minor}"
else
    target="HEAD"
fi

all_merges="$( git log --grep 'Merge pull request' --oneline --single-worktree --first-parent ${prev_minor}..${target} )"

echo "### [${repo}](https://github.com/jellyfin/${repo}) [$( wc -l <<<"${all_merges}" )]"
echo

awk '{ print $1 }' <<<"${all_merges}" | while read merge; do
    msg="$( git show --no-patch ${merge} )"
    pr_id="$( grep -Eo '#[0-9]+' <<<"${msg}" | head -1 | tr -d '#' | perl -pe 'chomp' )"

    /usr/local/bin/hub pr show -f " * %i [@%au] %t" ${pr_id}

done | sort -rn 
echo

git checkout ${cur_branch} &>/dev/null
popd &>/dev/null

done > ${curdir}/changelog_${cur_minor}
