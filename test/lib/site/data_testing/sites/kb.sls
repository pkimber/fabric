sites:
  kb_couk:
    profile: django
    domain: kbsoftware.co.uk
    ssl: True
    uwsgi_port: 3038
    db_pass: letmein
    db_type: psql
    test:
      domain: test.kbsoftware.co.uk
