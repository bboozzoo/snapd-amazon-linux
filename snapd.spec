%if 0%{?fedora} || 0%{?rhel} == 6
%global with_devel 1
%global with_bundled 0
%global with_debug 1
%global with_check 0
%global with_unit_test 0
%else
%global with_devel 0
%global with_bundled 0
%global with_debug 0
%global with_check 0
%global with_unit_test 0
%endif

%if 0%{?with_debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

%global provider        github
%global provider_tld    com
%global project         snapcore
%global repo            snapd
# https://github.com/snapcore/snapd
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}

# SELinux policy globals
%global polmodname snapcore-selinux
%global commit1 6331fd4a058271b0246714bc6746ab1e7ce2aa09
%global shortcommit1 %(c=%{commit1}; echo ${c:0:7})
%global snapdate 20161101
%global polmodfolder %{polmodname}-%{commit1}-%{commit1}


Name:           snapd
Version:        2.16
Release:        1%{?dist}
Summary:        A transactional software package manager
License:        GPLv3
URL:            https://%{provider_prefix}
Source0:        https://%{provider_prefix}/archive/%{version}/%{name}-%{version}.tar.gz
Patch0:         0001-dist-Add-generic-systemd-units.patch
Patch1:         0001-dirs-FEDORA-use-alternate-snap-mount-directory.patch
Patch2:         0001-docs-Fix-binary-path-referenced-in-documentation.patch
# snapcore SELinux policy
Source1:        https://gitlab.com/Conan_Kudo/snapcore-selinux/repository/archive.tar.gz?ref=%{commit1}#/%{polmodname}-%{shortcommit1}.tar.gz


# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required
ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} x86_64 %{arm}}
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}
# BuildRequires:  systemd-units
BuildRequires:  systemd
%{?systemd_requires}
Requires:       snap-confine >= 1.0.44-2
Requires:       squashfs-tools
# we need squashfs.ko loaded
Requires:       kmod(squashfs.ko)

# Force the SELinux module to be installed
Requires:       %{name}-selinux = %{version}-%{release}

%if ! 0%{?with_bundled}
BuildRequires: golang(github.com/cheggaaa/pb)
BuildRequires: golang(github.com/coreos/go-systemd/activation)
BuildRequires: golang(github.com/gorilla/context)
BuildRequires: golang(github.com/gorilla/mux)
BuildRequires: golang(github.com/gorilla/websocket)
BuildRequires: golang(github.com/gosexy/gettext)
BuildRequires: golang(github.com/jessevdk/go-flags)
BuildRequires: golang(github.com/mvo5/goconfigparser)
BuildRequires: golang(github.com/mvo5/uboot-go/uenv)
BuildRequires: golang(golang.org/x/crypto/ssh/terminal)
BuildRequires: golang(gopkg.in/check.v1)
BuildRequires: golang(gopkg.in/tomb.v2)
BuildRequires: golang(gopkg.in/yaml.v2)
BuildRequires: golang(gopkg.in/macaroon.v1)
%endif

%description
Snappy is a modern, cross-distribution, transactional package manager designed for
working with self-contained, immutable packages.

%package selinux
Summary:        SELinux module for snapd
License:        GPLv2+
BuildArch:      noarch
BuildRequires:  selinux-policy, selinux-policy-devel
Requires(post): selinux-policy-base >= %{_selinux_policy_version}
Requires(post): policycoreutils
Requires(post): policycoreutils-python-utils
Requires(pre):  libselinux-utils
Requires(post): libselinux-utils

%description selinux
This package provides the SELinux policy module to ensure snapd runs properly
under an environment with SELinux enabled.


%if 0%{?with_devel}
%package devel
Summary:       %{summary}
BuildArch:     noarch

%if 0%{?with_check} && ! 0%{?with_bundled}
%endif

Provides:      golang(%{import_path}) = %{version}-%{release}

%description devel
%{summary}

This package contains library source intended for
building other packages which use import path with
%{import_path} prefix.
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%package unit-test-devel
Summary:         Unit tests for %{name} package
%if 0%{?with_check}
#Here comes all BuildRequires: PACKAGE the unit tests
#in %%check section need for running
%endif

# test subpackage tests code from devel subpackage
Requires:        %{name}-devel = %{version}-%{release}

%description unit-test-devel
%{summary}

This package contains unit tests for project
providing packages with %{import_path} prefix.
%endif

%prep
%setup -q -n %{name}-%{version}
%patch0 -p1 -b .systemd
%patch1 -p1 -b .snapdir
%patch2 -p1 -b .docfix

# Extract source for SELinux policy module
tar xvf %{SOURCE1}

%build
# Build SELinux module
pushd ./%{polmodfolder}
make SHARE="%{_datadir}" TARGETS="snappy"
popd

