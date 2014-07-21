base:
  'drop-temp':
    - config.django
    - config.mysql_server_local
    - config.postgres_server_local
    - db.csw.settings
    - global.amazon
    - global.pip
    - sites.four
