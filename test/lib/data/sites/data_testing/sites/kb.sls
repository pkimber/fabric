sites:
  kb_couk:
    profile: django
    domain: kbsoftware.co.uk
    ssl: True
    uwsgi_port: 3038
    db_pass: letmein
    db_type: psql
    celery: True
    test:
      domain: test.kbsoftware.co.uk
  kbnot_couk:
    profile: django
    domain: kbnotsoftware.co.uk
    ssl: False
    uwsgi_port: 3039
    db_pass: letmeout
    db_type: psql
