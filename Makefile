# @copyright@
# Copyright (c) 2006 - 2017 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

ROLLROOT = .
include $(PALLETBUILD)/etc/CCRolls.mk

RURL	= https://github.com/saltstack/salt/releases/latest
VERS =	$(shell curl -s -k $(RURL) | sed "s/.*v\(.*\)\".*/\1/g")
		
include $(STACKBUILD)/etc/CCRules.mk

refresh:: 
	(							\
		echo "export ROLL	= stacki-salt"	> version.mk;	\
		echo "export VERSION	= $(VERS)"	>> version.mk;	\
		echo "export RELEASE  = redhat7"	>> version.mk;	\
		echo "COLOR		= darkturquoise"	>> version.mk;	\
	)
