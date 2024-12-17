
{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.python310Packages.certbot
    pkgs.python310Packages.pip
    pkgs.nodejs-18_x
    pkgs.nodePackages.typescript-language-server
    pkgs.nodePackages.yarn
    pkgs.replitPackages.jest
    pkgs.cloudflare-wrangler
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.python310
    ];
    PYTHONHOME = "${pkgs.python310}";
    PYTHONBIN = "${pkgs.python310}/bin/python3.10";
    LANG = "en_US.UTF-8";
    STDERRED_PATH = "${pkgs.replitPackages.stderred}/lib/libstderred.so";
    MPLBACKEND = "Agg";
    XDG_CONFIG_HOME = "$REPL_HOME/.config";
    npm_config_prefix = "$REPL_HOME/.config/npm/node_global";
  };
}
