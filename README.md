# ViNO-ELASCALE
This repository contains the initialization and setup scripts for deploying Elascale autoscaling platform on ViNO (Virtual Network Overlay). For more information regarding ViNO, refer to the following: https://www.savinetwork.ca/wp-content/uploads/savifunded/IM2015-106.pdf

This platform utilizes these specific VM images: 
*  Ubuntu-16-04-OVS-DOCKER   - For switches and Hosts
*  Ubuntu-16-04-RYU          - RYU OpenFlow Controller 

**Note:** Make sure you are logged into SAVI on client1/client2 ```(source savi ...)```

## Steps for deployment in SAVI Infrastructure ##
The following procedure describes how to setup Elascale on ViNO platform

## RYU OpenFlow Controller
In order for ViNO to be setup, you need to have a RYU OpenFlow Controller up and running. Boot a VM using the following image: Ubuntu-16-04-RYU. A small flavor will suffice. Next, run the following command:

```screen -d -m ryu-manager --config-file /etc/ryu/ryu.conf ryu.app.simple_switch```

To run QoS, you need to run the following commands:

```
tmux -l

cd /usr/local/lib/python2.7/dist-packages/ryu/app

ryu-manager --config-file /etc/ryu/ryu.conf ryu.app.simple_switch_13 ryu.app.ofctl_rest ryu.app.rest_qos ryu.app.rest_topology ryu.app.rest_conf_switch
```

This will create a screen session and run the controller. Please make sure the following secgroup ports are open for this VM and all other VMs:

| IP Protocol   | From Port  | To Port  |  Description     |
| ------------- |:----------:|:--------:| ----------------:|
| udp           |     8479   |    8479  |   OVS VXLAN      |
| udp           |     4789   |    4789  |   Docker VXLAN   |
| tcp           |     6633   |    6633  |   OpenFlow       |

In order to work with Elascale Autoscaler (for autonomic bandwidth control), you need to copy the switches.py file (in this repo) to /usr/local/lib/python2.7/dist-packages/ryu/topology/ and restart the controller. This allows fetching Switches' IP addresses for topology information (required for autoscaling).

## Execute Installation Script

Get the instalation script:

```wget https://raw.githubusercontent.com/RajsimmanRavi/vino_elascale/master/overlay-elascale-init```

Give execution privilege for the script: ```chmod 755 overlay-elascale-init```

Execute the script: ```./overlay-elascale-init```

The script does the following:
* Fetches appropriate public key and adds to keypair-list (if not added already)
* Adds appropriate secgroup-rules 
* Fetches the scripts from GitHub
* Modifies configuration script (config2.py) to add your SAVI authentication and environment information 
* Modifies topology file (topology2.py) to add the current region 

### Change CONTROLLER Address ###
Modify ```contr_addr``` variable in topology2.py to the OpenFlow controller VM's IP address (Port 6633 can stay the same)

Execute the ViNO script on the specified folder: ```${SCRIPTS_DIR}/./vino``` (fill in the variable)

The script does the following (in a nutshell):
* Boots up all the VMs (as defined by your topology)
* Sets up all the VXLAN interfaces for communication with OVS

Execute the ViNO script on the specified folder: ```${SCRIPTS_DIR}/./elascale_setup.py``` (fill in the variable)

The script does the following (in a nutshell):
* Sets up the Docker Swarm master (as defined by your topology)
* Adds all the other hosts as swarm workers 
* Adds role of monitor for specific host (as defined by your topology)
* Adds all the hosts as docker-machine clients

## Deploy Elascale Platform
Once the setup is complete, you can login to your swarm-master, and follow along the 'Execute Installation Script' and 'Elascale Deployment' instructions described in: https://github.com/RajsimmanRavi/Elascale_secure to deploy Elascale on ViNO platform. At the end of the procedure, if you're having this problem with docker-machine nodes: **Unable to query docker version: Cannot connect to the docker engine endpoint**, then just regenerate the certs: `sudo docker-machine regenerate-certs {hostname}`  

## Cleanup Script
In order to delete all the created VMs, you can simply call the following script: ```${SCRIPTS_DIR}/./vino_cleanup``` (fill in the variable)

## Contact

If you have any questions or comments, please email me at: rajsimmanr@savinetwork.ca
