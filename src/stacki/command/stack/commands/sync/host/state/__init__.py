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

import os
import sys
import time
import salt.client
import stack.commands
from stack.exception import *

	
class Command(stack.commands.sync.host.command):
	"""
	Run the highstate for each specified host.

	<arg optional='1' type='string' name='host' repeat='1'>
	Zero, one or more host names. If no host names are supplied, the command
	is run on all 'managed' hosts. 
	</arg>

       	<param type='bool' name='test' optional='1'>
        If set to TRUE perform a dryrun and only list out the current state of
        the specified host(s).  The default is FALSE.
        </param>

        <param type='string' name='name' optional='1'>
        Used in conjuction with the FUNCTION parameter run only one state
        rather than the entire Salt highstate.
        </param>

        <param type='string' name='function' optional='1'>
        Used in conjuction with the NAME parameter run only one state
        rather than the entire Salt highstate.
        </param>

        <param type='string' name='sls' optional='1'>
        Used to specify a unique .sls file to be used, rather than the
        entire salt file tree.
        </param>

	<example cmd='sync host state backend-0-0'>
	Sets backend-0-0 to the salt highstate.
	</example>

        <example cmd='sync host state backend-0-0 test=true'>
	Dry run of highstate for backend-0-0.  This is usefull to inspect the
        currect state (and what is not in sync), and to see the full list of
        names and functions in the highstate.
	</example>

	<example cmd='sync host state backend-0-0 name=user-root function=user.present'>
        Run the named state user-root function user.present on backend-0-0.  If the
        Attribute sync.root is defined as true this will set the root account password
        to the crypted valued stored in the attribute Kickstart_PrivateRootPassword.
	</example>
	"""


	def run(self, params, args):
		hosts = self.getHostnames(args, managed_only=True)
                
		(function, name, sls, test, timeout) = self.fillParams([
                    ('function', None),
                    ('name', None),
                    ('sls', None),
                    ('test', None),
                    ('timeout', 30) ])
                 
                test = self.str2bool(test)
                
		self.beginOutput()

		client = salt.client.LocalClient()
                if sls:
			job = client.cmd_async(hosts,
					       fun='state.sls',
					       arg=[ sls ],
					       expr_form='list')
		elif function or name:
                        if not (function and name):
                                raise ParamRequired(self, ('function', 'name'))
			job = client.cmd_async(hosts,
					       fun='state.single',
					       arg=[ function, 'name=%s' % name, 'test=%s' % test ],
					       expr_form='list')
		else:
			job = client.cmd_async(hosts,
					       fun='state.highstate',
					       arg=['test=%s' % test],
					       expr_form='list')

		if job:
			while timeout:
				result = client.get_cache_returns(job)
				if result and len(result.keys()) == len(hosts):
					break
				time.sleep(1)
				timeout -= 1


                for host in hosts:
                        if result.has_key(host):
				if result[host].has_key('ret'):
					ret = result[host]['ret']
					if ret:
						for key in ret.keys():
							list     = key.split('_|-')
							function = '%s.%s' % (list[0], list[3])
							id       = list[1]
							name = None
							if ret[key].has_key('name'):
								name = ret[key]['name']
							self.addOutput(host, [
									name,
									function,
									ret[key]['result'],
									ret[key]['comment'] ])
			else:
				self.addOutput(host, [None, None, False, 'Command not run'])
		
		self.endOutput(header=['host', 'name', 'function', 'result', 'comment'], trimOwner=False)


