#!/bin/bash

RUNTIME=${RUNTIME:-docker}
DOCKER_IMG=amazonlinux:2


#HELP: tool - a silly tool to build snapd for Amazon Linux 2
#HELP:
#HELP: commands:

#HELP:     build
#HELP:              build the snapd package under $PWD/rpmbuild
build_in_container() {
    yum install -y yum-utils rpm-build
    yum-builddep -y "$PWD/snapd.spec"

    mkdir -p "$PWD/rpmbuild/SOURCES"
    cp -av snapd_*.*-vendor.tar.xz "$PWD/rpmbuild/SOURCES/"
    find . -maxdepth 1 -name '*.patch' | while read -r name; do
        cp -av "$name" "$PWD/rpmbuild/SOURCES"
    done
    rpmbuild -ba -D "%_topdir $PWD/rpmbuild" ./snapd.spec
}

#HELP:     createrepo
#HELP:              generate a YUM repository structure under $PWD/repo
createrepo_in_container() {
    yum install -y createrepo

    mkdir -p "$PWD/repo/sources/packages"
    mkdir -p "$PWD/repo/x86_64/packages"
    find "$PWD/rpmbuild/SRPMS/" -name '*.src.rpm' -exec cp -v \{\} "$PWD/repo/sources/packages/" \;
    find "$PWD/rpmbuild/RPMS/" -name '*.rpm' -exec cp -v \{\} "$PWD/repo/x86_64/packages/" \;
    for d in "$PWD/repo/sources" "$PWD/repo/x86_64"; do
        createrepo -v "$d"
    done
}

spin_container() {
    engine="docker"
    if ! command -v "$engine" 2>/dev/null ; then
        engine="podman"
    fi
    # run a container, mount sources at /mnt, st
    "$engine" run --rm \
              -v "$PWD":/mnt \
              -w /mnt \
              -e IN_CONTAINER=1 \
              -t \
              "$DOCKER_IMG" \
              /mnt/tool "$@"
}

#HELP:     repoconf <url>
#HELP:              generate a repo file
make_repo_file() {
    local url

    if [ -z "$1" ]; then
        echo "url not provided"
        exit 1
    fi
    url="$1"
    cat <<EOF
[snapd-amzn2]
name=snapd packages for Amazon Linux 2
baseurl=$url/\$basearch
gpgcheck=0
enabled=1

[snapd-amzn2-sources]
name=snapd packages for Amazon Linux 2
baseurl=$url/sources
gpgcheck=0
enabled=0
EOF
}

cmd="$1"
shift
case "$cmd" in
    build)
        set -x
        if [ "$IN_CONTAINER" = "1" ]; then
            build_in_container "$@"
        else
            spin_container build "$@"
        fi
        ;;
    createrepo)
        set -x
        if [ -d "$PWD/repo" ]; then
            echo "repo directory already exists"
            exit 1
        fi
        if [ ! -d "$PWD/rpmbuild" ]; then
            echo "rpmbuild directory not found, run build first"
            exit 1
        fi
        if [ "$IN_CONTAINER" = "1" ]; then
            createrepo_in_container "$@"
        else
            spin_container createrepo "$@"
        fi
        ;;
    repoconf)
        make_repo_file "$1"
        ;;
    help|-h|--help|*)
        grep -E '^#HELP: ' "$0" | sed -e 's/#HELP: //'
        exit 1
        ;;
esac
