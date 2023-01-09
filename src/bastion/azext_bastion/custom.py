# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#
# Code generated by aaz-dev-tools
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=too-many-statements
# pylint: disable=protected-access

import platform
import subprocess
import tempfile
import threading
import time

import requests
from azure.cli.core.azclierror import ValidationError, InvalidArgumentValueError, RequiredArgumentMissingError, \
    UnrecognizedArgumentError, CLIInternalError, ClientRequestError
from knack.log import get_logger
from msrestazure.tools import is_valid_resource_id

from .aaz.latest.network.bastion import Create as _BastionCreate


logger = get_logger(__name__)


class BastionCreate(_BastionCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        # custom arguments
        args_schema.public_ip_address = AAZResourceIdArg(
            options=["--public-ip-address"],
            help="Name or ID of Azure Public IP. The SKU of the public IP must be Standard.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/publicIPAddresses/{}",
            ),
        )
        args_schema.vnet_name = AAZStrArg(
            options=["--vnet-name"],
            help="Name of the virtual network. It must have a subnet called AzureBastionSubnet",
            required=True,
        )
        # filter arguments
        args_schema.ip_configurations._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        subnet_id = f"/subscriptions/{self.ctx.subscription_id}/resourceGroups/{args.resource_group}" \
                    f"/providers/Microsoft.Network/virtualNetworks/{args.vnet_name}/subnets/AzureBastionSubnet"
        args.ip_configurations = [{
            "name": "bastion_ip_config",
            "subnet": {"id": subnet_id},
            "public_ip_address": {"id": args.public_ip_address}
        }]


SSH_EXTENSION_NAME = "ssh"
SSH_EXTENSION_MODULE = "azext_ssh.custom"
SSH_UTILS_EXTENSION_MODULE = "azext_ssh.ssh_utils"
SSH_EXTENSION_VERSION = "0.1.3"


def _test_extension(extension_name):
    from azure.cli.core.extension import (get_extension)
    from pkg_resources import parse_version

    ext = get_extension(extension_name)
    if parse_version(ext.version) < parse_version(SSH_EXTENSION_VERSION):
        raise ValidationError(f"SSH Extension (version >= {SSH_EXTENSION_VERSION}) must be installed")


def _get_ssh_path(ssh_command="ssh"):
    import os

    if platform.system() == "Windows":
        arch_data = platform.architecture()
        is_32bit = arch_data[0] == "32bit"
        sys_path = "SysNative" if is_32bit else "System32"
        system_root = os.environ["SystemRoot"]
        system32_path = os.path.join(system_root, sys_path)
        ssh_path = os.path.join(system32_path, "openSSH", (ssh_command + ".exe"))
        logger.debug("Platform architecture: %s", str(arch_data))
        logger.debug("System Root: %s", system_root)
        logger.debug("Attempting to run ssh from path %s", ssh_path)

        if not os.path.isfile(ssh_path):
            raise ValidationError("Could not find " + ssh_command + ".exe. Is the OpenSSH client installed?")
    elif platform.system() in ("Linux", "Darwin"):
        import shutil

        ssh_path = shutil.which(ssh_command)
        if not ssh_path:
            raise UnrecognizedArgumentError(f"{ssh_command} not found in path. Is the OpenSSH client installed?")
    else:
        err_msg = "Platform is not supported for this command. Supported platforms: Windows, Darwin, Linux"
        raise UnrecognizedArgumentError(err_msg)

    return ssh_path


def _get_host(username, ip):
    return username + "@" + ip


def _get_azext_module(extension_name, module_name):
    try:
        # adding the installed extension in the path
        from azure.cli.core.extension.operations import add_extension_to_path
        add_extension_to_path(extension_name)
        # import the extension module
        from importlib import import_module
        azext_custom = import_module(module_name)
        return azext_custom
    except ImportError as ie:
        raise CLIInternalError(ie) from ie


