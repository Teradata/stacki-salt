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

import stack.commands
import salt.client

class Command(stack.commands.Command,
	stack.commands.HostArgumentProcessor):
	"""
	Runs a salt module on all compute nodes
	<arg type='string' name='command' optional='0'>
	The salt command that should be run.
	</arg>

	<arg type='string' name='args' optional='0'>
	The arguments to the salt command.
	</arg>

	<example cmd='run saltmod command="cmd.run"
		args="hostname"'>
	Runs the cmd.run module on all hosts, and fetch the
	hostname from all nodes.
	</example>
	"""
	# Main entry point into the program
	def run(self, params, args):
		(command, args_cmdline) = self.fillParams([
			('command', None),
			('args', None)
			])
		minions = self.getHostnames(args)

		if not command:
			self.abort('command argument is missing')

		args_list = []
		if args_cmdline:
			args_list = args_cmdline.split(' ')

		client = salt.client.LocalClient()
		op = client.cmd(minions, command,
				args_list, expr_form = 'list')

		self.beginOutput()
		for o in op:
			error_str = "\"%s\" is not available." % \
				command
			if op[o] == error_str:
				self.addOutput(o, None)
			else:
				self.addOutput(o, (op[o],))
		self.endOutput(header=['host', 'output'])
