%global pypi_name fmclient

Summary: A python client library for Fault Management
Name: python-fmclient
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: Wind River <info@windriver.com>
URL: unknown
Source0: %{name}-%{version}.tar.gz

BuildRequires:  git
BuildRequires:  python3-pbr >= 5.1.2
BuildRequires:  python3-setuptools
BuildRequires:  python3-pip
BuildRequires:  python3-wheel

Requires:       python3-keystoneauth1 >= 3.17.1
Requires:       python3-pbr >= 5.1.2
Requires:       python3-six >= 1.11.0
Requires:       python3-oslo-i18n >= 3.24.0
Requires:       python3-oslo-utils >= 3.41.3
Requires:       python3-requests
Requires:       bash-completion

%description
A python client library for Fault Management

%define local_bindir /usr/bin/
%define local_etc_bash_completiond /etc/bash_completion.d/
%define pythonroot %python3_sitearch

%define debug_package %{nil}

%prep
%autosetup -n %{name}-%{version} -S git

# Remove bundled egg-info
rm -rf *.egg-info

%build
echo "Start build"

export PBR_VERSION=%{version}
%{__python3} setup.py build
%py3_build_wheel

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

install -d -m 755 %{buildroot}%{local_etc_bash_completiond}
install -p -D -m 664 tools/fm.bash_completion %{buildroot}%{local_etc_bash_completiond}/fm.bash_completion


%clean
echo "CLEAN CALLED"
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc LICENSE
%{local_bindir}/*
%{local_etc_bash_completiond}/*
%{pythonroot}/%{pypi_name}/*
%{pythonroot}/%{pypi_name}-%{version}*.egg-info


%package wheels
Summary: %{name} wheels

%description wheels
Contains python wheels for %{name}

%files wheels
/wheels/*
