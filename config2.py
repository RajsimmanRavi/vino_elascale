#!/usr/bin/env python

# vim: tabstop=4 shiftwidth=4 softtabstop=4 expandtab

'''
config.py
===============

This configuration file defines the user parameters and some defualt VM parameters
for cases where they were left out
'''


username="xxxx"
password="xxxx"
auth_url='xxxx'

# Prefix, prepend to instance names
instance_prefix="iot-"+username+"-"

# Key-pair name
key_name=username+"key"

# Private key file path (needed to auto-SSH into the VMs)
# Example private key file path: '/home/savitb/user1/.ssh/id_rsa'
private_key_file='xxxx'

# Default parameters for Nodes if region wasn't specified in the topology2.py file
region_name="xxxx"
tenant_name="xxxx"

# Default instances properties
#image_name="ECE1548.OFLab"
#image_name="Ubuntu64-3-OVS"
#image_name="Ubuntu-16-04-OVS"
image_name="Ubuntu-16-04-OVS-DOCKER"
flavor_name="m1.small"
sec_group_name=username
vm_user_name="ubuntu"

