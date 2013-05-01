%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Summary:   Dependency check and publish scripts
Name:      rutgers-repotools
Version:   0.6.5
Release:   5.ru6
License:   GPLv2+
Group:     System Environment/Base
URL:       http://cvs.rutgers.edu/cgi-bin/viewvc.cgi/trunk/orcan/rutgers-repotools/
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
This package contains the tools we use to check the dependencies of
new packages. This also installs a daily cron job which checks
the dependency situation in the rutgers tree and sends an email
if there is anything broken.

Moreover, it includes the scripts to recreate the repositories from
scratch and to populate the rpmfind database for use of rpm2php.

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
chmod -w $RPM_BUILD_ROOT/%{_bindir}/movepackage6
chmod -w $RPM_BUILD_ROOT/%{_bindir}/pullpackage6
chmod -w $RPM_BUILD_ROOT/%{_bindir}/pushpackage6
chmod -w $RPM_BUILD_ROOT/%{_bindir}/populate-rpmfind-db6
mkdir -p $RPM_BUILD_ROOT/var/lock/rutgers-repotools



%clean
rm -rf $RPM_BUILD_ROOT

%post
echo You need to create the SSL certificates for the koji user \"roji\" who will do
echo the dependency checks for us, in case it was not already created. The certificates
echo cannot be included in the RPM file for security reasons:
echo
echo    user=roji
echo    koji add-user ${user}
echo    koji grant-permission admin ${user}
echo    sudo -s
echo    cd /etc/pki/koji
echo    openssl genrsa -out certs/${user}.key 2048
echo    openssl req -config ssl.cnf -new -nodes -out certs/${user}.csr -key certs/${user}.key
echo    openssl ca -config ssl.cnf -keyfile private/koji_ca_cert.key -cert koji_ca_cert.crt -out certs/${user}.crt -outdir certs -infiles certs/${user}.csr
echo    cat certs/${user}.crt certs/${user}.key > ${user}.pem
echo
echo Also, a MySQL database needs to be created with write permisson, to be used by rpm2php:
echo
echo    mysql -u root -p
echo
echo Inside mysql prompt we do:
echo
echo    create database rpmfind;
echo    grant usage on *.* to roji@localhost identified by 'PASSWORD';
echo    grant all privileges on rpmfind.* to roji@localhost;
echo    exit;
echo
echo Symlinks to movepackage, pullpackage, pushpackage and populate-rpmfind-database
echo need to be created in webtools webbin directory to make runas work, for
echo managing packages through rpm2php. The symlinks must have the same owner with
echo the actual scripts.
echo
echo The configuration file /etc/rutgers-repotools.cfg will need to be put on NFS
echo and symlinked to /etc, so that other machines can also use the same .cfg file
echo
echo More information can be found in the README file.

%files
%defattr(-,root,root,-)
%doc AUTHORS ChangeLog COPYING README
%{_bindir}/automagiccheck.py
%{_bindir}/checkrepo
%{_bindir}/checkrepo6
%{_bindir}/movepackage
%{_bindir}/pullpackage
%{_bindir}/pushpackage
%{_bindir}/kojibackup.sh
%{_bindir}/rebuild-repos
%{_bindir}/populate-rpmfind-db
%{_bindir}/movepackage6
%{_bindir}/pullpackage6
%{_bindir}/pushpackage6
%{_bindir}/rebuild-repos6
%{_bindir}/populate-rpmfind-db6
%{python_sitelib}/RUtools/
%{python_sitelib}/rutgers_repotools-%{version}-py2.6.egg-info
%config %{_sysconfdir}/cron.daily/daily_checks
%config %{_sysconfdir}/cron.daily/depcheck_rutgers
%config %{_sysconfdir}/cron.daily/depcheck_rutgers6
%config %{_sysconfdir}/cron.daily/backup_rpmfind.sh
%config(noreplace) %{_sysconfdir}/depcheck.ignore
%config(noreplace) %{_sysconfdir}/depcheck6.ignore
%config(noreplace) %{_sysconfdir}/rutgers-repotools.cfg
%config(noreplace) %{_sysconfdir}/rutgers-repotools-centos6.cfg

# The log directory should be setgid with packagepushers, so the logs
# are readable/writeable by anyone in packagepushers
%attr(4775, root, packagepushers) %dir /var/log/%{name}/

# lock directory should be owned by packagepushers, and setgid packagepushers
%attr(4775, root, packagepushers) %dir /var/lock/rutgers-repotools


%changelog
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
