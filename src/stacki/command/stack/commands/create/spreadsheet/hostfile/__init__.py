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
import sys
import string
import stack.api as api
import csv
import io as cStringIO
import stack.commands
from stack.exception import *
from salt.client.ssh.client import SSHClient
from ipaddress import IPv4Address,IPv4Network,\
	IPv6Address,IPv6Network,ip_network,ip_address
from operator import itemgetter, attrgetter, methodcaller

class command(stack.commands.create.command,
	stack.commands.HostArgumentProcessor):
	MustBeRoot = 0


class Command(command):
	"""
	Create a hostfile spreadsheet for brownfield. Outputs a CSV
	file to /root/discovered_hosts.csv by default. This file
	can be used by "stack load hostfile" to preseed the database.

	<param type='string' name='hosts'>
	Comma delimited host name(s) or individual ips of machines to
	scan. This assumes host names are resolvable. If not,
	use the "network" parameter or use IPs.
	</param>
	
	<param type='string' name='network'>
	Use network/cidr notation (e.g., '192.168.1.0/24') to designate
	networks.
	</param>

	<param type='string' name='network_name'>
	The name of the network these hosts will belong to.
	Must be contained in the networks table when you import
	the spreadsheet. (e.g. 'private') Defaults to 'private.'
	</param>

	<param type='boolean' name='ipmi'>
	Scan for an ipmi network and get the IPMI interface information.
	Scans port 623. If you have changed IPMI
	
	Use: "Y/yes" "N/no" "T/true" or "F/false"
	</param>

	<param type='string' name='sshport'>
	We can scan for an ssh network and get the hosts. We assume port 22.
	If ssh is running on a different port, do that here.
	</param>

	<param type='string' name='ipfile'>
	Supply a file name of IPS or hostnames to search. One IP or hostname
	to a line. Hostnames must resolve. Don't put networks in this file.
	</param>

	<param type='string' name='rosterfile'>
	Use a different file for the salt roster file that drives the
	host information collection. Don't change this if you don't know
	what you are doing. Default: /etc/salt/roster
	</param>
	
	<param type='string' name='appliance'>
	The appliance you're going to name this. Add the appliance before
	loading the hostfile. Default: "backend"
	</param>

	<param type='string' name='rack'>
	Starting number to count from. Defaults: 0.
	</param>

	<param type='string' name='rank'>
	Starting number to count from. Defaults: 0.
	</param>

	<param type='boolean' name='chatty'>
	Turn on/off progress messages. Default: True.
	</param>

	<param type='string' name='output-file'>
	Output the CSV to file. Default: /root/discovered_hosts.csv.
	</param>

	<param type='string' name='interface'>
	Obviate the discovered interface.
	</param>
	
	<param type='string' name='output-headers'>
	Do/don't output CSV file headers. Usefull if scanning
	multiple subnets. Default: True
	</param>

	<example cmd="create spreadsheet hostfile">
	Basic:
	stack create spreadsheet hostfile network=10.3.255.0/24
	Intermediate:
	stack create spreadsheet hostfile network=10.3.255.0/24
	network_name=public
	Advanced:
	stack create spreadsheet hostfile network=10.3.255.0/24 rack=10 rank=3
	network_name=public appliance=edge
	</example>

	"""

	def config_bonding(self,name,ifaces,host,bond,ip,network_name,app,idx):
		global rck,rnk
#		data = self.get_grains()
		k = bond
