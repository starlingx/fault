Summary: CGTS Platform Fault Management Python API Package
Name: fm-api
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: Wind River <info@windriver.com>
URL: unknown
Source0: %{name}-%{version}.tar.gz

%define debug_package %{nil}

BuildRequires: python3-setuptools
BuildRequires: python3-pip
BuildRequires: python3-wheel

%description
CGTS platform Fault Management Client Library that provides APIs
for applications to raise/clear/update active alarms.

%package -n fm-api-doc
Summary: fm-api deploy doc
Group: doc
Provides: fm-api-doc

%description -n fm-api-doc
Contains contansts which is to be used by fm-doc package to validate
the Alarms & Logs Doc Yaml file

%define pythonroot %python3_sitearch
%define cgcs_doc_deploy_dir /opt/deploy/cgcs_doc

%prep
%setup

%build
%{__python3} setup.py build
%py3_build_wheel

%install
%{__python3} setup.py install --root=$RPM_BUILD_ROOT \
                             --install-lib=%{pythonroot} \
                             --prefix=/usr \
                             --install-data=/usr/share \
                             --single-version-externally-managed
mkdir -p $RPM_BUILD_ROOT/wheels
install -m 644 dist/*.whl $RPM_BUILD_ROOT/wheels/

CGCS_DOC_DEPLOY=$RPM_BUILD_ROOT/%{cgcs_doc_deploy_dir}
install -d $CGCS_DOC_DEPLOY
# install constants.py in CGCS_DOC_DEPLOY_DIR
# used by fm-doc package to validate the Alarms & Logs Doc Yaml file
install -m 644 fm_api/constants.py $CGCS_DOC_DEPLOY

%clean
rm -rf $RPM_BUILD_ROOT 

# Note: RPM package name is fm-api but import package name is fm_api so can't
# use '%{name}'.
%files
%license LICENSE
%defattr(-,root,root,-)
%dir %{pythonroot}/fm_api
%{pythonroot}/fm_api/*
%dir %{pythonroot}/fm_api-%{version}.0-py3.6.egg-info
%{pythonroot}/fm_api-%{version}.0-py3.6.egg-info/*

%files -n fm-api-doc
%defattr(-,root,root,-)
%{cgcs_doc_deploy_dir}/*

%package wheels
Summary: %{name} wheels

%description wheels
Contains python wheels for %{name}

%files wheels
/wheels/*
