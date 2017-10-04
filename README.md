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
ansible-playbook -i hosts.sample playbooks/upgrade-ambari-packages.yml -v --extra-vars "ambari_base_url=http://s3.amazonaws.com/dev.hortonworks.com/ambari/centos6/2.x/BUILDS/2.6.0.0-113 ambari_version=2.6.0.0 ambari_build_number=113 skip_ambari_server_upgrade_command=True"
```
### Local kinit to access Kerberized Solr UI from browsers
```bash
# important parameters: (you can set as --extra-vars or in the inventory file)
# - kerberos_realm: kerberos realm (default: EXAMPLE.COM)
# - kerberos_domain_realm: kerberos domain realm (default: ambari.apache.org)
# - kdc_hostname: used as --kdc-hostname parameter in the kinit command
# - keytab_file_name: filename of the keytab (saved to /tmp/<keytab_file_name>)
# - kerberos_service_user: kerberos principal name part
# - kerberos_service_host: kerberos principal host part
# (note: make sure kinit group points to that host where the service running)

ansible-playbook -i hosts.sample playbooks/local-kinit.yml -v
```

### Upload local stack to remote (common-services and stack)
```bash
# required: local_ambari_location in inventory file
ansible-playbook -i hosts.sample playbooks/local/upload-stack.yml -v
```
Or you can upload only one service as well: (add stack_service var)
```bash
ansible-playbook -i hosts playbooks/local/upload-stack.yml -v --extra-vars "stack_service=AMBARI_INFRA"
```

### Upload local Ambari agent python files to remote

```bash
ansible-playbook -i hosts.sample playbooks/local/upload-ambari-agent-python.yml -v
```

### Restart an Ambari service

```bash
ansible-playbook -i hosts.sample playbooks/service/restart.yml --extra-vars "service_name=AMBARI_INFRA" -v
```

### Save internal hostname and public IP addresses file from GCE cluster
```bash
# save to out/gce_hostnames file with internal hostname ip address pairs (you can put that into /etc/hosts)
ansible-playbook -i hosts playbooks/gce/gce-get-hosts.yml -v --extra-vars="gce_cluster_name=mycluster"
# save to out/gce_hostname file with only internal hostnames (you can put that into your inventory file)
ansible-playbook -i hosts playbooks/gce/gce-get-hosts.yml -v --extra-vars="gce_cluster_name=perf-solr gce_only_internal_address=true"
# or you can just print a public address to one hostname
ansible-playbook -i hosts playbooks/gce/print-public-ip.yml --extra-vars="gce_cluster_name=mycluster gce_hostname=hostname.internal"
```

### Ranger/Solr scale testing

#### Upload Ranger scripts for Ranger audit + Solr scale testing
First set the following params in your inventory files (or use them as extra-params):
```bash
ranger_zookeeper_quorum=localhost1:2181,localhost2:2181
ranger_sam_password=sam-password
ranger_tom_password=tom-password
ranger_admin_password=admin-password

ranger_admin_host=ranger_admin_hostname

ranger_kms_host=kms_hostname
ranger_kms_userlist=ambari-qa,hdfs,ranger

ranger_hive_host=hive_hostname
ranger_hive_userlist=hive,ambari-qa,hdfs

ranger_kafka_host=kafka_hostname
ranger_kafka_userlist=kafka

ranger_knox_host=knox_hostname

ranger_scale_test_folder=/opt
```
Then you can run (on different hosts, if hive, kafka, kms etc. are on different hosts, you can set the host with ranger_scale_test_hostname, make sure that hostname is located in your inventory somewhere):
```bash
ansible-playbook -i hosts.sample playbooks/ranger/upload-ranger-scripts.yml --extra-vars "ranger_scale_test_hostname=selected_hostname"
```
Note: libselinux-python package is required on the remote machine to generate config.ini file

#### Start ranger python scripts 
```bash
ansible-playbook -i hosts.sample playbooks/ranger/start-ranger-command.yml --extra-vars "ranger_scale_test_hostname=selected_hostname ranger_command_type=kafka ranger_command_param_days=1 ranger_command_param_threads=1 ranger_command_param_executions=1000"
```

#### Stop running ranger python scripts
```bash
ansible-playbook -i hosts.sample playbooks/ranger/stop-ranger-command.yml --extra-vars "ranger_scale_test_hostname=selected_hostname ranger_command_type=kafka"
```