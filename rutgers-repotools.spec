%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Summary:   Dependency check and publish scripts
Name:      rutgers-repotools
Version:   0.7.0
Release:   1%{?dist}
License:   GPLv2+
Group:     System Environment/Base
URL:       https://github.com/oss/rutgers-repotools
Source0:   %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildArch: noarch

Requires:  centos-release
Requires:  createrepo
Requires:  koji
Requires:  yum-utils
Requires:  MySQL-python
Requires: python
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

# In order webtools' runas to work
chmod -w $RPM_BUILD_ROOT/%{_bindir}/movepackage
chmod -w $RPM_BUILD_ROOT/%{_bindir}/pullpackage
chmod -w $RPM_BUILD_ROOT/%{_bindir}/pushpackage
chmod -w $RPM_BUILD_ROOT/%{_bindir}/populate-rpmfind-db
mkdir -p $RPM_BUILD_ROOT/var/lock/rutgers-repotools

%clean
rm -rf $RPM_BUILD_ROOT

%post
cat << EOF
You need to create the SSL certificates for the koji user "roji" who will do
the dependency checks for us, in case it was not already created. Refer to
"Adding a User to Koji" for detailed information about the certificate
generation process.

Also, a MySQL database needs to be created with write permisson, to be used by
rpm2python. See the Rutgers Repository Tools wiki page for detailed information
on making the database from scratch.

Symlinks to movepackage, pullpackage, pushpackage and populate-rpmfind-database
need to be created in webtools webbin directory to make runas work, for
managing packages through rpm2php. The symlinks must have the same owner with
the actual scripts.

The configuration file /etc/rutgers-repotools.cfg will need to be put on NFS
and symlinked to /etc, so that other machines can also use the same .cfg file

More information can be found in the README file and in the OSS wiki.
EOF

%files
%defattr(-,root,root,-)
%doc AUTHORS ChangeLog COPYING README
%{_bindir}/automagiccheck.py
%{_bindir}/checkrepo
%{_bindir}/movepackage
%{_bindir}/pullpackage
%{_bindir}/pushpackage
%{_bindir}/kojibackup.sh
%{_bindir}/rebuild-repos
%{_bindir}/populate-rpmfind-db
%{python_sitelib}/RUtools/
%{python_sitelib}/rutgers_repotools-%{version}-py2.6.egg-info
# TODO check this
%config %{_sysconfdir}/cron.daily/daily_checks
%config %{_sysconfdir}/cron.daily/depcheck_rutgers
%config %{_sysconfdir}/cron.daily/backup_rpmfind.sh
%config(noreplace) %{_sysconfdir}/depcheck.ignore
%config(noreplace) %{_sysconfdir}/rutgers-repotools.cfg

# The log directory and lock files should be owned by the group packagepushers
%attr(4775, root, packagepushers) %dir /var/log/%{name}/
%attr(4775, root, packagepushers) %dir /var/lock/rutgers-repotools


%changelog
* Thu Jan 16 2014 Kyle Suarez <kds124@nbcs.rutgers.edu> 0.7.0-1
- Complete rehaul for version 0.7.0

* Wed May 01 2013 Matt Robinson <mwr54@nbcs.rutgers.edu> 0.6.5-5
- Fixed an issue with lockfile checking and removed a redundant block of code

* Mon Apr 29 2013 Indraneel Purohit <ip132@nbcs.rutgers.edu> 0.6.5-4.ru6
- Moved automagiccheck.py and kojibackup.sh to /usr/bin/, added script to call both to cron.daily

* Thu Apr 25 2013 Jarek Sedlacek <jarek@nbcs.rutgers.edu> 0.6.5-3.ru6
- Added backup_rpmfind.sh to cron.daily

* Wed Apr 24 2013 Matt Robinson <mwr54@nbcs.rutgers.edu> 0.6.5-2.ru6
- fixed making lock file dir

* Wed Apr 17 2013 Matt Robinson <mwr54@nbcs.rutgers.edu> 0.6.5-1.ru6
- version bump

* Mon Mar 04 2013 Harry Stern <hcstern@nbcs.rutgers.edu> 0.6.4-1.ru6
- Rebuild for CentOS 6

* Tue Feb 05 2013 Jarek Sedlacej <jarek@nbcs.rutgers.edu> 0.6.4-1.ru
- bumped to version 0.6.4
* Wed Jan 30 2013 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.6.3-3.ru
- Updated depcheck cron scripts to check both stable and testing repos
* Tue Jan 22 2013 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.6.3-1.ru
- Included checkrepo6 binary in package (bump to 0.6.3)
* Wed Nov 07 2012 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.6.2-1.ru
- Updated to 0.6.2
* Wed Jun 13 2012 Kaitlin Poskaitis <katiepru@nbcs.rutgers.edu> - 0.6.1-1.ru
- Updated to 0.6.1

* Wed Feb 22 2012 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.6.0-1.ru
- update to 0.6.0

* Thu Jan 13 2011 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.5.1-1.ru
- Update to 0.5.1

* Fri Nov 05 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.5.0-1.ru
- Update to 0.5.0

* Tue Sep 07 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.4.6-1.ru
- Update to 0.4.6

* Thu Aug 12 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.4.5-1.ru
- Update to 0.4.5

* Wed Jul 28 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.4.1-3.ru
- echo also doesn't like parantheses

* Wed Jul 28 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.4.1-2.ru
- echo doesn't like a single quote '

* Tue Jul 27 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.4.1-1.ru
- Update to 0.4.1

* Thu Jul 22 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.4.0-1.ru
- Update to 0.4.0

* Fri Jul 02 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.3.0-1.ru
- Update to 0.3.0

* Thu Jun 03 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.2.2-1.ru
- Update to 0.2.2

* Wed May 12 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.2.1-1.ru
- Update to 0.2.1

* Wed Apr 14 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.2.0-1.ru
- Update to 0.2.0

* Fri Apr 02 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.1.9-1.ru
- Update to 0.1.9

* Fri Mar 19 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.1.2-1.ru
- Update to 0.1.2

* Fri Mar 19 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.1.1-1.ru
- Update to 0.1.1

* Fri Mar 19 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.1-1.ru
- Initial build.
