
: ${REALM:=EXAMPLE.COM}
: ${DOMAIN_REALM:=ambari.apache.org}
: ${KERB_MASTER_KEY:=masterkey}
: ${KERB_ADMIN_USER:=admin}
: ${KERB_ADMIN_PASS:=admin}

create_config() {
  : ${KDC_ADDRESS:=$(hostname -f)}

  cat>/etc/krb5.conf<<EOF
[logging]
 default = FILE:/var/log/kerberos/krb5libs.log
 kdc = FILE:/var/log/kerberos/krb5kdc.log
 admin_server = FILE:/var/log/kerberos/kadmind.log
[libdefaults]
 default_realm = $REALM
 dns_lookup_realm = false
 dns_lookup_kdc = false
 ticket_lifetime = 24h
 renew_lifetime = 7d
 forwardable = true
[realms]
 $REALM = {
  kdc = $KDC_ADDRESS
  admin_server = $KDC_ADDRESS
 }
[domain_realm]
 .$DOMAIN_REALM = $REALM
 $DOMAIN_REALM = $REALM
EOF
  cat>/var/kerberos/krb5kdc/kdc.conf<<EOF
[kdcdefaults]
 kdc_ports = 88
 kdc_tcp_ports = 88

[realms]
 $REALM = {
  #master_key_type = aes256-cts
  acl_file = /var/kerberos/krb5kdc/kadm5.acl
  dict_file = /usr/share/dict/words
  admin_keytab = /var/kerberos/krb5kdc/kadm5.keytab
  supported_enctypes = aes256-cts:normal aes128-cts:normal des3-hmac-sha1:normal arcfour-hmac:normal des-hmac-sha1:normal des-cbc-md5:normal des-cbc-crc:normal
 }
EOF
}

create_db() {
  /usr/sbin/kdb5_util -P $KERB_MASTER_KEY -r $REALM create -s
}

start_kdc() {
  mkdir -p /var/log/kerberos

  /etc/rc.d/init.d/krb5kdc start
  /etc/rc.d/init.d/kadmin start

  chkconfig krb5kdc on
  chkconfig kadmin on
}

create_admin_user() {
  kadmin.local -q "addprinc -pw $KERB_ADMIN_PASS $KERB_ADMIN_USER/admin"
  echo "*/admin@$REALM *" > /var/kerberos/krb5kdc/kadm5.acl
}

mkdir -p /var/log/kerberos/
yum install krb5-server krb5-libs krb5-auth-dialog krb5-workstation -y
yum install rng-tools -y
sed 's/""/"-r \/dev\/urandom"/' -i /etc/sysconfig/rngd
/etc/init.d/rngd start
create_config
create_db
create_admin_user
start_kdc
