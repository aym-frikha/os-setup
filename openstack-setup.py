from lib import juju_cli
import os
from jinja2 import Environment, FileSystemLoader


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
cloud_name = 'maas'
controller_name = 'foundations-maas'
model_name = 'openstack'
image='/home/ubuntu/os-setup/xenial-server-cloudimg-amd64-disk1.img'
image_name='xenial'
def render_openstack_cloud_files():
    keystone_ip = juju_cli.run(model_name, 'keystone/0', 'hostname --ip-address')
    admin_password = juju_cli.run(model_name, 'keystone/0', 'leader-get admin_passwd')

    j2_env = Environment(loader=FileSystemLoader(THIS_DIR),
                         trim_blocks=True)

    openstack_cloud_sdk = j2_env.get_template('openstack-cloud-sdk.yaml.j2').render(
        keystone_ip=keystone_ip.rstrip(), admin_password=admin_password.rstrip())

    directory = '/home/ubuntu/.config/openstack/'
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open('/home/ubuntu/.config/openstack/clouds.yaml', 'w') as f:
        f.write(openstack_cloud_sdk)


if __name__ == '__main__':
    render_openstack_cloud_files()
    from lib import openstack_utils
    openstack_utils.create_public_network()
    openstack_utils.create_private_network()
    openstack_utils.create_router()
    openstack_utils.creat_flavor()
    openstack_utils.import_image(image,image_name)