# Build snapd
mkdir -p src/github.com/snapcore
ln -s ../../../ src/github.com/snapcore/snapd

%if ! 0%{?with_bundled}
export GOPATH=$(pwd):%{gopath}
%else
export GOPATH=$(pwd):$(pwd)/Godeps/_workspace:%{gopath}
%endif

%gobuild -o bin/snap %{import_path}/cmd/snap
%gobuild -o bin/snap-exec %{import_path}/cmd/snap-exec
%gobuild -o bin/snapd %{import_path}/cmd/snapd


%install
install -d -p %{buildroot}%{_bindir}
install -d -p %{buildroot}%{_libexecdir}/snapd
install -d -p %{buildroot}%{_mandir}/man1
install -d -p %{buildroot}%{_unitdir}
install -d -p %{buildroot}%{_sysconfdir}/profile.d
install -d -p %{buildroot}%{_sysconfdir}/sysconfig
install -d -p %{buildroot}%{_sharedstatedir}/snapd/assertions
install -d -p %{buildroot}%{_sharedstatedir}/snapd/desktop
install -d -p %{buildroot}%{_sharedstatedir}/snapd/mount
install -d -p %{buildroot}%{_sharedstatedir}/snapd/seccomp
install -d -p %{buildroot}%{_sharedstatedir}/snapd/snaps
install -d -p %{buildroot}%{_sharedstatedir}/snapd/snap
install -d -p %{buildroot}%{_localstatedir}/snap
install -d -p %{buildroot}%{_datadir}/selinux/devel/include/contrib
install -d -p %{buildroot}%{_datadir}/selinux/packages

# Install SELinux module
install -p -m 0644 %{polmodfolder}/snappy.if %{buildroot}%{_datadir}/selinux/devel/include/contrib
install -p -m 0644 %{polmodfolder}/snappy.pp.bz2 %{buildroot}%{_datadir}/selinux/packages

# Install snap and snapd
install -p -m 0755 bin/snap %{buildroot}%{_bindir}
install -p -m 0755 bin/snap-exec %{buildroot}%{_libexecdir}/snapd
install -p -m 0755 bin/snapd %{buildroot}%{_libexecdir}/snapd

# Install snap(1) man page
bin/snap help --man > %{buildroot}%{_mandir}/man1/snap.1

# Install all systemd units
install -p -m 0644 dist/snapd.socket %{buildroot}%{_unitdir}
install -p -m 0644 dist/snapd.service %{buildroot}%{_unitdir}
install -p -m 0644 dist/snapd.refresh.service %{buildroot}%{_unitdir}
install -p -m 0644 dist/snapd.refresh.timer %{buildroot}%{_unitdir}

# Put /var/lib/snapd/snap/bin on PATH
# Put /var/lib/snapd/desktop on XDG_DATA_DIRS
cat << __SNAPD_SH__ > %{buildroot}%{_sysconfdir}/profile.d/snapd.sh
PATH=$PATH:/var/lib/snapd/snap/bin
if [ -z "$XDG_DATA_DIRS" ]; then
    XDG_DATA_DIRS=/usr/local/share/:/usr/share/:/var/lib/snapd/desktop
else
    XDG_DATA_DIRS="$XDG_DATA_DIRS":/var/lib/snapd/desktop
fi
export XDG_DATA_DIRS
__SNAPD_SH__

# Disable re-exec by default
echo 'SNAP_REEXEC=0' > %{buildroot}%{_sysconfdir}/sysconfig/snapd

# source codes for building projects
%if 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
echo "%%dir %%{gopath}/src/%%{import_path}/." >> devel.file-list
# find all *.go but no *_test.go files and generate devel.file-list
for file in $(find . -iname "*.go" \! -iname "*_test.go") ; do
    echo "%%dir %%{gopath}/src/%%{import_path}/$(dirname $file)" >> devel.file-list
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$(dirname $file)
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> devel.file-list
done
%endif

# testing files for this project
%if 0%{?with_unit_test} && 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# find all *_test.go files and generate unit-test.file-list
for file in $(find . -iname "*_test.go"); do
    echo "%%dir %%{gopath}/src/%%{import_path}/$(dirname $file)" >> devel.file-list
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$(dirname $file)
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> unit-test-devel.file-list
done
%endif

%if 0%{?with_devel}
sort -u -o devel.file-list devel.file-list
%endif

%check
%if 0%{?with_check} && 0%{?with_unit_test} && 0%{?with_devel}
%if ! 0%{?with_bundled}
export GOPATH=%{buildroot}/%{gopath}:%{gopath}
%else
export GOPATH=%{buildroot}/%{gopath}:$(pwd)/Godeps/_workspace:%{gopath}
%endif
%gotest %{import_path}
%endif

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%files selinux
%license %{polmodfolder}/COPYING
%doc %{polmodfolder}/README.md
%{_datadir}/selinux/packages/snappy.pp.bz2
%{_datadir}/selinux/devel/include/contrib/snappy.if

