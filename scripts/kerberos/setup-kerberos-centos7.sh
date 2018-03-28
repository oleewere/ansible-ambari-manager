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

start_kdc_centos7() {
  mkdir -p /var/log/kerberos
  systemctl start krb5kdc.service
  systemctl start kadmin.service
  systemctl enable krb5kdc.service
  systemctl enable kadmin.service
}

create_admin_user() {
  kadmin.local -q "addprinc -pw $KERB_ADMIN_PASS $KERB_ADMIN_USER/admin"
  echo "*/admin@$REALM *" > /var/kerberos/krb5kdc/kadm5.acl
}

echo "Entropy before installing RNG tools"
cat /proc/sys/kernel/random/entropy_avail

# Install packages
echo "Installing RNG tools"
yum install -y rng-tools
chkconfig rngd on
service rngd start

echo "Entropy after installing  RNG tools"
cat /proc/sys/kernel/random/entropy_avail

echo "Installing Kerberos Packages"
yum install -y krb5-server krb5-libs krb5-workstation

mkdir -p /var/log/kerberos/

create_config
create_db
create_admin_user
start_kdc_centos7
