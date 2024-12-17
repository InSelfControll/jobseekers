{pkgs}: {
  deps = [
    pkgs.sysvinit
    pkgs.dialog
    pkgs.certbot
    pkgs.psmisc
    pkgs.postgresql
    pkgs.openssl
  ];
}
