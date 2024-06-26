#!/bin/bash

RUNTIME=${RUNTIME:-docker}
if [ "${IN_CONTAINER-0}" = "0" ] && [ -z "$TARGET" ]; then
    (
    echo "TARGET is unset"
    echo "use:"
    echo "  - amazonlinux:2"
    echo "  - amazonlinux:2023"
    ) >&2
    exit 1
fi
DOCKER_IMG=${TARGET}


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
    yum install -y createrepo /usr/bin/find

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
              --ulimit nofile=1024:4096 \
              -v "$PWD":/mnt \
              -w /mnt \
              -e IN_CONTAINER=1 \
              -t \
              ${EXTRA_FLAGS} \
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
[snapd-amzn]
name=snapd packages for Amazon Linux
baseurl=$url/\$basearch
gpgcheck=0
enabled=1

[snapd-amzn-sources]
name=snapd packages for Amazon Linux
baseurl=$url/sources
gpgcheck=0
enabled=0
EOF
}

#HELP:     shell
#HELP:              Open a shell in build environment
shell_in_container() {
    exec /bin/bash
}

#HELP:     pack
#HELP:              Pack the repository tree
pack() {
    case "$TARGET" in
        amazonlinux:2)
            tarball_name="amazon-linux-2-repo.tar.xz"
            ;;
        amazonlinux:2023)
            tarball_name="amazon-linux-2023-repo.tar.xz"
            ;;
        *)
            echo "unsupported target $TARGET"
            exit 1
            ;;
    esac
    tar -cJv repo > "$tarball_name"
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
    shell)
        set -x
        if [ "$IN_CONTAINER" = "1" ]; then
            exec /bin/bash
        else
            EXTRA_FLAGS=-i spin_container shell "$@"
        fi
        ;;
    pack)
        if [ ! -d "$PWD/repo" ]; then
            echo "repo directory does not exist, run 'createrepo' first"
            exit 1
        fi
        pack
        ;;
    help|-h|--help|*)
        grep -E '^#HELP: ' "$0" | sed -e 's/#HELP: //'
        exit 1
        ;;
esac
