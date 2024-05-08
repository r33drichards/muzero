{ pkgs ? import <nixpkgs> { } }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    pkgs.python39
    swig4
    ffmpeg
    snappy

  ];
  shellHook = ''
  # if .venv does not exist, create it
  if [ ! -d .venv ]; then
    python3 -m venv .venv
  fi

  # activate the virtual environment
  source .venv/bin/activate
  '';
}