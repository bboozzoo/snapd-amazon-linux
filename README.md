snapd packaging for Amazon Linux 2

#### How to use the repositories

The repository for Amazon Linux 2 and Amazon Linux 2023 is hosted directly on
GitHub under https://bboozzoo.github.io/snapd-amazon-linux See the instructions
below for installation steps on your system.

##### Amazon Linux 2023

```
wget -O /etc/yum.repos.d/snapd.repo \
    https://bboozzoo.github.io/snapd-amazon-linux/al2023/snapd.repo
dnf install snapd -y
```

##### Amazon Linux 2

```
wget -O /etc/yum.repos.d/snapd.repo \
    https://bboozzoo.github.io/snapd-amazon-linux/amzn2/snapd.repo
yum install snapd -y
systemctl enable --now snapd.socket
```

On Amazon Linux 2 the package installs with all services disabled by default.


#### Build & Publish

Use the `tool` to build the package and create a YUM compatible repository
structure.

To build the RPMs use `tool build`. The build is done using `$PWD/rpmbuild` as
`%_topdir`.

To create a repository structure run `tool createrepo`. The repository structure
is initialized under `$PWD/repo`.

Use `tool repoconf <$baseurl>` to generate a suitable yum `*.repo` file.

The `TARGET` environment variable needs to be set when then invoking the `tool`
command.

Build and create repository for Amazon Linux 2:

```sh
TARGET=amazonlinux:2 ./tool build
TARGET=amazonlinux:2 ./tool createrepo
```

Build and create repository for Amazon Linux 2023:

```sh
TARGET=amazonlinux:2023 ./tool build
TARGET=amazonlinux:2023 ./tool createrepo
```

#### Packaging

The package uses the Fedora/EPEL package as base
https://src.fedoraproject.org/rpms/snapd and adds the following tweaks:

- disable SELinux (since it's not supported by AMZN2 kernels)
- set up  /snap -> /var/lib/snapd/snap symlink out of the box

#### Testing

Use the spread tool to run a smoke test suite with prebuilt packages like so:

```sh
spread -v google:amazon-linux-2-64:spread/prebuilt/...
```

Make sure the Github action artifact was extracted and placed is located at the
top directory.

A repository and packages can be built using spread like so:

```sh
spread -v -artifacts=./artifacts google:amazon-linux-2-64:spread/build/package-and-repo
```
