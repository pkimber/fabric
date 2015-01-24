base:
  'drop':
    - config.django
    - db.settings
    - sites.kb
  'drop-test':
    - config.django
    - config.testing
    - db.settings
    - sites.kb
