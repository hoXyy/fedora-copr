%global commit          a7c2620b9f72a327e049a2f9750a8d21bc0f14dc
%global shortcommit     a7c2620
%global commitdate      20260826

Name:           axolotl-apclient-git
Version:        0.1.6~git20260826.a7c2620
Release:        2%{?dist}
Summary:        Development snapshot of the Archipelago multiworld text client

# Axolotl, Dear ImGui, sol2, and Lua are MIT; IXWebSocket is BSD-3-Clause.
License:        MIT AND BSD-3-Clause
URL:            https://github.com/mooinglemur/axolotl
Source0:        %{url}/archive/%{commit}/axolotl-%{commit}.tar.gz

# GitHub-generated archives do not contain git submodule contents. These
# revisions are the gitlinks recorded by the snapshot commit above.
%global ixwebsocket_commit 150e3d83b5f6a2a47f456b79330a9afe87cd379c
%global imgui_commit       934c6a5f5ef2355d6df25395d555cb71f790c4e9
%global lua_commit         6443185167c77adcc8552a3fee7edab7895db1a9
%global sol2_commit        c1f95a773c6f8f4fde8ca3efe872e7286afe4444
Source1:        https://github.com/machinezone/IXWebSocket/archive/%{ixwebsocket_commit}/IXWebSocket-%{ixwebsocket_commit}.tar.gz
Source2:        https://github.com/ocornut/imgui/archive/%{imgui_commit}/imgui-%{imgui_commit}.tar.gz
Source3:        https://github.com/lua/lua/archive/%{lua_commit}/lua-%{lua_commit}.tar.gz
Source4:        https://github.com/ThePhD/sol2/archive/%{sol2_commit}/sol2-%{sol2_commit}.tar.gz

BuildRequires:  cmake
BuildRequires:  desktop-file-utils
BuildRequires:  gcc-c++
BuildRequires:  ninja-build
BuildRequires:  pkgconfig(fontconfig)
BuildRequires:  pkgconfig(gl)
BuildRequires:  pkgconfig(glfw3)
BuildRequires:  pkgconfig(libzip)
BuildRequires:  pkgconfig(openssl)
BuildRequires:  pkgconfig(yaml-cpp)
BuildRequires:  python3
BuildRequires:  cmake(nlohmann_json)

Provides:       axolotl-apclient = %{version}-%{release}
Conflicts:      axolotl-apclient

# The upstream build currently compiles these pinned libraries directly.
Provides:       bundled(ixwebsocket)
Provides:       bundled(imgui)
Provides:       bundled(lua)
Provides:       bundled(sol2)

%description
Axolotl is a lightweight graphical client for Archipelago multiworld
sessions. It supports multiple slots, chat, item and hint tracking,
personalized feeds, and streamer-friendly display options.

This package tracks a development snapshot from the upstream main branch.


%prep
%autosetup -n axolotl-%{commit} -p1
tar -xf %{SOURCE1}
tar -xf %{SOURCE2}
tar -xf %{SOURCE3}
tar -xf %{SOURCE4}
# GitHub's archive contains empty directories for the gitlinks. Remove those
# placeholders so the extracted repositories are not moved one level too deep.
rm -rf thirdparty/IXWebSocket thirdparty/imgui thirdparty/lua thirdparty/sol2
mv IXWebSocket-%{ixwebsocket_commit} thirdparty/IXWebSocket
mv imgui-%{imgui_commit} thirdparty/imgui
mv lua-%{lua_commit} thirdparty/lua
mv sol2-%{sol2_commit} thirdparty/sol2


%build
%cmake -G Ninja \
    -DAXOLOTL_IGNORE_DIRTY=ON \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo
%cmake_build


%install
%cmake_install
install -Dpm 0644 com.mooinglemur.axolotl.desktop \
    %{buildroot}%{_datadir}/applications/com.mooinglemur.axolotl.desktop
install -Dpm 0644 com.mooinglemur.axolotl.png \
    %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/com.mooinglemur.axolotl.png


%check
desktop-file-validate \
    %{buildroot}%{_datadir}/applications/com.mooinglemur.axolotl.desktop


%files
%license LICENSE.txt
%doc README.md documentation/README.md
%{_bindir}/axolotl-apclient
%{_datadir}/applications/com.mooinglemur.axolotl.desktop
%{_datadir}/icons/hicolor/128x128/apps/com.mooinglemur.axolotl.png


%changelog
* Sun Oct 04 2026 Fedora COPR Maintainer <noreply@example.com> - 0.1.6~git20260826.a7c2620-2
- Fix reconstruction of vendored submodules from GitHub archives

* Sun Oct 04 2026 Fedora COPR Maintainer <noreply@example.com> - 0.1.6~git20260826.a7c2620-1
- Package upstream development snapshot a7c2620
