Summary: Fault Management Openstack REST API
Name: fm-rest-api
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: Wind River <info@windriver.com>
URL: unknown
Source0: %{name}-%{version}.tar.gz

BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: python3-pip
BuildRequires: python3-wheel
BuildRequires: python3-oslo-config
BuildRequires: python3-oslo-db
BuildRequires: python3-oslo-log
BuildRequires: python3-oslo-messaging
BuildRequires: python3-oslo-middleware

Requires: python3-eventlet
Requires: python3-webob
Requires: python3-paste
Requires: setup

BuildRequires: systemd

%description
Fault Management Openstack REST API Service

%define local_bindir /usr/bin/
%define local_initddir /etc/rc.d/init.d
%define pythonroot %{python3_sitearch}
%define local_etc_pmond /etc/pmon.d/
%define debug_package %{nil}

%prep
%autosetup -n %{name}-%{version}

# Remove bundled egg-info
rm -rf *.egg-info

%build
echo "Start build"

export PBR_VERSION=%{version}
%{__python3} setup.py build
%py3_build_wheel
PYTHONPATH=. oslo-config-generator --config-file=fm/config-generator.conf

%install
echo "Start install"
export PBR_VERSION=%{version}
%{__python3} setup.py install --root=%{buildroot} \
                             --install-lib=%{pythonroot} \
                             --prefix=/usr \
                             --install-data=/usr/share \
                             --single-version-externally-managed
mkdir -p $RPM_BUILD_ROOT/wheels
install -m 644 dist/*.whl $RPM_BUILD_ROOT/wheels/

install -p -D -m 644 scripts/fm-api.service %{buildroot}%{_unitdir}/fm-api.service
install -d -m 755 %{buildroot}%{local_initddir}
install -p -D -m 755 scripts/fm-api %{buildroot}%{local_initddir}/fm-api

install -d -m 755 %{buildroot}%{local_etc_pmond}
install -p -D -m 644 fm-api-pmond.conf %{buildroot}%{local_etc_pmond}/fm-api.conf

# install default config files
cd %{_builddir}/%{name}-%{version} && oslo-config-generator --config-file fm/config-generator.conf --output-file %{_builddir}/%{name}-%{version}/fm.conf.sample
install -p -D -m 600 %{_builddir}/%{name}-%{version}/fm.conf.sample %{buildroot}%{_sysconfdir}/fm/fm.conf

%clean
echo "CLEAN CALLED"
rm -rf $RPM_BUILD_ROOT

%post
/bin/systemctl enable fm-api.service >/dev/null 2>&1

%files
%defattr(-,root,root,-)
%doc LICENSE

%{local_bindir}/*

%{local_initddir}/*

%{pythonroot}/fm/*

%{pythonroot}/fm-%{version}*.egg-info

%config(noreplace) %attr(600,fm,fm)%{_sysconfdir}/fm/fm.conf

# systemctl service files
%{_unitdir}/fm-api.service

# pmond config file
%{local_etc_pmond}/fm-api.conf

%package wheels
Summary: %{name} wheels

%description wheels
Contains python wheels for %{name}

%files wheels
/wheels/*
