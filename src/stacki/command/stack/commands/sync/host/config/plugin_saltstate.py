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
import re
import string
import shutil
import xml
import yaml
import shutil
from xml.sax import saxutils
from xml.sax import handler
from xml.sax import make_parser
from xml.sax._exceptions import SAXParseException
import stack.util
import stack.file
import stack.cond
import stack.profile
import stack.commands


class FileHandler(handler.ContentHandler,
			handler.DTDHandler,
			handler.EntityResolver,
			handler.ErrorHandler,
		stack.profile.AttributeHandler):

	def __init__(self, attrs):
		handler.ContentHandler.__init__(self)
		self.setAttributes(attrs)
		self.files = []
		self.curr  = {}
		self.text = ''

	def getFiles(self):
		return self.files

	def startElement(self, name, attrs):
		if name == 'file':
			path  = attrs.get('name')
			perms = attrs.get('perms')
			owner = attrs.get('owner')
			cond  = attrs.get('cond')
			watch = attrs.get('watch')
			req   = attrs.get('require')
			mode  = attrs.get('mode')

			self.text = ''
			if not path:
				return

			self.curr = {}
			self.curr['name'] = path
			self.curr['path'] = path
			if watch:
				self.curr['watch'] = watch
			if req:
				self.curr['require'] = req
			if perms:
				self.curr['perms'] = perms
			if mode:
				self.curr['mode'] = mode
			if owner:
				user  = owner
				group = None
				for sep in [ '.', ':' ]:
					if len(owner.split(sep)) == 2:
						(user, group) = owner.split(sep)
				self.curr['owner'] = owner
				self.curr['user']  = user
				if group:
					self.curr['group'] = group
			if cond:
				self.curr['cond'] = cond
		else:
			list = []
			for (k,v) in attrs.items():
				list.append(' %s="%s"' % (k,v))
			self.text += '<%s%s>' % (name, string.join(list, ','))

	def endElement(self, name):
		if name == 'file':
			self.curr['content'] = self.text
			self.files.append(self.curr)
		else:
			self.text += '</%s>' % name

	def characters(self, s):

		# If the very first character is a newline ignore it,
		# this means the firt line of the file can start on the
		# line after the file tag.

		if self.text or not s == '\n':
			self.text += s


class Plugin(stack.commands.Plugin):
	"Translates Stack Salt XML into Salt States"

	def provides(self):
		return 'saltstate'

	def writeSalt(self, host, template):

		dir = os.path.join(self.pathCompiled, host)
		if not os.path.exists(dir):
			os.makedirs(dir)
			

		# Append to the Kickstart node.xml file so during
		# Kickstart the same changes will be picked up.  This
		# protects us in case salt fails, and the machine is
		# left half configured.

		node = open(os.path.join(self.pathCompiled, 
					host, 'kickstart.xml'), 'a')
		node.write('<file')
		for key in [ 'name', 'perms', 'owner', 'mode' ]:
			if template.has_key(key):
				node.write(' %s="%s"' % (key, template[key]))
		node.write('>')
		node.write(saxutils.escape(template['content']))
		node.write('</file>\n')

		node.close()

		# Create the host specific compliled template file.
		# This is parsing the XML and expanding all the host
		# attributes.

		filename = template['path'].replace(os.sep, '_')
		fout = open(os.path.join(dir, filename), 'w')
		fout.write(template['content'])
		fout.close()

		# Append to the salt state file to register to 
		# above file.

		fout = open(os.path.join(self.pathCompiled, host, 'init.sls'),
				'a')
		fout.write('%s:\n' % template['path'])

		if template.has_key('watch'):
			fout.write('  cmd:\n')
			fout.write('    - wait\n')
			fout.write('    - watch:\n')
			fout.write('      - file: %s\n' % template['watch'])

		if template.has_key('mode'):
			fout.write('  file.append:\n')
			fout.write('    - source: salt://%s/%s\n' % (host, filename))
		else:
			fout.write('  file.managed:\n')
			fout.write('    - source: salt://%s/%s\n' % (host, filename))

		for key in [ 'user', 'group', 'perms' ]:
			if template.has_key(key):
				if key == 'perms':
					fout.write('    - mode: %s\n'  % (key, 
						template[key]))
				else:
					fout.write('    - mode: %s\n'  % (key, 
						template[key]))
		if template.has_key('require'):
			fout.write('    - require:\n')
			fout.write('      - file: %s\n' % template['require'])

		fout.write('\n')
		fout.close()
		
		# Append to the compiled/top.sls file to register to
		# host specific salt files.

		hasKey = False
		try:
			stream = file(os.path.join(self.pathCompiled, 
						'top.sls'), 'r')
			dict = yaml.load(stream)
			if dict['compiled'].has_key(host):
				hasKey = True
		except IOError:
			dict = { 'compiled': {} }
		if not hasKey:
			dict['compiled'][host] = [ host ]
			stream = file(os.path.join(self.pathCompiled, 
						'top.sls'), 'w')
			yaml.dump(dict, stream)
		

	def run(self, hosts):

		pathSource   = os.path.join(os.sep, 'export', 
						'stack', 'salt')
		self.pathCompiled = os.path.join(pathSource, 'compiled')
		attrs = {}
		for host in hosts['hosts']:
			attrs[host] = {}
			host_path = os.path.join(self.pathCompiled, host)
			if os.path.exists(host_path):
				shutil.rmtree(host_path)

		for row in self.owner.call('list.host.attr', hosts['hosts']):
			attrs[row['host']][row['attr']] = row['value']


		for host in hosts['hosts']:
			host_attrs = attrs[host]
			paths = [ os.path.join(pathSource, 'default') ]
			if 'environment' in host_attrs:
				paths.append(os.path.join(pathSource, host_attrs['environment']))
			for path in paths:
				tree = stack.file.Tree(path)
				for dir in tree.getDirs():
					for file in tree.getFiles(dir):
						if not os.path.splitext(file.getName())[1] == '.xml':
							continue
						parser  = make_parser()
						handler = FileHandler(host_attrs)
						parser.setContentHandler(handler)
						parser.feed(handler.getXMLHeader())
						parser.feed('<salt>')
						fin = open(file.getFullName(), 'r')

						# Parse as XML-ish to pickup the
						# entities that correspond to host
						# attributes.  But we assume the <file
						# ...> and </file> tags start at col 0
						# on a line by themselves.  Anything
						# between the file tags is first
						# sanitized for '<' and '&'
						# (non-entity refs only).  This keep
						# the file in XML-ish mode, and
						# prevents the need for using CDATA.
						# Node.xml files do not behave this
						# we, so while a node.xml <file>
						# section can move into this framework
						# the reverse is not true (yet).

						for line in fin.readlines():

							if line.find('<file') == 0 or \
								line.find('</file>') == 0:
								s = line
							else:
								s = ''
								for i in range(0, len(line)):
									if line[i] == '<':
										s += '&lt;'
									elif line[i] == '&':
										if not re.match('&[A-Za-z_.][A-Za-z0-9_.]*;', line[i:]):
											s += '&amp;'
										else:
											s += line[i]
									else:
										s += line[i]
							try:
								parser.feed(s)
							except:
								print('Parsing Error file %s line %s' % (file.getFullName(), line))
						parser.feed('</salt>')
						fin.close()

						for parsed in handler.getFiles():
							if stack.cond.EvalCondExpr(parsed.get('cond'), host_attrs):
								self.writeSalt(host, parsed)
