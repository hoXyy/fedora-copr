Name:           makima
Version:        0.10.3
Release:        1%{?dist}
Summary:        Linux input-remapping and macro daemon

License:        GPL-3.0-only
URL:            https://github.com/cyber-sushi/makima
Source0:        %{url}/archive/refs/tags/v%{version}/makima-%{version}.tar.gz

BuildRequires:  cargo
BuildRequires:  gcc
BuildRequires:  pkgconfig(libudev)
BuildRequires:  rust
BuildRequires:  systemd-rpm-macros

%description
Makima is a Linux daemon for remapping keyboards, mice, controllers, tablets,
and other evdev input devices. It can translate input events to keys, event
sequences, shell commands, pointer movement, and scrolling on both Wayland and
X11.

Its COPR build must have network access enabled so Cargo can download the
dependencies pinned by Cargo.lock.


%prep
%autosetup -p1


%build
export CARGO_HOME=%{_builddir}/cargo-home
export CARGO_TARGET_DIR=%{_builddir}/target
cargo build --locked --release


%install
install -Dpm 0755 %{_builddir}/target/release/makima \
    %{buildroot}%{_bindir}/makima
install -Dpm 0644 50-makima.rules \
    %{buildroot}%{_udevrulesdir}/50-makima.rules
install -Dpm 0644 makima.service \
    %{buildroot}%{_userunitdir}/makima.service
sed -i -e '/^User=$/d' -e '/^Group=input$/d' \
    %{buildroot}%{_userunitdir}/makima.service
install -Dpm 0644 /dev/null \
    %{buildroot}%{_modulesloaddir}/makima.conf
echo uinput > %{buildroot}%{_modulesloaddir}/makima.conf


%check
export CARGO_HOME=%{_builddir}/cargo-home
export CARGO_TARGET_DIR=%{_builddir}/target
cargo test --locked --release


%post
%systemd_user_post makima.service

%preun
%systemd_user_preun makima.service

%postun
%systemd_user_postun_with_restart makima.service


%files
%license LICENSE
%doc README.md examples
%{_bindir}/makima
%{_udevrulesdir}/50-makima.rules
%{_userunitdir}/makima.service
%{_modulesloaddir}/makima.conf


%changelog
* Thu Oct 08 2026 Fedora COPR Maintainer <noreply@example.com> - 0.10.3-1
- Initial package
