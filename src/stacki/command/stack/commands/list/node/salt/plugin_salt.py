# @copyright@
# Copyright (c) 2006 - 2017 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

from pprint import pformat
import stack.commands
import os


class Plugin(stack.commands.Plugin):
	"Include compiled salt templates into profile"

	def provides(self):
		return 'salt'

	def run(self, attrs):
		try:
			fin = open(os.path.join(os.sep, 'export', 
				'stack', 'salt', 
				'compiled', 
				attrs['hostname'], 
				'kickstart.xml'), 'r')
		except:
			fin = None

		if fin:
			self.owner.addText('<stack:script stack:stage="install-post">\n')
			for line in fin.readlines():
				self.owner.addText(line)
			self.owner.addText('</stack:script>\n')
