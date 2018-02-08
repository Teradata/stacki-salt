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

import stack.attr
import stack.commands

class Command(stack.commands.Command,
	stack.commands.HostArgumentProcessor):
	"""
	Report salt configuration for a host
	<arg name="host" type="string">
	Hostname
	</arg>
	"""
	def run(self, params, args):

		self.beginOutput()

		for host in self.getHostnames(args):
			
			for role in [ 'master', 'minion' ]:
				self.configure(host, role)

		self.endOutput(padChar='', trimOwner=1)



	def configure(self, host, role):

		# Use attributes to identify the master, rather than
		# hardcode to the Frontend appliance(s).  Further
		# all parameters other than id come directly from
		# attributes.

		run = self.getHostAttr(host, 'salt.%s' % role)
		if self.str2bool(run):

		# Salt configuration

			self.addOutput(host, '<stack:file stack:name="/etc/salt/%s" stack:perms="0644">' % role)
			if role == 'minion':
				self.addOutput(host, 'id: %s' % host)

			for row in self.call('list.host.attr',
					[ host,  'attr=salt.%s.*' % role]):

				a = row['attr'].split('.')[-1]
				v = row['value']
				self.addOutput(host, '%s: %s' % (a, v))

			self.addOutput(host, '</stack:file>')
