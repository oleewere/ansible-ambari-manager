# ansible-ambari-manager

## Playbook example:
```bash
ansible-playbook -i hosts.sample playbooks/install-ambari-2_6.yml --extra-vars "ambari_build_version=103"
```

## Run command on group
```bash
ansible -i hosts ambari-server -m shell -a "echo hello"
```