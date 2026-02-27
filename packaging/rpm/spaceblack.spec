Name:           spaceblack
Version:        1.0.0
Release:        1%{?dist}
Summary:        Space Black — Terminal AI Agent Infrastructure
License:        MIT
URL:            https://github.com/udaysagar/SpaceBlack
BuildArch:      noarch

Requires:       python3 >= 3.10
Requires:       python3-pip

%description
Space Black is a terminal-based AI infrastructure designed to host
autonomous agents. It provides CLI, file system access, browser engine,
and memory system for local AI agents. Ghost is the default AI agent.

After installation, run 'ghost start' to launch the agent.

%install
mkdir -p "%{buildroot}/opt/spaceblack"
cp -a "%{_sourcedir}/app/"* "%{buildroot}/opt/spaceblack/"
mkdir -p "%{buildroot}/usr/local/bin"

%post
# Install the ghost CLI launcher
mkdir -p /usr/local/bin
ln -sf /opt/spaceblack/packaging/ghost /usr/local/bin/ghost

# Set permissions on scripts
chmod +x /opt/spaceblack/spaceblack 2>/dev/null || true
chmod +x /opt/spaceblack/scripts/*.sh 2>/dev/null || true

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  Space Black installed successfully!             ║"
echo "║                                                  ║"
echo "║  Run:  ghost start                               ║"
echo "║                                                  ║"
echo "║  Setup runs automatically on first launch.       ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

%preun
rm -f /usr/local/bin/ghost
rm -rf /opt/spaceblack/.venv

%files
/opt/spaceblack/

%changelog
* Thu Feb 26 2026 Uday Sagar <udaysagarm@github.com> - 1.0.0-1
- Initial package release
