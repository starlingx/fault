#
# spec file for package python
#
#


%global pypi_name fmclient
Name:           python-%{pypi_name}
Version:        1.0
Release:        %{tis_patch_ver}%{?_tis_dist}
Summary:        A python client library for Fault Management
License:        Apache-2.0
Group:          Development/Tools/Other
URL:            https://opendev.org/starlingx/fault
Source0:        %{name}-%{version}.tar.gz
BuildRequires:  git
BuildRequires:  python-setuptools
BuildRequires:  python2-pbr
BuildRequires:  python3-pbr
Requires:       bash-completion
Requires:       python-keystoneauth1 >= 3.1.0
Requires:       python-oslo.i18n >= 2.1.0
Requires:       python-oslo.utils >= 3.20.0
Requires:       python-pbr >= 2.0.0
Requires:       python-requests
Requires:       python-six >= 1.9.0

%description
A python client library for StarlingX Fault Management service

%define local_etc_bash_completiond %{_sysconfdir}/bash_completion.d/
%define pythonroot %{_libdir}/python2.7/site-packages
%define debug_package %{nil}

%prep
%autosetup

# Remove bundled egg-info
rm -rf *.egg-info

%build
export PBR_VERSION=%{version}
python setup.py build

%install
export PBR_VERSION=%{version}
python setup.py install --root=%{buildroot} \
                             --install-lib=%{pythonroot} \
                             --prefix=%{_prefix} \
                             --install-data=%{_datadir} \
                             --single-version-externally-managed

install -d -m 755 %{buildroot}%{local_etc_bash_completiond}
install -p -D -m 664 tools/fm.bash_completion %{buildroot}%{local_etc_bash_completiond}/fm.bash_completion

%files
%license LICENSE
%{_bindir}/*
%config %{local_etc_bash_completiond}/*
%{pythonroot}/%{pypi_name}
%{pythonroot}/%{pypi_name}-%{version}*.egg-info

%changelog
