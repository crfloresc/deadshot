with import <nixpkgs> {};
with pkgs.python310Packages;

# let
#   pkgs = import <nixpkgs> {};
#   pythonEnv = pkgs.python310.withPackages(ps: [
#     ps.pip
#     ps.setuptools
#     ps.bokeh
#     ps.nltk
#     ps.scipy
#   ]);
# in pkgs.mkShell {
#   packages = [
#     pythonEnv
#   ];

#   shellHook = ''
#     pip freeze > requirements.txt
#     pip install -r requirements.txt
#     python setup.py build
#     python setup.py develop
#   '';
# }

# let bokeh_installed = (
#   let bokeh_module = (
#     python310.pkgs.buildPythonPackage rec {
#       pname = "bokeh";
#       version = "2.3.3";
#       src = ./.;
#     }
#   );
#   in python310.withPackages(ps: [
#     bokeh_module
#   ])
# );

# stdenv.mkDerivation = {
#   pname = "bokeh";
#   version = "2.2.3";
#   buildInputs = [ bokeh_installed ];
# };
let
  bokehVersion = python310Packages.bokeh.overrideAttrs (old: {
    version = "2.3.3";
    src = pkgs.fetchPypi {
      pname = "bokeh";
      version = "2.3.3";
      sha256 = "a5fdcc181835561447fcc5a371300973fce4114692d5853addec284d1cdeb677";
    };
  });
  requirements = [
    { name = "bokeh"; version = "2.3.3"; }
    { name = "nltk"; version = "3.8.1"; }
    { name = "scipy"; version = "1.11.4"; }
  ];
  requirementsPackages = map (pkg: python310Packages."${pkg.name}".overrideAttrs (old: { version = pkg.version; })) requirements;
in
buildPythonPackage rec {
  name = "hel";
  src = ./.;

  propagatedBuildInputs = [
    # pkgs.stdenv.cc.cc.lib
    bokeh
    nltk
    scipy
  ];

  preBuild = ''
    cat > setup.py << EOF
from setuptools import setup, find_packages

with open('requirements.txt') as f:
  install_requires = f.read().splitlines()

setup(
  name='deadshot',
  packages=find_packages(),
  version='1.0.0',
  author='Carlos Flores',
  author_email='carlos.flores@potros.itson.edu.mx',
  description='NA',
  python_requires='>=3.6',
  install_requires=install_requires,
  entry_points={
    'console_scripts': ['deadshot = app.bin.app:main']
  },
)
EOF
  '';

  postInstall = ''
    mv $out/bin/deadshot ./out
  '';
}
