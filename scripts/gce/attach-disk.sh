GCE_NODE_NAME=$(hostname)
: ${GCE_DISK_SIZE:="200GB"}
: ${GCE_ZONE:="us-east2-a"}

gcloud compute disks create sdb-$GCE_NODE_NAME --size=$GCE_DISK_SIZE --zone=$GCE_ZONE
gcloud compute instances attach-disk $GCE_NODE_NAME --disk sdb-$GCE_NODE_NAME --zone=$GCE_ZONE
mkdir -p /grid/0
mkfs.ext4 -F -E lazy_itable_init=0,discard /dev/disk/by-id/google-persistent-disk-1
mount -t ext4 /dev/disk/by-id/google-persistent-disk-1 /grid/0
chmod a+w /grid/0/