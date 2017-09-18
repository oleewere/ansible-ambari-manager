# ansible-ambari-manager

## Playbook example:
```bash
ansible-playbook -i hosts.sample playbooks/install-ambari-2_6.yml --extra-vars "ambari_build_version=103"
```