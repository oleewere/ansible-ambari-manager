yum clean all

yum install openldap-servers openldap-clients sssd perl-LDAP.noarch nss-pam-ldapd -y

LDAP_SERVER=localhost
CWD=`pwd`

cp /usr/share/openldap-servers/DB_CONFIG.example /var/lib/ldap/DB_CONFIG

chown -R ldap:ldap /var/lib/ldap

cd /etc/openldap

mv slapd.d slapd.d.original

chkconfig slapd on

cp ldap.conf ldap.conf.original

cat > /etc/openldap/slapd.conf << EOFDELIM
#
# See slapd.conf(5) for details on configuration options.
# This file should NOT be world readable.
#
include 	/etc/openldap/schema/core.schema
include 	/etc/openldap/schema/cosine.schema
include 	/etc/openldap/schema/inetorgperson.schema
include 	/etc/openldap/schema/nis.schema

# Added for policy
include /etc/openldap/schema/ppolicy.schema

# Allow LDAPv2 client connections.  This is NOT the default.
allow bind_v2

# Do not enable referrals until AFTER you have a working directory
# service AND an understanding of referrals.
#referral   ldap://root.openldap.org

pidfile 	/var/run/openldap/slapd.pid
argsfile	/var/run/openldap/slapd.args

# Load dynamic backend modules:
# modulepath	/usr/lib64/openldap

# Modules available in openldap-servers-overlays RPM package
# Module syncprov.la is now statically linked with slapd and there
# is no need to load it here
# moduleload accesslog.la
# moduleload auditlog.la
# moduleload denyop.la
# moduleload dyngroup.la
# moduleload dynlist.la
# moduleload lastmod.la
# moduleload pcache.la

moduleload ppolicy.la

# moduleload refint.la
# moduleload retcode.la
# moduleload rwm.la
# moduleload smbk5pwd.la
# moduleload translucent.la
# moduleload unique.la
# moduleload valsort.la

# modules available in openldap-servers-sql RPM package:
# moduleload back_sql.la

# The next three lines allow use of TLS for encrypting connections using a
# dummy test certificate which you can generate by changing to
# /etc/pki/tls/certs, running "make slapd.pem", and fixing permissions on
# slapd.pem so that the ldap user or group can read it.  Your client software
# may balk at self-signed certificates, however.
# TLSCACertificateFile /etc/pki/tls/certs/ca-bundle.crt
# TLSCertificateFile /etc/pki/tls/certs/slapd.pem
# TLSCertificateKeyFile /etc/pki/tls/certs/slapd.pem

# Sample security restrictions
#   Require integrity protection (prevent hijacking)
#   Require 112-bit (3DES or better) encryption for updates
#   Require 63-bit encryption for simple bind
# security ssf=1 update_ssf=112 simple_bind=64

# Sample access control policy:
#   Root DSE: allow anyone to read it
#   Subschema (sub)entry DSE: allow anyone to read it
#   Other DSEs:
#   	Allow self write access
#   	Allow authenticated users read access
#   	Allow anonymous users to authenticate
#   Directives needed to implement policy:
# access to dn.base="" by * read
# access to dn.base="cn=Subschema" by * read
# access to *
#   by self write
#   by users read
#   by anonymous auth
#
# if no access controls are present, the default policy
# allows anyone and everyone to read anything but restricts
# updates to rootdn.  (e.g., "access to * by * read")
#
# rootdn can always read and write EVERYTHING!

#######################################################################
# ldbm and/or bdb database definitions
#######################################################################

database  bdb
suffix  "dc=puppetlabs,dc=test"
rootdn  "cn=ambari,dc=puppetlabs,dc=test"
rootpw  {SSHA}ckC+F39YJhds/Rn2TRZqH8Y++7+avorS

# PPolicy Configuration
overlay ppolicy
ppolicy_default "cn=default,ou=policies,dc=puppetlabs,dc=test"
ppolicy_use_lockout
ppolicy_hash_cleartext

# The database directory MUST exist prior to running slapd AND
# should only be accessible by the slapd and slap tools.
# Mode 700 recommended.
directory   /var/lib/ldap

# Indices to maintain for this database
index objectClass  eq,pres
index ou,cn,mail,surname,givenname  eq,pres,sub
index uidNumber,gidNumber,loginShell  eq,pres
index uid,memberUid  eq,pres,sub
index nisMapName,nisMapEntry  eq,pres,sub
EOFDELIM

cat > /etc/openldap/ppolicy.ldif << EOFDELIM
dn: ou = policies,dc=puppetlabs,dc=test
objectClass: organizationalUnit
objectClass: top
ou: policies

# default, policies, example.com
dn: cn=default,ou=policies,dc=puppetlabs,dc=test
objectClass: top
objectClass: pwdPolicy
objectClass: person
cn: default
sn: dummy value
pwdAttribute: userPassword
pwdMaxAge: 7516800
pwdExpireWarning: 14482463
pwdMinLength: 2
pwdMaxFailure: 10
pwdLockout: TRUE
pwdLockoutDuration: 60
pwdMustChange: FALSE
pwdAllowUserChange: FALSE
pwdSafeModify: FALSE
EOFDELIM

service slapd start

# artbitary sleep to wait long enough for slapd to make the rest of the script work...
sleep 5

