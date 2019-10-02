with import <nixpkgs> {};

(python3.withPackages (ps: [ps.flask ps.libvirt ps.xmltodict ps.pyyaml])).env