def _build_args(cert_file, private_key_file):
    private_key, certificate = [], []
    if private_key_file:
        private_key = ["-i", private_key_file]
    if cert_file:
        certificate = ["-o", "CertificateFile=" + cert_file]
    return private_key + certificate


def ssh_bastion_host(cmd, auth_type, target_resource_id, resource_group_name, bastion_host_name,
                     resource_port=None, username=None, ssh_key=None):
    import os

    _test_extension(SSH_EXTENSION_NAME)

    if not resource_port:
        resource_port = 22
    if not is_valid_resource_id(target_resource_id):
        err_msg = "Please enter a valid resource ID. If this is not working, " \
                  "try opening the JSON view of your resource (in the Overview tab), and copying the full resource ID."
        raise InvalidArgumentValueError(err_msg)

    tunnel_server = _get_tunnel(cmd, resource_group_name, bastion_host_name, target_resource_id, resource_port)
    t = threading.Thread(target=_start_tunnel, args=(tunnel_server,))
    t.daemon = True
    t.start()

    if auth_type.lower() == "password":
        if username is None:
            raise RequiredArgumentMissingError("Please enter username with --username.")
        command = [_get_ssh_path(), _get_host(username, "localhost")]
    elif auth_type.lower() == "aad":
        azssh = _get_azext_module(SSH_EXTENSION_NAME, SSH_EXTENSION_MODULE)
        azssh_utils = _get_azext_module(SSH_EXTENSION_NAME, SSH_UTILS_EXTENSION_MODULE)
        cert_folder = tempfile.mkdtemp(prefix="aadsshcert")
        if not os.path.isdir(cert_folder):
            os.makedirs(cert_folder)
        azssh.ssh_cert(cmd, cert_path=os.path.join(cert_folder, "id_rsa.pub-aadcert.pub"))
        private_key_file = os.path.join(cert_folder, "id_rsa")
        cert_file = os.path.join(cert_folder, "id_rsa.pub-aadcert.pub")
        username = azssh_utils.get_ssh_cert_principals(cert_file)[0]
        command = [_get_ssh_path(), _get_host(username, "localhost")]
        command = command + _build_args(cert_file, private_key_file)
    elif auth_type.lower() == "ssh-key":
        if username is None or ssh_key is None:
            raise RequiredArgumentMissingError("Please enter username --username and ssh cert location --ssh-key.")
        command = [_get_ssh_path(), _get_host(username, "localhost")]
        command = command + _build_args(None, ssh_key)
    else:
        raise UnrecognizedArgumentError("Unknown auth type. Use one of password, aad or ssh-key.")

    command = command + ["-p", str(tunnel_server.local_port)]
    command = command + ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null"]
    command = command + ["-o", "LogLevel=Error"]
    logger.debug("Running ssh command %s", " ".join(command))

    try:
        subprocess.call(command, shell=platform.system() == "Windows")
    except Exception as ex:
        raise CLIInternalError(ex) from ex
    finally:
        tunnel_server.cleanup()


def _get_rdp_path(rdp_command="mstsc"):
    import os

    if platform.system() == "Windows":
        arch_data = platform.architecture()
        sys_path = "System32"
        system_root = os.environ["SystemRoot"]
        system32_path = os.path.join(system_root, sys_path)
        rdp_path = os.path.join(system32_path, (rdp_command + ".exe"))
        logger.debug("Platform architecture: %s", str(arch_data))
        logger.debug("System Root: %s", system_root)
        logger.debug("Attempting to run rdp from path %s", rdp_path)

        if not os.path.isfile(rdp_path):
            raise ValidationError("Could not find " + rdp_command + ".exe. Is the rdp client installed?")
    else:
        raise UnrecognizedArgumentError("Platform is not supported for this command. Supported platforms: Windows")

    return rdp_path


