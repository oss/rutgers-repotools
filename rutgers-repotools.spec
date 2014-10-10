%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Summary:   Dependency checking and publish scripts
Name:      rutgers-repotools
Version:   0.7.12
Release:   1%{?dist}
License:   GPLv2+
Group:     System Environment/Base
URL:       https://github.com/oss/rutgers-repotools
Source0:   %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildArch: noarch

Requires:  centos-release
Requires:  koji
Requires:  MySQL-python
Requires:  python
Requires:  repoutils
Requires:  yum-utils
BuildRequires: python

%description
This package contains Rutgers tools needed to check the dependencies of new
packages. This also installs a daily cron job which checks for broken
dependencies in the Rutgers tree and sends email to report problems.

This also includes scripts for recreating repositories from scratch and for
populating the MySQL database used by rpm2python.

%prep
%setup -q

%build
python setup.py build

%install
rm -rf $RPM_BUILD_ROOT
python setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/var/lock/rutgers-repotools

%clean
rm -rf $RPM_BUILD_ROOT

%post
cat << EOF
You need to create the SSL certificates for the koji user "roji" who will do
the dependency checks for us, in case it was not already created. Refer to
"Adding a User to Koji" for detailed information about the certificate
generation process.

Furthermore, you need to set up the MySQL database to be used by rpm2python if
you have not done so already. See the Rutgers Repository Tools wiki page for
detailed information on making the database from scratch.

The configuration file /etc/rutgers-repotools.cfg will need to be put on NFS
and symlinked to /etc, so that other machines can also use the same .cfg file

More information can be found in the README file and in the OSS wiki.
EOF

%files
%defattr(-,root,root,-)
%doc CHANGELOG LICENSE README.md
%{_bindir}/depcheck
%{_bindir}/koji-backup
%{_bindir}/movepackage
%{_bindir}/populate-rpmfind-db
%{_bindir}/pullpackage
%{_bindir}/pushpackage
%{_bindir}/rebuild-repos
%{_bindir}/repocheck
%{_bindir}/rpmdb-backup
%{python_sitelib}/RUtools/
%{python_sitelib}/rutgers_repotools-%{version}-py2.6.egg-info
%config %{_sysconfdir}/cron.daily/daily_checks
%config(noreplace) %{_sysconfdir}/depcheck.ignore.sample
%config(noreplace) %{_sysconfdir}/rutgers-repotools.cfg.sample

# The log directory and lock files should be owned by the group packagepushers
%attr(4775, root, packagepushers) %dir /var/log/%{name}/
%attr(4775, root, packagepushers) %dir /var/lock/rutgers-repotools


%changelog
