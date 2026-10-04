%global commit      225dcd7acb83a0cfcbfff09584160c1a09ec58ee
%global shortcommit 225dcd7
%global commitdate  20260807

Name:           livesplit-one-gtk-git
Version:        0.7.2~git20260807.225dcd7
Release:        1%{?dist}
Summary:        GTK desktop version of LiveSplit One built from git

License:        MIT
URL:            https://github.com/hoXyy/livesplit-one-gtk
Source0:        %{url}/archive/%{commit}/livesplit-one-gtk-%{commit}.tar.gz

# Native Rust dependencies build C and C++ code. Upstream disables distribution
# LTO because those objects cannot be consumed by Cargo's final link.
%global _lto_cflags %{nil}

BuildRequires:  cargo
BuildRequires:  desktop-file-utils
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  pkgconfig(gtk4) >= 4.14
BuildRequires:  pkgconfig(libadwaita-1) >= 1.5
BuildRequires:  pkgconfig(x11)
BuildRequires:  rust

Requires:       hicolor-icon-theme
Provides:       livesplit-one-gtk = %{version}-%{release}
Conflicts:      livesplit-one-gtk

%description
LiveSplit One GTK is an unofficial Linux desktop version of the LiveSplit One
speedrunning timer. It uses GTK 4 and libadwaita and supports layouts, split
editing, notes, global hotkeys, and autosplitters.

This package tracks the upstream main branch. Its COPR build must have network
access enabled so Cargo can download the dependencies pinned by Cargo.lock.


%prep
%autosetup -n livesplit-one-gtk-%{commit} -p1


%build
export CARGO_HOME=%{_builddir}/cargo-home
export CARGO_TARGET_DIR=%{_builddir}/target
cargo build --locked --release


%install
install -Dpm 0755 %{_builddir}/target/release/livesplit-one \
    %{buildroot}%{_bindir}/livesplit-one-gtk
install -Dpm 0644 packaging/livesplit-one-gtk.desktop \
    %{buildroot}%{_datadir}/applications/livesplit-one-gtk.desktop
install -Dpm 0644 icons/icon.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/livesplit-one-gtk.svg
install -Dpm 0644 icons/icon.png \
    %{buildroot}%{_datadir}/pixmaps/livesplit-one-gtk.png


%check
export CARGO_HOME=%{_builddir}/cargo-home
export CARGO_TARGET_DIR=%{_builddir}/target
cargo test --locked --release --all-features
desktop-file-validate \
    %{buildroot}%{_datadir}/applications/livesplit-one-gtk.desktop


%files
%license LICENSE
%doc README.md
%{_bindir}/livesplit-one-gtk
%{_datadir}/applications/livesplit-one-gtk.desktop
%{_datadir}/icons/hicolor/scalable/apps/livesplit-one-gtk.svg
%{_datadir}/pixmaps/livesplit-one-gtk.png


%changelog
* Sun Oct 04 2026 Fedora COPR Maintainer <noreply@example.com> - 0.7.2~git20260807.225dcd7-1
- Package upstream main-branch snapshot 225dcd7
