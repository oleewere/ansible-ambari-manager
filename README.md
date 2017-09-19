# ansible-ambari-manager

## Requirements:

Install ansible (2.x) 
```bash
pip install ansible
```
## Setup

Create an invertory file (based on hosts.sample) with proper hosts/variables which can be used for the playbooks.
Also make sure the default variables (group_vars/all) is redefined in your inventory file if it's required

## Examples

### Run command on group
```bash
ansible -i hosts ambari-server -m shell -a "echo hello"
```

### Install Ambari 2.6:
```bash
ansible-playbook -i hosts.sample playbooks/install-ambari-2_6.yml --extra-vars "ambari_build_number=103"
```

### Setup Kerberos:
```bash
ansible-playbook -i hosts.sample playbooks/setup-kerberos.yml --extra-vars "kerberos_domain_realm=ambari.apache.org"
```

### Install Solr Metrics Sink mpack:
```bash
ansible-playbook -i hosts.sample playbooks/mpacks/install-infra-solr-metrics-mpack.yml
```

### Install Solr Metrics Sink service/components:
```bash
ansible-playbook -i hosts.sample playbooks/mpacks/add-infra-solr-metrics-mpack.yml
```

### Upgarde Ambari (e.g.: 2.6.0.0 -> 3.0.0.0)
```bash
ansible-playbook -i hosts.sample playbooks/upgrade-ambari-packages.yml -v --extra-vars "ambari_base_url=http://s3.amazonaws.com/dev.hortonworks.com/ambari/centos6/3.x/BUILDS/3.0.0.0-1116 ambari_version=3.0.0.0 ambari_build_number=1116"
```

### Upgarde Ambari - build number change only (2.6.0.0-102 -> 2.6.0.0-113)
```bash
ansible-playbook -i hosts.sample playbooks/upgrade-ambari-packages.yml -v --extra-vars "ambari_base_url=http://s3.amazonaws.com/dev.hortonworks.com/ambari/centos6/2.x/BUILDS/2.6.0.0-113 ambari_version=2.6.0.0 ambari_build_number=113 skip_ambari_server_upgrade=True"
```
