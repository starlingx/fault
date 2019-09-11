%define local_dir %{_prefix}/local
%define local_bindir %{local_dir}/bin
%define cgcs_doc_deploy_dir /opt/deploy/cgcs_doc
%define pythonroot %{_libdir}/python2.7/site-packages
Name: fm-common
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
Summary: StarlingX Platform Fault Management Common Package
License: Apache-2.0
Group: Development/Tools/Other
URL: https://opendev.org/starlingx/fault
Source0: %{name}-%{version}.tar.gz
BuildRequires: libuuid-devel
BuildRequires: postgresql-devel
BuildRequires: python-devel
BuildRequires: python-setuptools
BuildRequires: util-linux
%if 0%{?suse_version}
BuildRequires: gcc-c++
%endif

%package -n fm-common-devel
Summary: StarlingX Platform Fault Management Common Package - Development files
Requires: fm-common = %{version}-%{release}
Provides: fm-common-dev = %{version}
Obsoletes: fm-common-dev < %{version}

%description
StarlingX Cloud platform Fault Management Client Library that provides APIs for
applications to raise/clear/update active alarms.

%description -n fm-common-devel
StarlingX Cloud platform Fault Management Client Library that provides APIs for
applications to raise/clear/update active alarms.  This package contains
symbolic links, header files, and related items necessary for software
development.

%package -n fm-common-doc
Summary: StarlingX Fault Management deploy doc for fm-common

%description -n fm-common-doc
Contains fmAlarm.h which is to be used by fm-doc package to validate
the Alarms & Logs Doc Yaml file

%prep
%autosetup

%build
VER=%{version}
MAJOR=`echo $VER | awk -F . '{print $1}'`
MINOR=`echo $VER | awk -F . '{print $2}'`
make  MAJOR=$MAJOR MINOR=$MINOR %{?_smp_mflags}
python setup.py build
#%%xpy2_build_wheel

%install
VER=%{version}
MAJOR=`echo $VER | awk -F . '{print $1}'`
MINOR=`echo $VER | awk -F . '{print $2}'`
make DESTDIR=%{buildroot} \
     BINDIR=%{local_bindir} \
     LIBDIR=%{_libdir} \
     INCDIR=%{_includedir} \
     CGCS_DOC_DEPLOY=%{cgcs_doc_deploy_dir} \
     MAJOR=$MAJOR MINOR=$MINOR install
python setup.py install --root=%{buildroot} \
                             --install-lib=%{pythonroot} \
                             --prefix=%{_prefix} \
                             --install-data=%{_datadir}

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%license LICENSE
%{local_bindir}/*
%{_libdir}/*.so.*

%{pythonroot}/fm_core.so
%{pythonroot}/fm_core-*.egg-info

%files -n fm-common-devel
%{_includedir}/*
%{_libdir}/*.so

%files -n fm-common-doc
%dir /opt/deploy
%{cgcs_doc_deploy_dir}

%changelog
