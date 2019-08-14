#!/bin/sh
#scp -r charm-neutron-api/* orangebox.home:~/dev/infoblox/charms/neutron-api/
#scp -r charm-infoblox orangebox.home:~/dev/infoblox/charms/

rsync -av -e ssh --exclude='*.pyc' --exclude='*.tox/*' --exclude='*.git*' ../os-setup orangebox.home:~/demo/
