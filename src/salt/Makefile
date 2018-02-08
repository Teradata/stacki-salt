# @copyright@
# Copyright (c) 2006 - 2017 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

PKGROOT        = /opt/stack
ROLLROOT    = ../..
#PACKAGES    = salt Jinja2 msgpack-python \
#        PyYAML MarkupSafe requests \
#        tornado pycrypto pyzmq \
#        urllib3 certifi idna chardet

#PACKAGES    = salt msgpack-python tornado pycrypto futures cherrypy
PACKAGES    = salt msgpack-python tornado pycrypto futures
RURL    = https://github.com/saltstack/salt/releases/latest
VERS=$(shell curl -s -k $(RURL) | sed "s/.*v\(.*\)\".*/\1/g")

include $(STACKBUILD)/etc/CCRules.mk

refresh::
	(                        \
        echo "NAME=stacki-salt" > version.mk;        \
        echo "ANAME=salt" >> version.mk;    \
        echo "VERSION=$(VERS)" >> version.mk;    \
	)
	python3 -m ensurepip
#	pip3 download $(PACKAGES) -d PKGS
	pip3 download --no-deps $(PACKAGES) -d PKGS

build::

install::
	pip3 install -I --no-deps --root=$(ROOT) ./PKGS/*
	tar -xxzf ./PKGS/$(ANAME)-$(VERSION).tar.gz
	mkdir -p $(ROOT)/usr/lib/systemd/system
	$(INSTALL) -m644 ./$(ANAME)-$(VERSION)/pkg/salt-master.service $(ROOT)/usr/lib/systemd/system/salt-master.service
	$(INSTALL) -m644 ./$(ANAME)-$(VERSION)/pkg/salt-minion.service $(ROOT)/usr/lib/systemd/system/salt-minion.service
	$(INSTALL) -m644 ./$(ANAME)-$(VERSION)/pkg/salt-api.service $(ROOT)/usr/lib/systemd/system/salt-api.service

clean::
