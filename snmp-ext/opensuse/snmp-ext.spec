%define mib_ver 2.0
Name: snmp-ext
Version: 1.0.0
Release: %{tis_patch_ver}%{?_tis_dist}
Summary: StarlingX Platform SNMP extension Package
License: Apache-2.0
Group: Development/Tools/Other
URL: https://opendev.org/starlingx/fault
Source0: %{name}-%{version}.tar.gz
BuildRequires: fm-common-devel
BuildRequires: libuuid-devel
BuildRequires: net-snmp-devel
Requires:      fm-common
Requires:      net-snmp
%if 0%{?suse_version}
BuildRequires: gcc-c++
%endif

%description
StarlingX Cloud platform SNMP extension provides Wind River enterprise MIBs support
and it serves as SNMP based alarm surveillance module for Network Manager
System.

%package -n snmp-ext-devel
Summary: StarlingX Cloud Platform SNMP extension Package - Development files
Group: Development/Tools/Other
Requires: snmp-ext = %{version}-%{release}

%description -n snmp-ext-devel
StarlingX Cloud platform SNMP extension provides Wind River enterprise MIBs support
and it serves as SNMP based alarm surveillance module for Network Manager
System.  This package contains symbolic links, header files, and related
items necessary for software development.

%prep
%autosetup -n %{name}-%{version}/sources

%build
MAJOR=`echo %{version} | awk -F . '{print $1}'`
MINOR=`echo %{version} | awk -F . '{print $2}'`
make MAJOR=$MAJOR MINOR=$MINOR PATCH=%{tis_patch_ver} %{?_smp_mflags}

%install
MAJOR=`echo %{version} | awk -F . '{print $1}'`
MINOR=`echo %{version} | awk -F . '{print $2}'`
make DEST_DIR=%{buildroot} \
     LIB_DIR=%{_libdir} \
     MAJOR=$MAJOR \
     MINOR=$MINOR \
     MIBVER=%{mib_ver} \
     PATCH=%{tis_patch_ver} install

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%defattr(-,root,root,-)
%license LICENSE
%{_libdir}/*.so.*
%{_datadir}/snmp/mibs/*

%files -n snmp-ext-devel
%defattr(-,root,root,-)
%{_libdir}/*.so

%changelog
