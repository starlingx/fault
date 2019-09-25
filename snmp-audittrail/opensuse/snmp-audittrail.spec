Name: snmp-audittrail
Version: 1.0.0
Release: %{tis_patch_ver}%{?_tis_dist}
Summary: StarlingX SNMP Audit Trail
License: Apache-2.0
Group: Development/Tools/Other
URL: https://opendev.org/starlingx/fault
Source0: %{name}-%{version}.tar.gz
BuildRequires: fm-common-devel
BuildRequires: libuuid-devel
BuildRequires: net-snmp-devel
BuildRequires: uuid-devel
Requires: net-snmp
Requires: uuid
%if 0%{?suse_version}
BuildRequires: gcc-c++
%endif

%description
StarlingX SNMP Audit Trail provides audit trail support for incoming
SNMP requests.

%package -n snmp-audittrail-devel
Summary: StarlingX SNMP Audit Trail Package - Development files
Group: Development/Tools/Other
Requires: snmp-audittrail = %{version}-%{release}

%description -n snmp-audittrail-devel
StarlingX SNMP Audit Trail provides audit trail support for incoming SNMP requests.
This package contains symbolic links, header files, and related items necessary
for software development.

%prep
%autosetup -n %{name}-%{version}/sources

%build
VER=%{version}
MAJOR=`echo $VER | awk -F . '{print $1}'`
MINOR=`echo $VER | awk -F . '{print $2}'`
make MAJOR=$MAJOR MINOR=$MINOR PATCH=%{tis_patch_ver} %{?_smp_mflags}

%install
VER=%{version}
MAJOR=`echo $VER | awk -F . '{print $1}'`
MINOR=`echo $VER | awk -F . '{print $2}'`
make install DESTDIR=%{buildroot} LIB_DIR=%{_libdir} MAJOR=$MAJOR MINOR=$MINOR PATCH=%{tis_patch_ver}

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%defattr(-,root,root,-)
%license LICENSE
%{_libdir}/*.so.*

%files -n snmp-audittrail-devel
%defattr(-,root,root,-)
%{_libdir}/*.so

%changelog
