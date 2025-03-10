#!/bin/bash

#
# Enable IP forwarding
#
sed -i 's/^net.ipv4.ip_forward = 0/net.ipv4.ip_forward = 1/' /etc/sysctl.conf && sudo sysctl -p |true
echo "Pre-bootstrap configurations applied."

#
# Get instance family type
#
token=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
instance_type=$(curl -H "X-aws-ec2-metadata-token: $token" http://169.254.169.254/latest/dynamic/instance-identity/document | grep "instanceType" | awk -F\" '{print $4}')
instance_family="${instance_type%%.*}"
echo "Instance family: $instance_family"

#
# Exit if instance family does not support NVME SSD instance store
#
if [[ $instance_family != "m5ad" ]]; then
  exit 0
fi

# Create a filesystem path to mount the disk
# The location is CRITIAL here. It it root path used by kubelets to host
# the scratch directories requested by Pods
# MOUNT_LOCATION="/var/lib/kubelet/pods"
MOUNT_LOCATION="/data"
mkdir -p $MOUNT_LOCATION

#
# Install NVMe CLI, Software RAID Utility
#
yum update -y
yum install nvme-cli mdadm -y

#
# Get a list of instance-store NVMe drives. If none found, do not fail.
#
nvme_drives=$(nvme list | grep "Amazon EC2 NVMe Instance Storage" | cut -d " " -f 1 || true)

#
# Build an array object
readarray -t nvme_drives <<< "$nvme_drives"

#
# Get number of disks available.
#
num_drives=${#nvme_drives[@]}

#
# Test to see if there is only 1 NVMe drive; create a RAID array if num_drives > 1
#
if [[ $num_drives -gt 1 ]]; then

    echo "Formatting instance store as a RAID device."

    # Create RAID-0 array across the instance store NVMe SSDs
    mdadm --create /dev/md0 --level=0 --name=md0 --raid-devices=$num_drives "${nvme_drives[@]}"

    # Format drive with ext4
    # Please note: THIS IS JUST AN EXAMPLE HERE. You may implemented advanced
    # formatting option. Refers to the mkfs.ext4 documentation
    #
    #     https://linux.die.net/man/8/mkfs.ext4
    #
    mkfs.ext4 /dev/md0

    #
    # Mount RAID device finally
    mount /dev/md0 $MOUNT_LOCATION

    #
    # Have disk be mounted on reboot
    #
    mdadm --detail --scan >> /etc/mdadm.conf
    echo /dev/md0 $MOUNT_LOCATION ext4 defaults,noatime 0 2 >> /etc/fstab

    echo "Mounted /dev/md0 to $MOUNT_LOCATION."
    df -h $MOUNT_LOCATION

#
# There is only one NVMe drive
#
else

    echo "Formatting instance store as a single drive."

    #
    # Format the NVMe drive
    #
    nvme_drive=${nvme_drives[0]}
    mkfs -t xfs $nvme_drive

    #
    # Mount NVMe drive to mount
    #
    mount $nvme_drive $MOUNT_LOCATION

    #
    # Have disk mounted on reboot
    #
    echo $nvme_drive $MOUNT_LOCATION xfs defaults,noatime 0 2 >> /etc/fstab

    echo "Mounted $nvme_drive to $MOUNT_LOCATION."
    df -h $MOUNT_LOCATION

fi
