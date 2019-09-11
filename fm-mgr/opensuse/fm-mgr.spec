%define local_dir %{_prefix}/local
%define local_bindir %{local_dir}/bin
Name: fm-mgr
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
Summary: StarlingX Platform Fault Manager Package
License: Apache-2.0
Group: Development/Tools/Other
URL: https://opendev.org/starlingx/fault
Source0: %{name}-%{version}.tar.gz
BuildRequires: fm-common-devel
BuildRequires: libuuid-devel
BuildRequires: systemd-devel
Requires: logrotate
%if 0%{?suse_version}
BuildRequires: gcc-c++
%endif

%description
StarlingX platform Fault Manager that serves the client
application fault management requests and raise/clear/update
alarms in the active alarm database.

%prep
%autosetup

%build
VER=%{version}
MAJOR=`echo $VER | awk -F . '{print $1}'`
MINOR=`echo $VER | awk -F . '{print $2}'`
make  MAJOR=$MAJOR MINOR=$MINOR %{?_smp_mflags}

%install
VER=%{version}
MAJOR=`echo $VER | awk -F . '{print $1}'`
MINOR=`echo $VER | awk -F . '{print $2}'`
make DESTDIR=%{buildroot} \
     BINDIR=%{local_bindir} \
     SYSCONFDIR=%{_sysconfdir} \
     UNITDIR=%{_unitdir} \
     MAJOR=$MAJOR MINOR=$MINOR \
     install

%files
%defattr(-,root,root,-)
%license LICENSE
%{local_bindir}/fmManager
%_sysconfdir/init.d/fminit
%{_unitdir}/fminit.service
%config(noreplace) %{_sysconfdir}/logrotate.d/fm.logrotate

%pre
%service_add_pre fminit.service fminit.target

%post
%service_add_post fminit.service fminit.target

%preun
%service_del_preun fminit.service fminit.target

%postun
%service_del_postun fminit.service fminit.target

%changelog
