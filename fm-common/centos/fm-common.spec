%define local_dir /usr/local
%define local_bindir %{local_dir}/bin
%define cgcs_doc_deploy_dir /opt/deploy/cgcs_doc
%define pythonroot %python3_sitearch

Summary: CGTS Platform Fault Management Common Package
Name: fm-common
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: Wind River <info@windriver.com>
URL: unknown
Source0: %{name}-%{version}.tar.gz
BuildRequires: util-linux
BuildRequires: postgresql-devel
BuildRequires: libuuid-devel
BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: python3-pip
BuildRequires: python3-wheel

%package -n fm-common-dev
Summary: CGTS Platform Fault Management Common Package - Development files
Group: devel
Requires: fm-common = %{version}-%{release}

%description
StarlingX platform Fault Management Client Library that provides APIs for
applications to raise/clear/update active alarms.

%description -n fm-common-dev
StarlingX platform Fault Management Client Library that provides APIs for
applications to raise/clear/update active alarms.  This package contains
symbolic links, header files, and related items necessary for software
development.

%package -n fm-common-doc
Summary: fm-common deploy doc
Group: doc

%description -n fm-common-doc
Contains fmAlarm.h which is to be used by fm-doc package to validate
the Alarms & Logs Doc Yaml file

%prep
%setup

%build
VER=%{version}
MAJOR=`echo $VER | awk -F . '{print $1}'`
MINOR=`echo $VER | awk -F . '{print $2}'`
make  MAJOR=$MAJOR MINOR=$MINOR %{?_smp_mflags}
%{__python3} setup.py build
%py3_build_wheel

%install
rm -rf %{buildroot}
VER=%{version}
MAJOR=`echo $VER | awk -F . '{print $1}'`
MINOR=`echo $VER | awk -F . '{print $2}'`
make DESTDIR=%{buildroot} \
     BINDIR=%{local_bindir} \
     LIBDIR=%{_libdir} \
     INCDIR=%{_includedir} \
     CGCS_DOC_DEPLOY=%{cgcs_doc_deploy_dir} \
     MAJOR=$MAJOR MINOR=$MINOR install

%{__python3} setup.py install --root=%{buildroot} \
                             --install-lib=%{pythonroot} \
                             --prefix=/usr \
                             --install-data=/usr/share
mkdir -p %{buildroot}/wheels
install -m 644 dist/*.whl %{buildroot}/wheels/

%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%doc LICENSE
%{local_bindir}/*
%{_libdir}/*.so.*

# with python3 PEP 3149, ABI version is tagged in so name.
# so the file name will be like: fm_core.cpython-36m-x86_64-linux-gnu.so
%{pythonroot}/fm_core.cpython-3*.so
%{pythonroot}/fm_core-*.egg-info

%files -n fm-common-dev
%defattr(-,root,root,-)
%{_includedir}/*
%{_libdir}/*.so

%files -n fm-common-doc
%defattr(-,root,root,-)
%{cgcs_doc_deploy_dir}/*

%package wheels
Summary: %{name} wheels

%description wheels
Contains python wheels for %{name}

%files wheels
/wheels/*
