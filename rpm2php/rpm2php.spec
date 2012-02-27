Name:           rpm2php
Version:        0.1.6
Release:        1%{?dist}
Summary:        Browse and manage Rutgers RPM packages
Group:          Applications/Internet
License:        BSD and GPLv2+
URL:            http://cvs.rutgers.edu/cgi-bin/viewvc.cgi/trunk/orcan/rpm2php/
Source0:        %{name}-%{version}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
Requires:       php
Requires:       php-mysql
# I think this is needed only by php < 5.3 - Orcan:
Requires:       php-pecl-Fileinfo
Requires:       php-tidy
Requires:       rutgers-repotools >= 0.5
Requires:       webtools

%description
This package contains the PHP software that is used to browse and manage the
RPM packages created by Rutgers OSS.

%prep
%setup -q

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_datadir}/%{name}-%{version}
cp -a %{name} %{buildroot}%{_datadir}/%{name}-%{version}

%clean
rm -rf %{buildroot}

%post
echo See the %{_docdir}/%{name}-%{version}/README file for information how to set up rpm2php.

%files
%defattr(-,root,root,-)
%doc AUTHORS COPYING* LICENSE README ChangeLog htaccess-example
%{_datadir}/%{name}-%{version}

%changelog
* Thu Jan 05 2012 Jarek Sedlacek <jarek@nbcs.rutgers.edu> - 0.1.6-1
- bumped to 0.1.6

* Fri Jan 14 2011 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.1.5-1
- Update to 0.1.5

* Thu Nov 11 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.1.4-1
- Update to 0.1.4

* Tue Sep 07 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.1.3-1
- Update to 0.1.3

* Tue Jul 27 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.1.2-1
- Update to 0.1.2

* Thu Jul 22 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.1.1-1
- Update to 0.1.1

* Thu Jul 22 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.1-2
- Package should require webtools

* Thu Jul 22 2010 Orcan Ogetbil <orcan@nbcs.rutgers.edu> - 0.1-1
- Initial release