ldapsearch -h localhost -D "cn=ambari,dc=puppetlabs,dc=test" -w yoursecretpassword -b "dc=puppetlabs,dc=test" -s sub "objectclass=*"

cat > /etc/openldap/ldap-init.ldif << EOFDELIM
dn: dc=puppetlabs,dc=test
objectClass: top
objectClass: domain
dc: apache

dn: ou=dev,dc=puppetlabs,dc=test
objectClass: top
objectClass: OrganizationalUnit
ou: dev

dn: ou=people,ou=dev,dc=puppetlabs,dc=test
objectClass: top
objectClass: OrganizationalUnit
ou: people

dn: ou=groups,ou=dev,dc=puppetlabs,dc=test
objectClass: top
objectClass: OrganizationalUnit
ou: groups
EOFDELIM

ldapadd -x -D "cn=ambari,dc=puppetlabs,dc=test" -w yoursecretpassword -f ldap-init.ldif

cp $CWD/users_groups.ldif /etc/openldap/users_groups.ldif

ldapadd -x -D "cn=ambari,dc=puppetlabs,dc=test" -w yoursecretpassword  -f users_groups.ldif

cat > /etc/openldap/ldap.conf << EOFDELIM
URI ldap://LDAP_SERVER:389
BASE dc=puppetlabs,dc=test
TLS_CACERTDIR /etc/openldap/certs
EOFDELIM

sed -i "s/LDAP_SERVER/$LDAP_SERVER/" /etc/openldap/ldap.conf

cat > /etc/nslcd.conf << EOFDELIM
uri ldap://LDAP_SERVER:389
base dc=puppetlabs,dc=test
ssl no
tls_cacertdir /etc/openldap/cacerts
EOFDELIM

sed -i "s/LDAP_SERVER/$LDAP_SERVER/" /etc/nslcd.conf

cat > /etc/pam_ldap.conf << EOFDELIM
uri ldap://LDAP_SERVER:389
base dc=puppetlabs,dc=test
ssl no
tls_cacertdir /etc/openldap/cacerts
pam_password md5
EOFDELIM

sed -i "s/LDAP_SERVER/$LDAP_SERVER/" /etc/pam_ldap.conf

cat > /etc/pam.d/system-auth << EOFDELIM
#%PAM-1.0
# This file is auto-generated.
# User changes will be destroyed the next time authconfig is run.
auth        required      pam_env.so
auth        sufficient    pam_unix.so nullok try_first_pass
auth        requisite     pam_succeed_if.so uid >= 500 quiet
auth        required      pam_deny.so
auth        sufficient    pam_ldap.so use_first_pass

account     required      pam_unix.so
account     [default=bad success=ok user_unknown=ignore] pam_ldap.so
account     sufficient    pam_localuser.so
account     sufficient    pam_succeed_if.so uid < 500 quiet
account     required      pam_permit.so

password    requisite     pam_cracklib.so try_first_pass retry=3 type=
password    sufficient    pam_unix.so md5 shadow nullok try_first_pass use_authtok
password    required      pam_deny.so

password    sufficient    pam_ldap.so use_authtok

session     optional      pam_keyinit.so revoke
session     required      pam_limits.so
session     [success=1 default=ignore] pam_succeed_if.so service in crond quiet use_uid
session     required      pam_unix.so
session     optional      pam_ldap.so
# add if you need ( create home directory automatically if it's none )
session     optional      pam_mkhomedir.so skel=/etc/skel umask=077
EOFDELIM

cat > /etc/nsswitch.conf << EOFDELIM
passwd:     files ldap
shadow:     files ldap
group:      files ldap

#hosts:     db files nisplus nis dns
hosts:      files dns

# Example - obey only what nisplus tells us...
#services:   nisplus [NOTFOUND=return] files
#networks:   nisplus [NOTFOUND=return] files
#protocols:  nisplus [NOTFOUND=return] files
#rpc:        nisplus [NOTFOUND=return] files
#ethers:     nisplus [NOTFOUND=return] files
#netmasks:   nisplus [NOTFOUND=return] files

bootparams: nisplus [NOTFOUND=return] files

ethers:     files
netmasks:   files
networks:   files
protocols:  files
rpc:        files
services:   files

netgroup:   ldap

publickey:  nisplus

automount:  files ldap
aliases:    files nisplus
EOFDELIM

cat > /etc/sysconfig/authconfig << EOFDELIM
IPADOMAINJOINED=no
USEMKHOMEDIR=no
USEPAMACCESS=no
CACHECREDENTIALS=yes
USESSSDAUTH=no
USESHADOW=yes
USEWINBIND=no
USEDB=no
FORCELEGACY=no
USEFPRINTD=no
FORCESMARTCARD=no
PASSWDALGORITHM=md5
USELDAPAUTH=yes
USEPASSWDQC=no
IPAV2NONTP=no
USELOCAUTHORIZE=yes
USECRACKLIB=yes
USEIPAV2=no
USEWINBINDAUTH=no
USESMARTCARD=no
USELDAP=no
USENIS=no
USEKERBEROS=no
USESYSNETAUTH=no
USESSSD=no
USEHESIOD=no
USEMD5=yes
EOFDELIM

chkconfig nslcd on

chkconfig iptables off

echo 'Reboot the server by running: shutdown -r now'
