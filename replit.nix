{pkgs}: {
  deps = [
    pkgs.dialog
    pkgs.certbot
    pkgs.psmisc
    pkgs.postgresql
    pkgs.openssl
  ];
}