def rdp_bastion_host(cmd, target_resource_id, resource_group_name, bastion_host_name,
                     resource_port=None, disable_gateway=False, configure=False, enable_mfa=False):
    import os
    from azure.cli.core._profile import Profile
    from ._process_helper import launch_and_wait

    if not resource_port:
        resource_port = 3389
    if not is_valid_resource_id(target_resource_id):
        err_msg = "Please enter a valid resource ID. If this is not working, " \
                  "try opening the JSON view of your resource (in the Overview tab), and copying the full resource ID."
        raise InvalidArgumentValueError(err_msg)

    from .aaz.latest.network.bastion import Show
    bastion = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": bastion_host_name
    })

    if bastion['sku']['name'] == "Basic" or \
            bastion['sku']['name'] == "Standard" and bastion['enableTunneling'] is not True:
        raise ClientRequestError('Bastion Host SKU must be Standard and Native Client must be enabled.')

    if platform.system() == "Windows":
        if disable_gateway:
            tunnel_server = _get_tunnel(cmd, resource_group_name, bastion_host_name, target_resource_id, resource_port)
            t = threading.Thread(target=_start_tunnel, args=(tunnel_server,))
            t.daemon = True
            t.start()
            command = [_get_rdp_path(), f"/v:localhost:{tunnel_server.local_port}"]
            launch_and_wait(command)
            tunnel_server.cleanup()
        else:
            profile = Profile(cli_ctx=cmd.cli_ctx)
            access_token = profile.get_raw_token()[0][2].get("accessToken")
            logger.debug("Response %s", access_token)

            web_address = f"https://{bastion['dnsName']}/api/rdpfile?resourceId={target_resource_id}" \
                          f"&format=rdp&rdpport={resource_port}&enablerdsaad={enable_mfa}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Content-Type": "application/json"
            }
            response = requests.get(web_address, headers=headers)
            if not response.ok:
                raise ClientRequestError("Request to EncodingReservedUnitTypes v2 API endpoint failed.")

            _write_to_file(response)

            rdpfilepath = os.getcwd() + "/conn.rdp"
            command = [_get_rdp_path()]
            if configure:
                command.append("/edit")
            command.append(rdpfilepath)
            launch_and_wait(command)
    else:
        raise UnrecognizedArgumentError("Platform is not supported for this command. Supported platforms: Windows")


def _write_to_file(response):
    with open("conn.rdp", "w", encoding="utf-8") as f:
        for line in response.text.splitlines():
            if not line.startswith('signscope'):
                f.write(line + "\n")


def _get_tunnel(cmd, resource_group_name, name, vm_id, resource_port, port=None):
    from .tunnel import TunnelServer
    from .aaz.latest.network.bastion import Show

    bastion = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": name
    })
    if port is None:
        port = 0  # will auto-select a free port from 1024-65535
    tunnel_server = TunnelServer(cmd.cli_ctx, "localhost", port, bastion, vm_id, resource_port)

    return tunnel_server


def _start_tunnel(tunnel_server):
    tunnel_server.start_server()


def _tunnel_close_handler(tunnel):
    logger.info("Ctrl + C received. Clean up and then exit.")
    tunnel.cleanup()
    import sys
    sys.exit()


def create_bastion_tunnel(cmd, target_resource_id, resource_group_name, bastion_host_name, resource_port, port,
                          timeout=None):
    if not is_valid_resource_id(target_resource_id):
        raise InvalidArgumentValueError("Please enter a valid VM resource ID.")

    tunnel_server = _get_tunnel(cmd, resource_group_name, bastion_host_name, target_resource_id, resource_port, port)
    t = threading.Thread(target=_start_tunnel, args=(tunnel_server,))
    t.daemon = True
    t.start()
    logger.warning("Opening tunnel on port: %s", tunnel_server.local_port)
    logger.warning("Tunnel is ready, connect on port %s", tunnel_server.local_port)
    logger.warning("Ctrl + C to close")

    import signal
    # handle closing the tunnel with an active session still connected
    signal.signal(signal.SIGINT, lambda signum, frame: _tunnel_close_handler(tunnel_server))

    if timeout:
        time.sleep(int(timeout))
    else:
        while t.is_alive():
            time.sleep(5)
