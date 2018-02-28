#!/usr/bin/env python

# vim: tabstop=4 shiftwidth=4 softtabstop=4 expandtab

#  ----------------------- topology dict ------------------
"""
The Keys of the topology dictionary can only be switches

The values represent the connection to/from that switch. To create a link to another switch,
just write the switch#. To represent a connection to a host, write down a tuple containing the
host# and internal port address. An optional field for the host is the bridge name at tuple index 2.
The other two fields are mandatory

topology['switch number'] = [ ( 'host number' , 'internal port addr' , 'bridge_name'), 'switch' ]
"""

#Address and port pair of controller, e.g. Pox, Ryu, Floodlight
contr_addr = '10.2.1.23:6633'

switches = {}
switches["sw1"] = {'contr_addr': contr_addr, 'region': 'CORE', 'flavor': 'm1.small', 'bridge_name': 'sw1_br', 'int_ip': ('p1', '192.168.200.18')}
switches["sw2"] = {'contr_addr': contr_addr, 'region': 'CORE', 'flavor': 'm1.small'}
switches["sw3"] = {'contr_addr': contr_addr, 'region': 'CORE', 'flavor': 'm1.small', 'bridge_name': 'sw3_br'}

hosts = {}
hosts["h1"] = {'region': 'CORE', 'flavor': 'm1.medium'}
hosts["h2"] = {'region': 'CORE', 'flavor': 'm1.medium'}
hosts["h3"] = {'region': 'CORE', 'flavor': 'm1.medium'}
hosts["h4"] = {'region': 'CORE', 'flavor': 'm1.medium'}

# Do not connect two Vxlans to the same switch pairings while running a simple switch controller
topology = {}
topology["sw1"] = [('h1', '192.168.200.10', 'h1_br'), ('h4', '192.168.200.13')]
topology["sw2"] = ['sw1', ('h2', '192.168.200.11')]
topology["sw3"] = ['sw2', ('h3','192.168.200.12')]

# Specify which host to be Swarm master and which host to monitor the platform (where Elascale will be deployed)
swarm_master = "h1"
swarm_monitor = "h4"