#		print(data)
		# get real macs for bonded interfaces
		bondedmacs = self.get_real_macs(host,bond)
		interface = k
		bondmac = ifaces[k]
		bondednics = []
		name = name
		rows = []
		for mk,mv in ifaces.iteritems():
			if mv == ifaces[k] and mk != k:
				bondednics.append(mk)
		mac = None
		# Now get proc/net/bonding options here
		options = self.get_bonding_opts(host,bond)
		network = network_name
		mac = None
		channel = None
		if idx > 0:
			default = None
			rack = None
			rank = None
			appliance = None
		else:
			default = 'True'
			rack = rck
			rank = rnk
			rnk += 1
			appliance = app
		if len(interface.split('.')) == 2:
			vlan = interface.split('.')[1]	
		else:
			vlan = None
		row = [ name, interface_hostname,
			default, appliance, rack,
			rank, ip, mac, interface,
			network, channel, options,
			vlan, installaction, osaction,
			groups, box, comment ]
		rows.append(row)
		del ifaces[k]

		for n in bondednics:
			name = name
			mac = bondedmacs[n]
			interface = n
			options = None
			network = None
			default = None
			rack = None
			rank = None
			appliance = None
			channel = bond
			ip = None

			if len(interface.split('.')) == 2:
				vlan = interface.split([1])

			row = [ name, interface_hostname,
				default, appliance, rack,
				rank, ip, mac, interface,
				network, channel, options,
				vlan, installaction, osaction,
				groups, box, comment ]

			rows.append(row)
			del ifaces[n]

		return ifaces, rows

	def get_bonding_opts(self,host,bond):
		# maybe tell it where the python lib is?
		client = SSHClient()
		# can't do hosts without a roster file, gotta build that
		# or figure something out
		mcmd = ["grep BONDING_OPTS \
			/etc/sysconfig/network-scripts/ifcfg-%s" % bond]
		output = client.cmd(tgt=host,fun='cmd.run', arg=mcmd)
		olist = sorted(output.keys())
		for o in olist:
			if output[o]['retcode'] == 0:
				out = output[o]['return'].lower()
		return out

	def get_real_macs(self,host,bond):
		# maybe tell it where the python lib is?
		client = SSHClient()
		# can't do hosts without a roster file, gotta build that
		# or figure something out
		mcmd = ["cat /proc/net/bonding/%s | egrep 'addr|Slave I'"
			% bond]

		output = client.cmd(tgt=host,fun='cmd.run', arg=mcmd)
		olist = sorted(output.keys())
		realnic = {}
		for o in olist:
			if output[o]['retcode'] == 0:
				out = output[o]['return'].split('\n')
				l = [x.split()[-1] for x in out ]
				realmacs = dict(zip(*[iter(l)]*2))
		return realmacs

	def get_grains(self):
		client = SSHClient()
		output = client.cmd(tgt='*',fun='grains.item host \
				hwaddr_interfaces ip4_interfaces')
		olist = sorted(output.keys())
		data = {}
		for o in olist:
			if output[o]['retcode'] == 0:
				out =  output[o]['return']
				data[out['host']] = output[o]['return']
		return data

	def get_network_name(self,ip):
		nets = api.Call('list network')
		nlist = []	
		ndict = {}
		for n in nets:
			mask,addr = n['mask'],n['address']
			hostnet = IPv4Network(u'%s/%s' % (addr,mask))
			if ip_address(u'%s' % ip) in ip_network(hostnet):
				nlist.append(n['network'])
	# compare two nets
		clist=[]
		if len(nlist) > 1:
			for j in nets:
				if j['network'] in nlist:
					mask,addr = j['mask'],j['address']
					clist.append(IPv4Network(u'%s/%s'
						% (addr,mask)))
			if ip_network(clist[0]).compare_networks(ip_network
					(clist[1])) == -1:
				return nlist[1]
		else:
			return nlist[0]

	def doHosts(self,hosts,app,network_name):
		data = self.get_grains()
		rows = []
		for d in sorted(data.keys()):
			ifaces = data[d]['hwaddr_interfaces']
			ips = data[d]['ip4_interfaces']
			hs = data[d]['host']
			name = hs
			# check for bonding, if bonded, process, and remove
			# pairs this is some truly sneaky-ass shit. If
			# there's bonding, the ifaces gets rewritten by
			# deleting the bond interface(s) and any interfaces
			# in the bond
			ikeys = ifaces.keys()
			bonds = [x for x in ikeys if "bond" in x]
			for b in bonds:
				idx = bonds.index(b)
				network_name = self.get_network_name(ips[b][0])
				ifaces,row = self.config_bonding(name,ifaces,
							name,b,ips[b][0],
							network_name, app, idx)
				for i in row:
					rows.append(i)

			for k,v in sorted(ifaces.items()):
				interface = k
				mac = v
				vlan = None
				if k == 'NULL':
					interface = 'em1'

				if not k == 'lo' and k.find('bond') == -1:
					if len(ips[k]) == 0:
						ip = None
						network = None
						default = None
						appliance = None
						rack = None
						rank = None
					else:
						ip = ips[k][0]
						# fuck you fucking 80 char
						# count standard
						network = \
						self.get_network_name(ip)

						if network == 'private':
							default = 'True'
							global rck,rnk
							rack = rck
							rank = rnk
							appliance = app
							rnk += 1
						else:
							default = ''
							rack = ''
							rank = ''
							appliance = ''
							
						mac = v
					if len(interface.split('.')) == 2:
						vlan = interface.split('.')[1]
					row = [ name, interface_hostname,
							default, appliance,
							rack, rank, ip, mac,
							interface, network,
							channel, options, vlan,
							installaction, osaction,
							groups, box, comment ]

					rows.append(row)
		
		return rows

	def print_debug(self,chatty,contents):
		if chatty == True:
			print(contents)
		else:
			None

	def run(self, params, args):
		# make these global so you don't have to pass
		# as options to the functions.
		# This is safe as global variable is local to the
		# module, so don't get your panties in a bunch.
		global ip, mac, default, interface, network, channel, \
				options, vlan, interface_hostname, \
				rck, rnk, chatty, interface, \
				installaction, osaction, groups, \
				box, comment
	
		(hosts, network, network_name, ipmi, sshport, ipfile,
		rosterfile, appliance, rack, rank, interface, chatty_flag,
			ofile, headers, installaction, osaction, groups,
			box, comment) = self.fillParams([
			('hosts', None),
			('network', None),
			('network_name', 'private'),
			('ipmi', False),
			('sshport', 22),
			('ipfile', None),
			('rosterfile', '/etc/salt/roster'),
			('appliance', 'backend'),
			('rack', 0),
			('rank', 0),
			('interface', None),
			('chatty', 'True'),
			('output-file', '/root/discovered_hosts.csv'),
			('output-headers', True),
			('installaction', 'default'),
			('osaction', 'default'),
			('group', ''),
			('box', 'default'),
			('comment', '')
			])
		#print(interface)
		# Turn on/off progress messages.
		chatty = stack.bool.str2bool(chatty_flag)

		# add counters for rack and rank
		rck = int(rack)
		rnk = int(rank)
		# Stuff the functions change.
		ip = mac = default = channel = options \
			= vlan = interface_hostname = None
		
		# The implementation does the following:
		# 1. nmaps the SSH port (22) on the given network to see
		# if we can actually connect.
		# 2. If we can connect, put the host in /etc/hosts and
		# /etc/salt/roster

		if stack.bool.str2bool(ipmi) == False:

			self.runImplementation('discover', \
			(hosts, network, ipmi, sshport, ipfile,
				rosterfile,chatty,interface))

			self.print_debug(chatty,"\nCreating CSV output.\n")
		else:
			msg = "IPMI network scanning is not implemented yet."
			raise CommandError(self, msg)
			self.runImplementation('discover_ipmi',
				(hosts, network, ipmi))
			print_debug("\nCreating CSV output.\n")
		# this all depends on the roster containing hosts. If it doesn't
		# nothing else will work, so bail, be helpful.

		if os.stat(rosterfile).st_size == 0:
			raise CommandError(self,"No hosts found or accessible.")

		header = ['NAME', 'INTERFACE HOSTNAME', 'DEFAULT', 'APPLIANCE',
			'RACK', 'RANK', 'IP', 'MAC', 'INTERFACE', 'NETWORK',
			'CHANNEL', 'OPTIONS', 'VLAN', 'INSTALLACTION', 'OSACTION',
			'GROUPS', 'BOX', 'COMMENT']
#		installaction, osaction, groups, box, comment
		# CSV writer requires fileIO.
		# Setup string IO processing
		csv_f = cStringIO.StringIO()
		csv_w = csv.writer(csv_f)
		if headers == True:
			csv_w.writerow(header)
		# collect all the bluidy rows
		rows = self.doHosts(hosts,appliance,network_name)

		# sort the damn thing while we are at it.
		for r in sorted(rows,key=itemgetter(0)):
			csv_w.writerow(r)

		# Get string from StringIO object
		s = csv_f.getvalue().strip()
		csv_f.close()
		if chatty == True:
			self.beginOutput()
			self.addOutput('',s)
			self.endOutput()

		self.print_debug(chatty,"Writing discovered hosts to %s.\n"
					% ofile)
		f = open(ofile,'w')
		f.write(s)
		f.close()
		# clean up /etc/hosts which we have been manipulating
		self.print_debug(chatty,"Cleaning up.\n")
		self.command('sync.config')	
