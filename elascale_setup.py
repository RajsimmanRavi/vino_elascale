#!/usr/bin/env python

import paramiko
import time
import topology2 as topology
import config2 as config

import novaclient.v1_1.client as nclient
from novaclient import exceptions
import re

def execute_and_verify(shell, command, verify_command, keyword_search):
    ssh = shell
    while True:
        try:
            stdin, stdout, stderr = ssh.exec_command(command, timeout=25)
            # If command is docker-machine create, print
            if "docker-machine create" in command:
                print(stdout.read())
                print(stderr.read())

            stdin, stdout, stderr = ssh.exec_command(verify_command,timeout=25)
            # If command is worker trying to join, then get the output of error from verify_command, not output
            if "swarm join --token" in command:
                output = stderr.read()
            else:
                output = stdout.read()

            if keyword_search in output:
                # join --token command spits error (which is good), but may startle user, hence, don't print
                # Don't print 'docker node inspect' output (too long)
                if "Error" not in output or "docker node inspect" in verify_command:
                    print output
                print "successfully executed (above) command"
                break
            else:
                print "Not executed yet. Trying again..."
                time.sleep(5)
        except Exception as e:
            print e
            print "Unable to execute command. Trying again...."
            time.sleep(5)
    # If command is manager trying to get token, return the output
    if "join-token" or "docker node ls" in command:
        return output.strip()

def init_docker_machines(ssh, nova, master_key):

    try:
        ftp_client=ssh.open_sftp()
        ftp_client.put(config.private_key_file,master_key)
        ftp_client.close()
    except Exception as e:
        print e
        print "Unable to send key to master node...You may need to do this manually for Docker-machine to work properly! Exiting..."
    else:
        workers = get_swarm_workers(nova)
        for worker in workers:
            hostname = worker.split(":")[0]
            ip = worker.split(":")[1]
            command = "sudo docker-machine create --driver generic --generic-ip-address="+ip+" --generic-ssh-user="+config.vm_user_name+" --generic-ssh-key="+master_key+" "+hostname
            verify_command = "sudo docker-machine ls | grep -v Timeout"
            keyword_search = hostname
            execute_and_verify(ssh, command, verify_command, keyword_search)

def init_swarm_master(ssh, hostname):
    command = "sudo docker swarm init"
    verify_command = "sudo docker node ls"
    keyword_search = hostname
    execute_and_verify(ssh, command, verify_command, keyword_search)

    command = "sudo docker node update --label-add role=master "+hostname
    verify_command = "sudo docker node inspect "+hostname
    keyword_search = "master"
    execute_and_verify(ssh, command, verify_command, keyword_search)

    command = "sudo docker swarm join-token worker | grep -v 'add' | tr -d '\' 2> /dev/null"
    verify_command = command
    keyword_search = "--token"
    token = execute_and_verify(ssh, command, verify_command, keyword_search)


    # Return token
    return token

def get_specific_swarm_node(nova, hostname):
    for s in sorted(nova.servers.list()):
        if hostname in (s.name).lower():
            vm_net , vm_ip = s.networks.popitem()
            vm_ip = vm_ip[0] # Just care about the first IP (most likely private 10.x.x.x)
            hostname = (s.name).lower()
    return hostname, vm_ip

def get_swarm_workers(nova):
    search_hosts = '.*h[0-9]' # Get all hosts, but remove master later
    workers = []
    for s in sorted(nova.servers.list()):
        if config.instance_prefix in s.name and re.search(pattern=search_hosts, string=s.name) and topology.swarm_master not in (s.name).lower():
            vm_net , vm_ip = s.networks.popitem()
            vm_ip = vm_ip[0] # Just care about the first IP (most likely private 10.x.x.x)

            workers.append((s.name).lower()+":"+vm_ip)

    return workers

def bring_swarm_hosts_up(nova, downed_hosts):

    for host in downed_hosts:
        vm_name, vm_ip = get_specific_swarm_node(nova, host)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(vm_ip, username=config.vm_user_name, key_filename=config.private_key_file)
        command = "sudo service docker restart"
        verify_command = "sudo docker ps"
        keyword_search = "CONTAINER ID"
        execute_and_verify(ssh, command, verify_command, keyword_search)

        ssh.close()

        print ("Brought node %s UP" % vm_name)
        time.sleep(3)

def get_downed_swarm_hosts(master_ssh):
    downed_hosts = []
    # check for any down nodes
    command = "sudo docker node ls | grep 'Down\|STATUS'"
    verify_command = command
    keyword_search = "MANAGER STATUS"
    output = execute_and_verify(master_ssh, command, verify_command, keyword_search)
    # Split it into multiple lines
    output = output.split("\n")
    for line in output:
        if "Down" in line:
            downed_hosts.append(line.split()[1])

    return downed_hosts



def config_hosts_elascale():

    nova = nclient.Client(config.username, config.password, config.tenant_name, config.auth_url, region_name=config.region_name, no_cache=True)

    master_hostname = config.instance_prefix+topology.swarm_master
    swarm_hostname, swarm_node_ip = get_specific_swarm_node(nova, master_hostname)
    print("SWARM_MASTER_IP: %s" %swarm_node_ip)
    master_ssh = paramiko.SSHClient()
    master_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    master_ssh.connect(swarm_node_ip, username=config.vm_user_name, key_filename=config.private_key_file)
    print "Successfully connected to Swarm Master!"


    # Initialize swarm master and get the token to add other hosts as workers
    join_token = init_swarm_master(master_ssh, swarm_hostname)

    workers = get_swarm_workers(nova)

    # Add workers to swarm cluster
    for worker in workers:
        hostname = worker.split(":")[0]
        ip = worker.split(":")[1]

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=config.vm_user_name, key_filename=config.private_key_file)
        print "Successfully connected to %s" %hostname

        command = "sudo "+join_token
        verify_command = command
        keyword_search = "This node is already part of a swarm"
        execute_and_verify(ssh, command, verify_command, keyword_search)
        print "Closing SSH connection for %s" %hostname
        ssh.close()

    # Need to update role of monitor host
    # Get the host responsible for monitor (need to update node role)
    monitor_host = config.instance_prefix+topology.swarm_monitor
    command = "sudo docker node update --label-add role=monitor "+monitor_host
    verify_command = "sudo docker node inspect "+monitor_host
    keyword_search = "monitor"
    execute_and_verify(master_ssh, command, verify_command, keyword_search)
    print("Successfully labeled Monitor Node")


    # Check for any downed hosts and bring them back up
    downed_hosts = get_downed_swarm_hosts(master_ssh)
    if downed_hosts:
        bring_swarm_hosts_up(nova, downed_hosts)


    print("Setting up Docker-machine clients")
    time.sleep(3)
    # Location where you copy private_key to Swarm manager (needed for Docker-machine to access other hosts)
    master_key= "/home/"+config.vm_user_name+"/.ssh/master_id_rsa"

    # Join the hosts to the docker-machine client
    init_docker_machines(master_ssh, nova, master_key)

    print("Successfully Joined hosts to Docker-machine client")
    print("Closing SSH connection for Swarm Master")

    master_ssh.close()

if __name__=="__main__":
    config_hosts_elascale()


