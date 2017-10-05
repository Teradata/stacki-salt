#
# Do not edit
#

.PHONY: install-rpm
install-rpm: /export/src/stacki-salt/src/salt/../../../build--/RPMS/x86_64/salt-5.0-.x86_64.rpm
	rpm -Uhv --force --nodeps $<
