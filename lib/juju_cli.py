# Copyright 2017-2019 Canonical Ltd. All rights reserved.
import os
import subprocess
import yaml
from datetime import datetime
import logging


def add_cloud(cloud_name, cloud_definition_file):
    command = ['juju', 'add-cloud', '--replace',
               cloud_name, cloud_definition_file]
    subprocess.check_call(command)


def add_credential(cloud_name, credentials_file):
    command = ['juju', 'add-credential', '--replace',
               cloud_name, '-f', credentials_file]
    subprocess.check_call(command)


def add_unit(model, application, placement_directives=None):
    command = [
        'juju', 'add-unit', '-m', model,
        '--debug',
        application,
    ]

    if placement_directives is not None:
        command.extend(
            ['--to', placement_directives])
    subprocess.check_call(command)


def model_defaults(controller, settings):
    command = ['juju', 'model-defaults', '-c', controller]
    for key, value in settings.items():
        command.append("%s=%s" % (key, value))
    subprocess.check_call(command)


def is_controller_reachable(cloud, timeout=10):
    command = ['juju', 'show-controller', cloud]
    try:
        subprocess.check_call(command, timeout)
    except subprocess.CalledProcessError:
        logging.error("juju controller is bootstrapped but unreachable.")
        raise


def bootstrap(cloud, options=None):
    if options is None:
        options = []

    command = ['juju', 'bootstrap']
    command.extend(options)
    command.extend([cloud, cloud])
    print(command)
    try:
        subprocess.check_call(command)
    # check if controller bootstrapped and available, LP: #1750822
    except subprocess.CalledProcessError:
        is_controller_reachable(cloud)
        logging.warn("controller \"" + cloud +
                     "\" is already bootstrapped, continuing.")
        pass


def deploy(model, bundle, overlays=None, network_space=None):
    command = [
        'juju', 'deploy', '-m', model, bundle,
    ]

    if overlays is None:
        overlays = []

    for overlay in overlays:
        command.extend(['--overlay', overlay])

    if network_space is not None:
        command.extend(
            ['--bind', network_space])
    subprocess.check_call(command)


def enable_ha(controller):
    command = [
        'juju', 'enable-ha', '-c', controller]
    subprocess.check_call(command)


def status(model):
    command = ['juju', 'status', '-m', model, '--format=yaml']
    return yaml.load(subprocess.check_output(command))


def get_applications(status):
    """Return the applications section from status.

    :param status: juju status
    :type status: yaml string
    :returns: application section of the status
    :rtype: dict
    """
    return status['applications']


def iter_units(status):
    """Yield each of the units in status.

    :param status: juju status
    :type status: yaml string
    :returns: yields each unit listed in the status
    :rtype: dict
    """
    for app_name, app in sorted(get_applications(status).items()):
        for unit_name, unit in sorted(app.get('units', {}).items()):
            yield unit_name, unit
            subordinates = unit.get('subordinates', ())
            for sub_name in sorted(subordinates):
                yield sub_name, subordinates[sub_name]


def get_leader(model, application_name):
    """Return the name of the leader unit

    :param model: model to check for application
    :type model: string
    :param application: name of an application
    :type application: string
    :returns: name of leader unit
    :rtype: string
    """
    command = ['juju', 'run', '--format=yaml',
               '--model', model,
               '--application', application_name,
               'is-leader']
    results = yaml.load(subprocess.check_output(command))
    for unit in results:
        if 'True' in unit['Stdout'].strip():
            return unit['UnitID']


def get_units(status, application_name):
    """Return all units for the given application_name.

    :param status: juju status
    :type status: yaml string
    :param application_name: name of the application
    :type application_name: string
    :returns: list of (unit_name, unit) tuples
    :rtype: list
    """
    units = []
    for unit_name, unit in iter_units(status):
        if unit_name.startswith('{}/'.format(application_name)):
            units.append((unit_name, unit,))
    return units


