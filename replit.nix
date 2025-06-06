{ pkgs }: {
    deps = [
        pkgs.python38Full
        pkgs.python38Packages.pip
        pkgs.python38Packages.virtualenv
    ];
    env = {
        PYTHONPATH = "${pkgs.python38Full}/${pkgs.python38Full.sitePackages}";
    };
} 