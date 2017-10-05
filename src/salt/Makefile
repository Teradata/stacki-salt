# @copyright@
# Copyright (c) 2006 - 2017 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

PKGROOT		= /opt/stack
ROLLROOT	= ../..
#PACKAGES	= salt Jinja2 msgpack-python \
#		PyYAML MarkupSafe requests \
#		tornado pycrypto pyzmq \
#		urllib3 certifi idna chardet

PACKAGES	= salt msgpack-python tornado pycrypto


include $(STACKBUILD)/etc/CCRules.mk

refresh:: 
	pip3 download --no-deps $(PACKAGES) -d PKGS
	
build::

install::
	pip3 install -I --no-deps --root=$(ROOT) ./PKGS/*
	tar -xxzf ./PKGS/salt-2017.7.1.tar.gz
	mkdir -p $(ROOT)/usr/lib/systemd/system
	$(INSTALL) -m644 ./salt-2017.7.1/pkg/salt-master.service $(ROOT)/usr/lib/systemd/system/salt-master.service
	$(INSTALL) -m644 ./salt-2017.7.1/pkg/salt-minion.service $(ROOT)/usr/lib/systemd/system/salt-minion.service

clean::
