%define debug_package %{nil}
Name: fm-api
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
Summary: StarlingX Platform Fault Management Python API Package
License: Apache-2.0
Group: Development/Tools/Other
URL: https://opendev.org/starlingx/fault
Source0: %{name}-%{version}.tar.xz
BuildRequires: python-setuptools
BuildRequires: python2-pip

%description
StarlingX platform Fault Management Client Library that provides APIs
for applications to raise/clear/update active alarms.

%package -n fm-api-doc
Summary: StarlingX fm-api deploy doc
Group: Documentation/Other

%description -n fm-api-doc
Contains constants which is to be used by fm-doc package to validate
the Alarms & Logs Doc Yaml file

%define pythonroot %{_libdir}/python2.7/site-packages
%define doc_deploy_dir /opt/deploy/cgcs_doc

%prep
%autosetup

%build
python setup.py build

%install
python setup.py install --root=%{buildroot} \
                             --install-lib=%{pythonroot} \
                             --prefix=%{_prefix} \
                             --install-data=%{_datadir} \
                             --single-version-externally-managed

DOC_DEPLOY=%{buildroot}/%{doc_deploy_dir}
install -d $DOC_DEPLOY
# install constants.py in DOC_DEPLOY_DIR
# used by fm-doc package to validate the Alarms & Logs Doc Yaml file
install -m 644 fm_api/constants.py $DOC_DEPLOY

# Note: RPM package name is fm-api but import package name is fm_api so can't
# use '%%{name}'.
%files
%defattr(-,root,root,-)
%license LICENSE
%dir %{pythonroot}/fm_api
%{pythonroot}/fm_api/*
%dir %{pythonroot}/fm_api-%{version}.0-py2.7.egg-info
%{pythonroot}/fm_api-%{version}.0-py2.7.egg-info/*

%files -n fm-api-doc
%defattr(-,root,root,-)
%dir /opt/deploy
%dir %{doc_deploy_dir}
%{doc_deploy_dir}/*

%changelog
