# @SI_Copyright@
#                               stacki.com
#                                  v4.0
# 
#      Copyright (c) 2006 - 2017 StackIQ Inc. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#  
# 2. Redistributions in binary form must reproduce the above copyright
# notice unmodified and in its entirety, this list of conditions and the
# following disclaimer in the documentation and/or other materials provided 
# with the distribution.
#  
# 3. All advertising and press materials, printed or electronic, mentioning
# features or use of this software must display the following acknowledgement: 
# 
# 	 "This product includes software developed by StackIQ" 
#  
# 4. Except as permitted for the purposes of acknowledgment in paragraph 3,
# neither the name or logo of this software nor the names of its
# authors may be used to endorse or promote products derived from this
# software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY STACKIQ AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL STACKIQ OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# @SI_Copyright@

from __future__ import print_function
import os
import string
from stack.api import get
import csv
import cStringIO
import stack.commands
from stack.exception import *
from salt.client.ssh.client import SSHClient
from ipaddress import IPv4Address,IPv4Network,\
	IPv6Address,IPv6Network,ip_network
import subprocess
import sys
import ipaddress 
import struct
import socket
import stack.bool
import logging
import stack.util
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import arping,conf,srp,Ether,ARP,sr,IP,TCP 
from datetime import datetime, date, time

