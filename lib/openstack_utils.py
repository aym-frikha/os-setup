import openstack

# Initialize cloud
conn = openstack.connect(cloud='openstack')

External_subnet = '172.27.34.0/23'
External_gateway ='172.27.35.254'
provider_phy_net = 'physnet1'
provider_phy_net_type = "flat"
dns_nameserver = ['8.8.8.8']
public_net_name = 'juju-public-net'
public_subnet_name = 'juju-public-subnet'
private_net_name = 'juju-private-net'
private_subnet_name = 'juju-private-subnet'
flavor_name = 'juju_flavor'

def create_private_network():
    print("Create Private Network used By Juju:")
    if not conn.network.find_network(private_net_name):
        private_network = conn.network.create_network(
            name=private_net_name)

        print(private_network)
        if not conn.network.find_subnet(private_subnet_name):
            private_subnet = conn.network.create_subnet(
                name=private_subnet_name,
                network_id=private_network.id,
                ip_version='4',
                cidr='192.168.1.0/24',
                gateway_ip='192.168.1.1',
                dns_nameservers=['8.8.8.8'])
            print(private_subnet)


def create_public_network():
    print("Create Public Network used By Juju:")
    if not conn.network.find_network(public_net_name):
        public_network = conn.network.create_network(
            name=public_net_name,
            is_router_external=True,
            provider_network_type=provider_phy_net_type,
            provider_physical_network=provider_phy_net)
        print(public_network)
        if not conn.network.find_subnet(public_subnet_name):
            public_subnet = conn.network.create_subnet(
                name=public_subnet_name,
                network_id=public_network.id,
                ip_version='4',
                cidr=External_subnet,
                gateway_ip=External_gateway,
                dns_nameservers=dns_nameserver)

            print(public_subnet)


def create_router():
    print(" Create router used by Juju")
    router_name = 'juju-router'
    if not conn.network.find_router(router_name):
        pub_net = conn.network.find_network(public_net_name)
        priv_subnet = conn.network.find_subnet(private_subnet_name)
        router = conn.network.create_router(name=router_name,
                                            external_gateway_info={"network_id": pub_net.id,
                                                                   "enable_snat": "true"}
                                            )
        conn.network.add_interface_to_router(router, subnet_id=priv_subnet.id)


def creat_flavor():
    print(" Create flavor used by Juju")
    if not conn.compute.find_flavor(flavor_name):
        flavor = {
            'name': flavor_name,
            'disk': 1,
            'is_public': True,
            'ram': 1024,
            'vcpus': 1
        }
        conn.compute.create_flavor(**flavor)

def import_image(image_path, image_name):
    print("Import Image:")

    # Url where glance can download the image

    # Build the image attributes and import the image.
    image_attrs = {
        'name': image_name,
        'disk_format': 'qcow2',
        'container_format': 'bare',
        'visibility': 'public',
        'data': open(image_path, 'rb') 
        # 'Location' : 'file://home/ubuntu/demo/os-setup/cirros-0.4.0-x86_64-disk.img'
    }
    image = conn.image.upload_image(**image_attrs)
    activeFlag = False
    i = 1
    while(i < 10):
       status =conn.image.get_image(image.id).status
       print status
       if(status == 'active'):
         activeFlag = True
         break;
         i = i + 1
         sleep(60)
       if( not activeFlag):
         print 'Image upload failed'
    # conn.image.import_image(image, method="web-download", uri=uri)

if __name__ == '__main__':
    create_public_network()
    create_private_network()
    create_router()
