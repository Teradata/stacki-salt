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

import string
from stack.api import get
import csv
import cStringIO
import stack.commands
from stack.exception import *
from salt.client.ssh.client import SSHClient
import ipaddress, struct, socket
import subprocess
import sys
import ipaddress 
import struct
import socket
import stack.bool


class command(stack.commands.discover.command,
	stack.commands.HostArgumentProcessor):
	MustBeRoot = 0


class Command(command):
	"""
	write hosts.local and sync it.
	write a roster file
	assumes you have ssh access and know
	the keys

	<param type='string' name='hosts'>
	Host name(s) or individual ips of machines to scan. This 
	assumes they are resolvable. If not, use "network" parameter.
	
	IPs and host names follow the standard nmap pattern matching
	criteria. (e.g. 192.168.1.31-34 and NOT 192.168.1.3[1-4])

	If hosts are in site DNS, the use of host names is acceptable.
	</param>
	
	<param type='string' name='network'>
	The name of the network to detect. (e.g., 'private')
	Or use at the network/cidr notation (e.g., '192.168.1.0/24')
	</param>

	<param type='boolean' name='ipmi'>
	We can scan for an ipmi network and get the hosts. Scans
	a different port.
	</param>
	
	give a network name and we'll add it.

	"""

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
		        for row in self.call('list.network'):
       		        	if network == row['network']:
					net = row['address']
					cidr = row['mask']
		try:	
			n = ipaddress.IPv4Network(u'%s/%s' % (net,cidr))
		except ValueError, e:
			msg = '%s. Maybe fix that?' % e
			raise CommandError(self,msg)

		x = str(n)
		if int(x.split('/')[-1]) <= 16:
			msg = 'That\'s %s addresses. ' % n.num_addresses
			msg += 'No way I''m scanning that. Pick a '
			msg += ' smaller subnet.'
			raise CommandError(self,msg)
		# if cidr == 16 or less, warn about the size of the scan
		return n

	def generate_roster(self):
		pass

	def scan_network(self,scanitems,port):
		cmd = 'nmap -nR -T5 -p %s %s' % (port,' '.join(scanitems))
		p = subprocess.Popen(cmd, 
		stdout=subprocess.PIPE, 
		stderr=subprocess.PIPE, 
		shell=True)
		(o, e) = p.communicate()

		if p.returncode == 0:
			stuff = o
		if len(e) > 0:
			msg = "Host specification is incorrect."
			raise CommandError(self,e+msg)

		scanres = stuff.lower().splitlines()[2:-1]
		x = filter(None,[ i.split() for i in scanres ])
		ips = []
		for i in x:
			if i[0] == 'nmap':
				ips.append(i[-1])
		return ips
	
	def create_initial_roster(self,ips):
		f = open('/etc/salt/roster','w')			
		for i in ips:
			f.write("%s: %s\n" % (i,i))
		f.close()

	def create_host_files(self):
		client = SSHClient()
		try:
			output = client.cmd(tgt='*',
				fun='grains.item fqdn_ip4 fqdn host')
		except:
			raise CommandError(self,"Host target is incorrect.")

		f = open('/etc/salt/roster','w')
		h = open('/etc/hosts','a')
		for o in output:
			if output[o]['retcode'] == 0:
				name = output[o]['return']['host']
				ip = output[o]['return']['fqdn_ip4'][0]
				fqdn = output[o]['return']['fqdn']
				f.write("%s: %s\n" % (name,ip))
				h.write("%s %s %s\n" % (ip,fqdn,name))
			else:
				msg = "Unable to access %s. " % o
				msg += " via ssh. It will not be included."
				print msg

		f.close()
		h.close()
	  	# might need to remove dupes here	

	def run(self, params, args):
                (hosts, network, ipmi) = self.fillParams([
                        ('hosts', None),
                        ('network', None),
                        ('ipmi', False)
                        ])
		scanitems = []
		if hosts == 'None' or network == 'None':
			msg = 'A "host" or "network" parameter is required.'
			raise CommandError(self,msg)

		if hosts:
			scanitems.append(hosts) 

		if network:
			# check that it's valid
			nets = network.split(',')
			for net in nets:
				validnet = self.check_network(net)
				if validnet:
					scanitems.append('%s' % validnet)

		if self.str2bool(ipmi) == True:
			port = 623	
			# run ipmi implementation here?
			print "run ipmi implementation here"
		else:
			port = 22
       			s = self.scan_network(scanitems,port)
			self.create_initial_roster(s)
			self.create_host_files()
