%global ioctl_opt_version 1.3.1

Name:           sc-controller
Version:        1.0.5
Release:        2%{?dist}
Summary:        User-mode driver and configuration GUI for game controllers

# SC Controller is GPL-2.0-only. The bundled ioctl-opt module is
# LGPL-2.0-or-later.
License:        GPL-2.0-only AND LGPL-2.0-or-later
URL:            https://github.com/C0rn3j/sc-controller
Source0:        %{url}/archive/refs/tags/v%{version}/%{name}-%{version}.tar.gz
# Fedora does not currently package ioctl-opt. Upstream publishes 1.3.1 only
# as a pure-Python wheel.
Source1:        https://files.pythonhosted.org/packages/7f/ba/2a8796dfa24e8ac9fbbffe4e70c9cdab6fa088122b258ab53354ba8af490/ioctl_opt-%{ioctl_opt_version}-py3-none-any.whl

BuildRequires:  desktop-file-utils
BuildRequires:  gcc
BuildRequires:  gettext
BuildRequires:  libappstream-glib
BuildRequires:  python3-devel >= 3.12
BuildRequires:  python3-installer
BuildRequires:  python3-pip
BuildRequires:  python3-setuptools
BuildRequires:  python3-setuptools_scm
BuildRequires:  python3-wheel
BuildRequires:  shared-mime-info
BuildRequires:  systemd-rpm-macros
BuildRequires:  libxml2

Requires:       gtk4 >= 4.14
Requires:       gtk4-layer-shell
Requires:       hicolor-icon-theme
Requires:       librsvg2
Requires:       python3-cairo
Requires:       python3-evdev
Requires:       python3-gobject
Requires:       python3-libusb1
Requires:       python3-pylibacl
Requires:       python3-vdf

Provides:       bundled(python3dist(hidraw-pure))
Provides:       bundled(python3dist(ioctl-opt)) = %{ioctl_opt_version}
Provides:       python3dist(ioctl-opt) = %{ioctl_opt_version}

%description
SC Controller is a user-mode driver, mapper, and GTK 4 configuration
application for game controllers. It supports the Steam Controller, Steam
Deck, DualShock 4, DualSense, and controllers exposed through evdev, and can
emulate an Xbox 360 controller, mouse, trackball, or keyboard.


%prep
%autosetup -p1


%build
# GitHub source archives do not contain the Git metadata setuptools-scm uses
# to derive the version.
export SETUPTOOLS_SCM_PRETEND_VERSION_FOR_SCCONTROLLER=%{version}
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files -l scc
%{python3} -m installer --destdir=%{buildroot} %{SOURCE1}


%check
desktop-file-validate \
    %{buildroot}%{_datadir}/applications/io.github.c0rn3j.sc-controller.desktop
appstream-util validate-relax --nonet \
    %{buildroot}%{_datadir}/metainfo/io.github.c0rn3j.sc-controller.metainfo.xml
xmllint --noout \
    %{buildroot}%{_datadir}/mime/packages/io.github.c0rn3j.sc-controller.mimetypes.xml
%pyproject_check_import


%files -f %{pyproject_files}
%license LICENSE
%license %{python3_sitelib}/ioctl_opt-%{ioctl_opt_version}.dist-info/licenses/COPYING
%license %{python3_sitelib}/ioctl_opt-%{ioctl_opt_version}.dist-info/licenses/COPYING.LESSER
%doc README.md ADDITIONAL-LICENSES
%{_bindir}/sc-controller
%{_bindir}/scc
%{_bindir}/scc-daemon
%{_bindir}/scc-osd-*
%{python3_sitearch}/libcemuhook*.so
%{python3_sitearch}/libhiddrv*.so
%{python3_sitearch}/libremotepad*.so
%{python3_sitearch}/libsc_by_bt*.so
%{python3_sitearch}/libuinput*.so
%{python3_sitelib}/ioctl_opt/
%{python3_sitelib}/ioctl_opt-%{ioctl_opt_version}.dist-info/METADATA
%{python3_sitelib}/ioctl_opt-%{ioctl_opt_version}.dist-info/RECORD
%{python3_sitelib}/ioctl_opt-%{ioctl_opt_version}.dist-info/WHEEL
%{python3_sitelib}/ioctl_opt-%{ioctl_opt_version}.dist-info/top_level.txt
%{_datadir}/applications/io.github.c0rn3j.sc-controller.desktop
%{_datadir}/icons/hicolor/*/status/*.png
%{_datadir}/icons/hicolor/scalable/apps/io.github.c0rn3j.sc-controller.svg
%{_datadir}/locale/*/LC_MESSAGES/sc-controller.mo
%{_datadir}/metainfo/io.github.c0rn3j.sc-controller.metainfo.xml
%{_datadir}/mime/packages/io.github.c0rn3j.sc-controller.mimetypes.xml
%{_datadir}/scc/
%{_udevrulesdir}/69-sc-controller.rules


%changelog
* Mon Oct 05 2026 Fedora COPR Maintainer <noreply@example.com> - 1.0.5-2
- Add the missing python3-pip build dependency

* Sun Oct 04 2026 Fedora COPR Maintainer <noreply@example.com> - 1.0.5-1
- Fix many issues with cross-platform support - Windows support is now possible
  as a result
- SC Controller can now be translated into your favorite language! See the
  README for more info.
- Fix X/Y being flipped when emulating an X360 controller
- Fix Custom Editor not opening (regression after GTK 4 migration)
- Fix OSD crashing when not using Wayland (regression after GTK 4 migration)
- Fix loading button icons in some cases
- Fix run.sh loading cached build files
- Fix crash on launch if scc directory is present in some pre-defined paths,
  but the rest of the expected files aren't there
- Log files are now created per each of the various components when using
  development versions - or when a special debug file is present
- Some deprecation fixes
- Initial package
