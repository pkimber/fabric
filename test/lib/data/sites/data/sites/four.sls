sites:
  csw_web:
    amazon: True
    profile: django
    db_pass: myPassword
    db_type: psql
    domain: westcountrycoders.co.uk
    mailgun_receive: True
    secret_key: 'abc'
    ssl: True
    uwsgi_port: '3031'
    mail:
      mail_template_type: django
  csw_mail:
    profile: django
    db_pass: myNextPassword
    db_type: psql
    domain: westcountrycycles.co.uk
    secret_key: 'def'
    ssl: True
    uwsgi_port: '3032'
  test_crm:
    amazon: True
    compress: False
    profile: django
    db_pass: myPassword
    db_type: mysql
    domain: westcountrycoders.co.uk
    mailgun_receive: True
    secret_key: 'abc'
    ssl: False
    uwsgi_port: '3033'
    mail:
      mail_template_type: mandrill
  test_nodb:
    profile: django
    db_type: ''
    domain: westcountrycycles.co.uk
    secret_key: 'def'
    ssl: True
    uwsgi_port: '3034'
