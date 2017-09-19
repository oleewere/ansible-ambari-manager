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
