# stacki-salt  for Stacki 5.0

The stacki-salt pallet integrates Salt Stack open source version 2017.7.3 (February 5, 2018) (Hydrogen or Nitrogen or Teragen or Termagant or whatever)

The Stacki frontend acts as the salt master and the endpoint for salt-api. The frontend also has a minion. 

The Stacki backends all have salt-minions.

Minions keys are preseeded via an api call to the frontend at first boot after an install or re-install of a backend node. You shouldn't have to wrangle Salt minion keys.

By default, the "stack run host" command uses SSH as it's transportation backend. (Parallel ssh thankyouvermuch.) When the stacki-salt pallet is added to your frontend, the transportation protocol defaults to Salt. This is much faster if you have a large cluster. If you can't use SSH in your environment, this may also be acceptable since Salt uses 2048 AES encryption by default. 


### Adding the pallet

Download the stacki-salt pallet for Stacki 5.0 to your frontend.

[stacki-salt-5.0_2017.7.3_3cf9991-redhat7.x86_64.disk1.iso](http://http://teradata-stacki.s3.amazonaws.com/release/stacki/5.x/stacki-salt-5.0_2017.7.3_3cf9991-redhat7.x86_64.disk1.iso) 
md5sum: 4b3fd03132f6676b73c8cd943f2a7c4b

```
# stack add pallet stacki-salt-5.0_2017.7.3_3cf9991-redhat7.x86_64.disk1.iso

# stack enable pallet stacki-salt
```

### Run the pallet

Now that the pallet is on and enabled, run it:

```
# stack run pallet stacki-salt | bash
```

This should bring up a salt-master, salt-api, and salt-minion on the frontend. Check to see if they are "active"
```
# systemctl status salt-master salt-api salt-minion
```

And make sure the frontend's minion key has been accepted:
```
# salt-key -L
```

### Backends

There is no way at the moment to easily setup salt on the backends without a reinstall. It's advisable you add the stacki-salt pallet before installing machines. 

#### Initial install
Salt will just be there working on a backends after install. Don't do nothing. Just install.

Make sure with:

```
# salt-key -L
```

If you like to watch whilst the backends are installing:

```
# watch -n 2 "salt-key -L"
```

When they're all up:
```
# salt '*' test.ping
```

or
```
# stack run host command="uptime"
```

#### Re-install your backends.


A reinstall without nukedisks=True just refreshes the installation and doesn't ruin your data, so feel free to do that to get Salt working between your frontends and backends.


```
# stack set host boot a:backend action=install

# stack run host command="reboot"

(Or power cycle with your preferred method. 
```


