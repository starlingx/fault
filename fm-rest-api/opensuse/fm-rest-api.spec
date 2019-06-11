Name: fm-rest-api
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
Summary: Fault Management Openstack REST API
License: Apache-2.0
Group: Development/Tools/Other
URL: https://opendev.org/starlingx/fault
Source0: %{name}-%{version}.tar.xz
BuildRequires: python2-oslo.config
BuildRequires: python-oslo.db
BuildRequires: python2-oslo.log
BuildRequires: python-oslo.messaging
BuildRequires: python-oslo.middleware
BuildRequires: python-setuptools
BuildRequires: python2-pip
BuildRequires: systemd
BuildRequires: systemd-rpm-macros
BuildRequires: insserv-compat
Requires: python-eventlet
Requires: python-paste
Requires: python-webob
Requires: systemd

%description
Fault Management Openstack REST API Service

%define local_bindir %{_bindir}
%define local_initddir %{_sysconfdir}/rc.d/init.d
%define pythonroot %{_libdir}/python2.7/site-packages
%define local_etc_pmond %{_sysconfdir}/pmon.d/
%define debug_package %{nil}

%prep
%autosetup

# Remove bundled egg-info
rm -rf *.egg-info

%build
echo "Start build"

export PBR_VERSION=%{version}
python setup.py build
PYTHONPATH=. oslo-config-generator --config-file=fm/config-generator.conf

%install
echo "Start install"
export PBR_VERSION=%{version}
python setup.py install --root=%{buildroot} \
                             --install-lib=%{pythonroot} \
                             --prefix=%{_prefix} \
                             --install-data=%{_datadir} \
                             --single-version-externally-managed

install -p -D -m 644 scripts/fm-api.service %{buildroot}%{_unitdir}/fm-api.service
install -D -d -m 755 %{buildroot}%{_sbindir}
ln -s %{_sbindir}/service %{buildroot}%{_sbindir}/rcfm-api

install -d -m 755 %{buildroot}%{local_initddir}
install -p -D -m 755 scripts/fm-api %{buildroot}%{local_initddir}/fm-rest-apid

install -d -m 755 %{buildroot}%{local_etc_pmond}
install -p -D -m 644 fm-api-pmond.conf %{buildroot}%{local_etc_pmond}/fm-api.conf

# Install sql migration stuff that wasn't installed by setup.py
install -m 640 fm/db/sqlalchemy/migrate_repo/migrate.cfg %{buildroot}%{pythonroot}/fm/db/sqlalchemy/migrate_repo/migrate.cfg

# install default config files
oslo-config-generator --config-file fm/config-generator.conf --output-file %{_builddir}/fm.conf.sample
install -p -D -m 644 %{_builddir}/fm.conf.sample %{buildroot}%{_sysconfdir}/fm/fm.conf

%files
%defattr(-,root,root,-)
%license LICENSE

%{local_bindir}/*

%dir %{_sysconfdir}/rc.d
%dir %{local_initddir}
%{local_initddir}/*

%dir %{pythonroot}/fm
%{pythonroot}/fm/*

%{pythonroot}/fm-%{version}*.egg-info

%dir %{_sysconfdir}/fm
%config(noreplace) %{_sysconfdir}/fm/fm.conf

# systemctl service files
%{_unitdir}/fm-api.service
%{_sbindir}/rcfm-api

# pmond config file
%dir %{local_etc_pmond}
%config %{local_etc_pmond}/fm-api.conf

%pre
%service_add_pre fm-api.service fm-api.target

%post
/bin/systemctl enable fm-api.service >/dev/null 2>&1
%service_add_post fm-api.service fm-api.target

%preun
%service_del_preun fm-api.service fm-api.target

%postun
%service_del_postun fm-api.service fm-api.target

%changelog
