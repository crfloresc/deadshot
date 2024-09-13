with import <nixpkgs> {};
with pkgs.python310Packages;

pkgs.mkShell rec { # mkShellNoCC
  name = "impurePythonEnv";
  # venvDir = "./.venv";

  NIX_LD_LIBRARY_PATH = lib.makeLibraryPath [
    stdenv.cc.cc
  ];
  NIX_LD = lib.fileContents "${stdenv.cc}/nix-support/dynamic-linker";
  # libraries = with pkgs; [
  #   stdenv.cc.cc.lib
  # ];

  packages = [
    python310Packages.pip
  ]

  buildInputs = [
    gcc
    glibc
    # stdenv.cc.cc.lib
    python310Packages.pip
    python310Packages.python
    # python310Packages.venvShellHook
  ];

  # postVenvCreation = ''
  #   unset SOURCE_DATE_EPOCH
  #   pip install -r requirements.txt
  # '';

  # postShellHook = ''
  #   # allow pip to install wheels
  #   unset SOURCE_DATE_EPOCH
  # '';
}
