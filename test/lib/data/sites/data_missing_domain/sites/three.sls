sites:
  csw_web:
    profile: django
    db_pass: myPassword
    db_type: psql
    domain: westcountrycoders.co.uk
    mailgun_receive: True
    secret_key: 'abc'
    ssl: True
    uwsgi_port: '3031'
  csw_mail:
    profile: django
    db_pass: myPassword
    db_type: psql
    secret_key: 'def'
    ssl: True
    uwsgi_port: '3032'
