sites:
  hatherleigh_info:
    db_pass: myPassword
    db_type: mysql
    domain: hatherleigh.info
    mailgun_receive: True
    php: True
    secret_key: 'abc'
    ssl: False
    packages:
      - name: drupal
        archive: drupal-6.29.tar.gz
        tar: --strip-components=1
      - name: date
        archive: date-6.x-2.9.tar.gz