class Implementation(stack.commands.Implementation):

	def check_nets(self,network):
		a = {}
		iface = None
		gnetwork = IPv4Network(u'%s' % (network))
		ifaces = self.owner.call('list.host.interface', ['a:frontend'])	

		for i in ifaces:
			a[i['network']] = i['interface']

		nets = self.owner.call('list.network')	
		for n in nets:
			if n['network'] in a.keys():
				mask,addr = n['mask'],n['address']
				hostnet = IPv4Network(u'%s/%s' % (addr,mask))
				if (ip_network(hostnet).\
					overlaps(ip_network(gnetwork))) == True:
						iface = (a[n['network']])
		return iface

	def is_in_network(self,host,network):
		iface = None
		try:
			IPv4Address(host)
		except:
			msg = "%s is either not an ip or " % host
			msg += "cannot be resolved.\n"
			msg += "Either fix your DNS or use ips.\n"
			raise CommandError(self,msg)

		if IPv4Address(host) in IPv4Network(network):
			iface = self.check_nets(network)
			return iface
		
	def check_host_net(self,hosts):
                subnets = self.owner.call('list.network')
		a = {}
		h = []
		for host in hosts:
			for sub in subnets:
				addr = sub['address']
				mask = sub['mask']
				cidr = IPv4Network._make_netmask\
					(u'%s' % mask)[1]
				network = IPv4Network(u'%s/%s' % \
						(addr,cidr),strict=False)
				iface = self.is_in_network(u'%s' % host,network)
				if iface != None:
					h.append(host)
					a[iface] = h
		if len(a.keys()) > 1:
			msg = "Don't scan hosts on multiple networks.\n"
			msg += "Provide hosts/ips on the same network."

			raise CommandError(self,msg)
		else:
			return a.keys()[0]

	def check_network(self,network):
		# lookup network in table
		if network.find('/') != -1:
			try:
				net,cidr = network.split('/')

			except UnboundLocalError:
				msg = "No network given."
				raise CommandError(self,msg)

			except ValueError:
				msg = "No cidr given."
				raise CommandError(self,msg)

		else:
			# assume you got a network name
			networks = []
		        for row in self.owner.call('list.network'):
       		        	if network == row['network']:
					net = row['address']
					cidr = row['mask']
		try:	
			n = IPv4Network(u'%s/%s' % (net,cidr))
		except ValueError, e:
			msg = '%s. Maybe fix that?' % e
			raise CommandError(self,msg)

		return n

	def create_initial_roster(self,ips,rosterfile):
		f = open(rosterfile,'w')			
		for i in ips:
			f.write("%s: %s\n" % (i,i))
		f.close()

	def cleanup(self,rosterfile):
		if os.path.isfile(rosterfile) and \
			os.path.getsize(rosterfile) > 0:
			self.owner.command('sync.config')	

	def isfile(self,afile):
		if os.path.isfile(afile) and \
			os.path.getsize(afile) > 0:
			return True
		else:
			return False
	def create_host_files(self):
		client = SSHClient()
		roster_exists = self.isfile('/etc/salt/roster')	
		if roster_exists == True:
			output = client.cmd(tgt='*',
				fun='grains.item fqdn_ip4 fqdn host')
		else:	
			raise CommandError(self,"Host target is incorrect.")

		no_ssh = []
		ssh = {}
		f = open('/etc/salt/roster','w')
		h = open('/etc/hosts','a')
		for o in output:
			if output[o]['retcode'] == 0:
				name = output[o]['return']['host']
				ip = output[o]['return']['fqdn_ip4'][0]
				fqdn = output[o]['return']['fqdn']
				ssh[o] = { 'ip': ip, 'name': name, \
						'fqdn': fqdn }
			else:
				no_ssh.append(o) 

		if len(no_ssh) > 0:
			msg = "Unable to access %s " % no_ssh
			msg += "via ssh. They/It will not be included.\n"
			msg += "Check the key for those hosts if this is "
			msg += "unexpected."
			print(msg)

		if len(ssh) > 0:
			for k,v in ssh.iteritems():
				name = ssh[k]['name']
				ip = ssh[k]['ip']
				fqdn = ssh[k]['fqdn']
				f.write("%s: %s\n" % (name,ip))
				h.write("%s %s %s\n" % (ip,fqdn,name))

		f.close()
		h.close()

	def get_ips(self,network,port,iface,chatty):
		self.owner.print_debug(chatty,"Scanning %s on interface %s.\n" % \
			(str(network).strip('[]'),iface))
		conf.verb = 0
		conf.iface = iface
		ans,unans=srp(Ether(dst="ff:ff:ff:ff:ff:ff")/\
				ARP(pdst=network),timeout=2)
		ips = [ r.psrc for s,r in ans ]
		if len(ips) == 0:
			msg = "No ips found. "
			msg += "Are you sure you have access to that network?\n"
			raise CommandError(self,msg)
		else:
			msg = "Scanning for live machines with SSH " 
			msg += "on port %s\n" % port
			self.owner.print_debug(chatty,msg)
			try:
				a,ua = sr(IP(dst=ips)/TCP(dport=[int(port)],\
						flags='S'), timeout=2)
			except:
				msg = "SSH port %s is not accepting "
				msg += "connections.\n" % port
				raise CommandError(self,msg)
			ssh_up = [ r[IP].src for s,r in a if \
					len(r[TCP].options) > 0 ]
			if len(ssh_up) == 0:
				msg = "No ips found answering to SSH "
				msg += "port %s.\n" % port
				raise CommandError(self,msg)
			else:
				sships = [ i for i in \
					set(ssh_up).intersection(set(ips)) ]
				return sorted(sships)

	def run(self, args):
                (hosts, network, ipmi, sshport, ipfile, rosterfile, chatty, interface) = args
		scanitems = []

		if hosts:
			h = hosts.split(',')
			iface = self.check_host_net(h)
			for host in h:
				scanitems.append(host)
				

		if network:
			# check that it's valid
			nets = network.split(',')
			if len(nets) > 1:
				msg = "Scan only one network at a time.\n"
				raise CommandError(self,msg)
			else:
				net = nets[0]
				validnet = self.check_network(net)
				iface = self.check_nets(net)
				if iface == None:
					msg = "Can't access %s.\n" % network
					msg += "No valid interface found." 
					raise CommandError(self, msg)
				if validnet:
					scanitems.append(str(validnet))

		if ipfile:	
			f = open(ipfile,'r')
			hosts = f.read().splitlines()
			f.close
			iface = self.check_host_net(hosts)
			for h in hosts:
		               	scanitems.append(h)

		if hosts == None and network == None and ipfile == None:
			msg = 'A "hosts" or "network" parameter is required.'
			raise CommandError(self,msg)

		if self.owner.str2bool(ipmi) == True:
			port = 623	
			# run ipmi implementation here?
			raise CommandError(self,"run ipmi implementation here")
		else:
			if interface:
				iface = interface
			try:
				s = self.get_ips(scanitems,sshport,iface,chatty)
			except OSError:
				err = "%s is not found.\n" % iface
				err += "Try starting that network."
				raise CommandError(self,err)

			if len(s) == 0:
				raise CommandError(self,"No ips found for %s" 
						% network)
			else:
				msg = "Creating %s and /etc/hosts files." \
					% rosterfile
				self.owner.print_debug(chatty,msg)
				self.create_initial_roster(s,rosterfile)
				self.create_host_files()
			
		self.cleanup('/etc/salt/roster')
