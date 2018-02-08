# stacki-salt  for Stacki 5.0

The stacki-salt pallet integrates Salt Stack open source version 2017.7.3 (February 5, 2018) (Hydrogen or Nitrogen or Teragen or Termagant or whatever)

The Stacki frontend acts as the salt master and the endpoint for salt-api. The frontend also has a minion. 

The Stacki backends are all salt-minions.

Minion keys are accepted by default during install via the rest_tornado api housed on the frontend and served with salt-api.

Stacki used to pre-seed minion keys, but the way we did that no longer is sufficient in this version of Salt.

The keys are now accepted via an api call to the frontend at first boot after an install or re-install of a backend node. You shouldn't have to wrangle Salt minion keys.

By default, the "stack run host" command uses SSH as it's transportation backend. (Parallel ssh thankyouvermuch.) When the stacki-salt pallet is added to your frontend, the transportation protocol defaults to Salt. This is much faster if you have a large cluster. If you can't use SSH in your environment, this may also be acceptable since Salt uses 2048 AES encryption by default. 


### Adding the pallet

Download the stacki-salt pallet for Stacki 5.0 to your frontend.

```
# stack add pallet

# stack enable pallet
```

### Run the pallet

Now that the pallet is on and enabled, run it:

```
# stack run pallet stacki-salt | bash
```

This should bring up a salt-master, salt-api, and salt-minion on the frontend. Check to see if they are "active"
```
systemctl status salt-master salt-api salt-minion
```

And make sure the frontend's minion key has been accepted:
```
salt-key -L
```

### Backends

There is no way at the moment to easily setup salt on the backends without a reinstall. It's advisable you add the stacki-salt pallet before installing machines. 

#### Initial install
Salt will just be there. 

Make sure with:

```
# salt-key -L

When they're all up:

# salt '*' test.ping

or

# stack run host command="uptime"
```


A reinstall without nukedisk=True just refreshes the installation and doesn't ruin your data, so feel free to do that. 

#### Re-install your backends.


```
# stack set host boot a:backend action=install

# stack run host command="reboot"

(Or power cycle with your preferred method. 
```


