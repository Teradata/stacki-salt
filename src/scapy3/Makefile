# @copyright@
# Copyright (c) 2006 - 2017 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

PKGROOT        = /opt/stack
ROLLROOT    = ../..
RURL    = https://github.com/phaethon/scapy/releases/latest
VERS 	= $(shell curl -s -k $(RURL) | sed "s/.*v\(.*\)\".*/\1/g")
URL	= https://github.com/phaethon/scapy/archive/
include $(STACKBUILD)/etc/CCRules.mk

refresh::
	(                        \
        echo "NAME=foundation-scapy3" > version.mk;        \
        echo "VERSION=$(VERS)" >> version.mk;    \
	)
	wget $(URL)/v$(VERS).tar.gz

build:: 
	(					\
		tar -xf v$(VERS).tar.gz;	\
		cd scapy-$(VERS);		\
		$(PY.PATH) setup.py build;	\
	)

install::
	(					\
		cd scapy-$(VERS);		\
		$(PY.PATH) setup.py install 	\
			--root $(ROOT);	\
	)

clean::
