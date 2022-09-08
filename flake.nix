{
  description = "dev utilities for working with github.com/reserve-protocol/protocol";

  inputs = {
    nixpkgs.url = github:NixOS/nixpkgs/release-22.05;
    flake-utils.url = github:numtide/flake-utils;
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
    with nixpkgs.legacyPackages.${system};
    with lib;
    let
      scripts = {
        example = "echo hello from $ENV_ROOT";
      };
    in {
      devShell = stdenvNoCC.mkDerivation {
        name = "shell";
        buildInputs = attrsets.mapAttrsToList writeShellScriptBin scripts ++ [
        ];
      };
    });
}
