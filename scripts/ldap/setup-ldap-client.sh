if [ $# -ne 1 ]
then
  echo ""
  echo "Usage: setup-ldap-client.sh <ldap-server-hostname>"
  echo "Example: setup-ldap-client.sh host123"
  echo ""
  exit 1
fi

yum clean all

yum install openldap-clients sssd perl-LDAP.noarch nss-pam-ldapd -y

cat > /etc/openldap/ldap.conf << EOFDELIM
URI ldap://LDAP_SERVER:389
BASE dc=puppetlabs,dc=test
TLS_CACERTDIR /etc/openldap/certs
EOFDELIM

sed -i "s/LDAP_SERVER/$1/" /etc/openldap/ldap.conf

cat > /etc/nslcd.conf << EOFDELIM
uri ldap://LDAP_SERVER:389
base dc=puppetlabs,dc=test
ssl no
tls_cacertdir /etc/openldap/cacerts
EOFDELIM

sed -i "s/LDAP_SERVER/$1/" /etc/nslcd.conf

cat > /etc/pam_ldap.conf << EOFDELIM
uri ldap://LDAP_SERVER:389
base dc=puppetlabs,dc=test
ssl no
tls_cacertdir /etc/openldap/cacerts
pam_password md5
EOFDELIM

sed -i "s/LDAP_SERVER/$1/" /etc/pam_ldap.conf

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

echo 'Reboot the server by running: shutdown -r now'