def get_unit_names(status, application_name):
    """Return all unit names for a given application_name.

    :param status: juju status
    :type status: yaml string
    :param application_name: name of the application
    :type application_name: string
    :returns: list of unit name strings
    :rtype: list
    """
    return [name for name, unit in get_units(status, application_name)]


def generate_image_metadata(region, auth_url, image_id, series, arch, path):
    command = ['juju', 'metadata', 'generate-image', '-a', arch, '-r', region,
               '-u', auth_url, '-i', image_id, '-s', series, '-d', path]
    subprocess.check_call(command)


def run(model, unit, cmd, args=None):
    command = ['juju', 'run', '-m', model, '-u', unit, cmd]
    if args is not None:
        command.append(args)
    return subprocess.check_output(command)


def get_action_id(output):
    """Return the action uuid from output.

    :param output: action output
    :parm type: string
    :returns: action id
    :rtype: string
    """
    return output['Action queued with id']


def run_action(model, unit, action, args=None):
    command = ['juju', 'run-action', '-m', model,
               '--format=yaml', unit, action]
    if args is not None:
        command.append(args)
    return yaml.load(subprocess.check_output(command))


def list_actions(model, application):
    command = ['juju', 'list-actions', '-m', model,
               '--format=yaml', application]
    return yaml.load(subprocess.check_output(command))


def wait_for_action(model, action_id, timeout=600):
    command = ['juju', 'show-action-output', '-m', model,
               '--format=yaml', '--wait', str(timeout), action_id]
    return yaml.load(subprocess.check_output(command))


def show_action_status(model, action_id):
    command = ['juju', 'show-action-status', '-m', model,
               '--format=yaml', action_id]
    return yaml.load(subprocess.check_output(command))


def model_exists(model_name):
    try:
        status(model_name)
    except subprocess.CalledProcessError:
        return False
    return True


def add_model(controller_name, model_name):
    command = ['juju', 'add-model', '-c', controller_name, model_name]
    subprocess.check_call(command)


def wait(model, exclude=None):
    if exclude:
        exclude_str = '-x ' + ' -x '.join(exclude)
        exclude_list = exclude_str.split()
    else:
        exclude_list = []
    command = ['juju', 'wait', '-m', model, '-t', '14400', '--workload']
    subprocess.check_call(command + exclude_list)


def controller_exists(controller_name):
    command = ['juju', 'controllers', '--format', 'yaml']
    results = yaml.load(subprocess.check_output(command))
    return controller_name in results['controllers']


def kill_controller(controller_name):
    subprocess.check_call(
        ['juju', 'kill-controller', '--yes', controller_name])


def destroy_model(model_name):
    """Destroy a model.

    :param str model_name: The name of the model to destroy.
    """
    subprocess.check_call(
        ['juju', 'destroy-model', '--yes', model_name])


def capture_crashdump(controller_name, model_name, output_dir):
    """Collect a juju crashdump.
    :param str controller_name: The controller the model exists on.
    :param str model_name: The model to collect logs for.
    :param str output_dir: The directory to write the crashdump to.
    :returns: The full path to the crashdump file.
    """
    datestring = datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
    crashdump_path = os.path.join(
        output_dir, "juju-crashdump-%s-%s.tar.gz" % (
            model_name, datestring))
    full_model = "%s:%s" % (controller_name, model_name)
    current_dir = os.path.dirname(__file__)
    addons_yaml = os.path.join(current_dir, "resources/addons.yaml")
    command = [
        "/snap/bin/juju-crashdump", "-m", full_model, "--timeout", "300",
        "--small", "-f", "100000000", "--compression", "gz",
        "--addons-file", addons_yaml, "--addon", "juju-engine-report", "-o",
        crashdump_path]
    subprocess.check_call(command)
    return crashdump_path


def relate(model, app1, app2):
    command = ['juju', 'relate', '-m', model, app1, app2]
    return subprocess.check_output(command)


def scp(model, unit, src, dest):
    command = ['juju', 'scp', '-m', model, '{}:{}'.format(unit, src), dest]
    return subprocess.check_output(command)