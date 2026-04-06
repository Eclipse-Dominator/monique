{
  description = "MONitor Integrated QUick Editor — graphical monitor configurator for Hyprland and Sway";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    let
      # Derivazione riutilizzabile (riceve pkgs dal chiamante)
      mkMonique = pkgs: pkgs.python3Packages.buildPythonPackage {
        pname = "monique";
        version = "0.5.0";
        format = "pyproject";

        src = self;

        nativeBuildInputs = with pkgs; [
          python3Packages.setuptools
          wrapGAppsHook4
          gobject-introspection
        ];

        buildInputs = with pkgs; [
          gtk4
          libadwaita
        ];

        propagatedBuildInputs = with pkgs.python3Packages; [
          pygobject3
          pyudev
        ];

        postInstall = ''
          install -Dm644 data/com.github.monique.desktop \
            $out/share/applications/com.github.monique.desktop
          install -Dm644 data/com.github.monique.svg \
            $out/share/icons/hicolor/scalable/apps/com.github.monique.svg
          install -Dm644 data/moniqued.service \
            $out/lib/systemd/user/moniqued.service
        '';

        # I test non esistono ancora
        doCheck = false;

        meta = with pkgs.lib; {
          description = "MONitor Integrated QUick Editor — graphical monitor configurator for Hyprland and Sway";
          homepage = "https://github.com/ToRvaLDz/monique";
          license = licenses.gpl3Plus;
          platforms = platforms.linux;
          mainProgram = "monique";
        };
      };
    in
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        packages.default = mkMonique pkgs;

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python3
            python3Packages.pygobject3
            python3Packages.pyudev
            python3Packages.setuptools
            gtk4
            libadwaita
            gobject-introspection
          ];
        };
      }
    ) // {
      # Overlay: nix.overlays = [ monique.overlays.default ]
      overlays.default = final: _prev: {
        monique = mkMonique final;
      };

      # NixOS module
      nixosModules.default = { config, lib, pkgs, ... }:
        let
          cfg = config.programs.monique;
          package = mkMonique pkgs;
        in
        {
          options.programs.monique = {
            enable = lib.mkEnableOption "Monique monitor configurator";

            enablePolkit = lib.mkOption {
              type = lib.types.bool;
              default = true;
              description = ''
                Installa la regola polkit per consentire scritture su
                /usr/share/sddm/scripts/Xsetup e /etc/greetd/monique-monitors.conf
                senza richiedere la password.
              '';
            };
          };

          config = lib.mkIf cfg.enable {
            environment.systemPackages = [ package ];

            # Regola polkit: usa il percorso Nix di coreutils per `tee`
            security.polkit.extraConfig = lib.mkIf cfg.enablePolkit ''
              polkit.addRule(function(action, subject) {
                if (action.id === "org.freedesktop.policykit.exec" &&
                    action.lookup("program") === "${pkgs.coreutils}/bin/tee" &&
                    (action.lookup("command_line").indexOf("/usr/share/sddm/scripts/Xsetup") !== -1 ||
                     action.lookup("command_line").indexOf("/etc/greetd/monique-monitors.conf") !== -1) &&
                    subject.active === true &&
                    subject.local  === true) {
                    return polkit.Result.YES;
                }
              });
            '';
          };
        };
    };
}
