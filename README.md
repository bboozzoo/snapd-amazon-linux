snapd packaging for Amazon Linux 2

#### Build & Publish

Use the `tool` to build the package and create a YUM compatible repository
structure.

To build the RPMs use `tool build`. The build is done using `$PWD/rpmbuild` as
`%_topdir`.

To create a repository structure run `tool createrepo`. The repository structure
is initialized under `$PWD/repo`.

Use `tool repoconf <$baseurl>` to generate a suitable yum `*.repo` file.

#### Packaging

The package uses the Fedora/EPEL package as base
https://src.fedoraproject.org/rpms/snapd and adds the following tweaks:

- disable SELinux (since it's not supported by AMZN2 kernels)
- set up  /snap -> /var/lib/snapd/snap symlink out of the box