%files
%license COPYING 
%doc README.md docs/*
%{_bindir}/snap
%{_libexecdir}/snapd
%{_mandir}/man1/snap.1*
%{_sysconfdir}/profile.d/snapd.sh
%{_unitdir}/snapd.socket
%{_unitdir}/snapd.service
%{_unitdir}/snapd.refresh.service
%{_unitdir}/snapd.refresh.timer
%config(noreplace) %{_sysconfdir}/sysconfig/snapd
%dir %{_sharedstatedir}/snapd
%dir %{_sharedstatedir}/snapd/assertions
%dir %{_sharedstatedir}/snapd/desktop
%dir %{_sharedstatedir}/snapd/mount
%dir %{_sharedstatedir}/snapd/seccomp
%dir %{_sharedstatedir}/snapd/snaps
%dir %{_sharedstatedir}/snapd/snap
%dir %{_localstatedir}/snap

%if 0%{?with_devel}
%files devel -f devel.file-list
%license COPYING
%doc README.md
%dir %{gopath}/src/%{provider}.%{provider_tld}/%{project}
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%files unit-test-devel -f unit-test-devel.file-list
%license COPYING
%doc README.md
%endif

%post
%systemd_post snapd.service snapd.socket snapd.refresh.timer snapd.refresh.service

%preun
%systemd_preun snapd.service snapd.socket snapd.refresh.timer snapd.refresh.service

%postun
%systemd_postun_with_restart snapd.service snapd.socket snapd.refresh.timer snapd.refresh.service

%pre selinux
%selinux_relabel_pre

%post selinux
%selinux_modules_install %{_datadir}/selinux/packages/snappy.pp.bz2
%selinux_relabel_post

%postun selinux
%selinux_modules_uninstall snappy
if [ $1 -eq 0 ]; then
    %selinux_relabel_post
fi


%changelog
* Wed Oct 19 2016 Zygmunt Krynicki <me@zygoon.pl> - 2.16-1
- New upstream release
* Tue Oct 18 2016 Neal Gompa <ngompa13@gmail.com> - 2.14-2
- Add SELinux policy module subpackage
* Tue Aug 30 2016 Zygmunt Krynicki <me@zygoon.pl> - 2.14-1
- New upstream release
* Tue Aug 23 2016 Zygmunt Krynicki <me@zygoon.pl> - 2.13-1
- New upstream release
* Thu Aug 18 2016 Zygmunt Krynicki <me@zygoon.pl> - 2.12-2
- Correct license identifier
* Thu Aug 18 2016 Zygmunt Krynicki <me@zygoon.pl> - 2.12-1
- New upstream release
* Thu Aug 18 2016 Zygmunt Krynicki <me@zygoon.pl> - 2.11-8
- Add %%dir entries for various snapd directories
- Tweak Source0 URL
* Tue Aug 16 2016 Zygmunt Krynicki <me@zygoon.pl> - 2.11-7
- Disable snapd re-exec feature by default
* Tue Aug 16 2016 Zygmunt Krynicki <me@zygoon.pl> - 2.11-6
- Don't auto-start snapd.socket and snapd.refresh.timer
* Tue Aug 16 2016 Zygmunt Krynicki <me@zygoon.pl> - 2.11-5
- Don't touch snapd state on removal
* Tue Aug 16 2016 Zygmunt Krynicki <me@zygoon.pl> - 2.11-4
- Use ExecStartPre to load squashfs.ko before snapd starts
- Use dedicated systemd units for Fedora
* Tue Aug 16 2016 Zygmunt Krynicki <me@zygoon.pl> - 2.11-3
- Remove systemd preset (will be requested separately according to distribution
  standards).
* Tue Aug 16 2016 Zygmunt Krynicki <me@zygoon.pl> - 2.11-2
- Use Requires: kmod(squashfs.ko) instead of Requires: kernel-modules
* Tue Aug 16 2016 Zygmunt Krynicki <me@zygoon.pl> - 2.11-1
- New upstream release
- Move private executables to /usr/libexec/snapd/
* Fri Jun 24 2016 Zygmunt Krynicki - 2.0.9-2
- Depend on kernel-modules to ensure that squashfs can be loaded. Load it afer
  installing the package. This hopefully fixes
  https://github.com/zyga/snapcore-fedora/issues/2
* Fri Jun 17 2016 Zygmunt Krynicki - 2.0.9
- New upstream release
  https://github.com/snapcore/snapd/releases/tag/2.0.9
* Tue Jun 14 2016 Zygmunt Krynicki - 2.0.8.1
- New upstream release
* Fri Jun 10 2016 Zygmunt Krynicki - 2.0.8
- First package for Fedora
