# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#
# Code generated by aaz-dev-tools
# --------------------------------------------------------------------------------------------

import uuid
import unittest

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.scenario_tests import record_only
from azure.cli.testsdk import ScenarioTest


class FirmwareanalysisScenario(ScenarioTest):
    @record_only()
    def test_generate_upload_url(self):
        self.kwargs.update({
            'firmware_id': 'cd4e9671-72cf-4f78-9c9e-8e8bb2c5eaa4',
            'resource_group': 'FirmwareAnalysisRG',
            'workspace_name': 'default'
        })

        self.cmd('az firmwareanalysis workspace generate-upload-url '
                 '--resource-group {resource_group} '
                 '--workspace-name {workspace_name} '
                 '--firmware-id {firmware_id}',
                 checks=[self.check('length(@)', 1),
                         self.check("url.contains(@, '{firmware_id}')", True)]).get_output_in_json()

    @record_only()
    @AllowLargeResponse()
    def test_firmware_commands(self):
        self.kwargs.update({
            'resource_group': 'FirmwareAnalysisRG',
            'firmware_id': 'cd4e9671-72cf-4f78-9c9e-8e8bb2c5eaa4',
            'workspace_name': 'default'
        })

        self.cmd('az firmwareanalysis firmware create '
                 '--firmware-id {firmware_id} '
                 '--resource-group {resource_group} '
                 '--workspace-name {workspace_name} '
                 '--file-name file_name '
                 '--file-size 1 '
                 '--vendor vendor_name '
                 '--status Pending '
                 '--version version_name '
                 '--description fw_description '
                 '--model fwid_model ',
                 checks=[self.greater_than('length(@)', 1),
                         self.check('description', 'fw_description'),
                         self.check('vendor', 'vendor_name'),
                         self.check('fileName', 'file_name'),
                         self.check('fileSize', 1),
                         self.check('status', 'Pending'),
                         self.check('version', 'version_name'),
                         self.check("id.contains(@, 'e8b0bf57-9ef4-4bc6-8a09-6a8bf22f6931')", True),
                         self.check('model', 'fwid_model')]).get_output_in_json()

        self.cmd('az firmwareanalysis firmware  show '
                 '--resource-group {resource_group} '
                 '--firmware-id {firmware_id} '
                 '--workspace-name {workspace_name} ',
                 checks=[self.greater_than('length(@)', 1),
                         self.check('type', 'microsoft.iotfirmwaredefense/workspaces/firmwares'),
                         self.check('resourceGroup', 'FirmwareAnalysisRG')]).get_output_in_json()

        self.cmd('az firmwareanalysis firmware  list '
                 '--resource-group {resource_group} '
                 '--workspace-name {workspace_name} ',
                 checks=[self.greater_than('length(@)', 1),
                         self.check('[0].type', 'microsoft.iotfirmwaredefense/workspaces/firmwares'),
                         self.check('[0].resourceGroup', 'FirmwareAnalysisRG')]).get_output_in_json()

    @record_only()
    @AllowLargeResponse()
    def test_analyser_commands(self):
        self.kwargs.update({
            'resource_group': 'FirmwareAnalysisRG',
            'firmware_id': '80ac3a57-b985-888b-ae28-b6eb8c8393a4',
            'workspace_name': 'default'
        })

        self.cmd('az firmwareanalysis firmware  binary-hardening '
                 '--resource-group {resource_group} '
                 '--workspace-name {workspace_name} '
                 '--firmware-id {firmware_id}',
                 checks=[self.greater_than('length(@)', 1),
                         self.check('[0].type', 'Microsoft.IoTFirmwareDefense/workspaces/firmwares/binaryHardeningResults'),
                         self.check('[0].resourceGroup', 'FirmwareAnalysisRG')]).get_output_in_json()

        self.cmd('az firmwareanalysis firmware  sbom-component '
                 '--resource-group {resource_group} '
                 '--workspace-name {workspace_name} '
                 '--firmware-id {firmware_id}',
                 checks=[self.greater_than('length(@)', 1),
                         self.check('[0].type', 'Microsoft.IoTFirmwareDefense/workspaces/firmwares/sbomComponents'),
                         self.check('[0].resourceGroup', 'FirmwareAnalysisRG')]).get_output_in_json()

        self.cmd('az firmwareanalysis firmware  cve '
                 '--resource-group {resource_group} '
                 '--workspace-name {workspace_name} '
                 '--firmware-id {firmware_id}',
                 checks=[self.greater_than('length(@)', 1),
                         self.check('[0].type', 'Microsoft.IoTFirmwareDefense/workspaces/firmwares/cves'),
                         self.check('[0].resourceGroup', 'FirmwareAnalysisRG')]).get_output_in_json()

        self.cmd('az firmwareanalysis firmware  crypto-certificate '
                 '--resource-group {resource_group} '
                 '--workspace-name {workspace_name} '
                 '--firmware-id {firmware_id}',
                 checks=[self.greater_than('length(@)', 1),
                         self.check('[0].type', 'Microsoft.IoTFirmwareDefense/workspaces/firmwares/cryptoCertificates'),
                         self.check('[0].resourceGroup', 'FirmwareAnalysisRG')]).get_output_in_json()

        self.cmd('az firmwareanalysis firmware  crypto-key '
                 '--resource-group {resource_group} '
                 '--workspace-name {workspace_name} '
                 '--firmware-id {firmware_id}',
                 checks=[self.greater_than('length(@)', 1),
                         self.check('[0].type', 'Microsoft.IoTFirmwareDefense/workspaces/firmwares/cryptoKeys'),
                         self.check('[0].resourceGroup', 'FirmwareAnalysisRG')]).get_output_in_json()

        self.cmd('az firmwareanalysis firmware  password-hash '
                 '--resource-group {resource_group} '
                 '--workspace-name {workspace_name} '
                 '--firmware-id {firmware_id}',
                 checks=[self.greater_than('length(@)', 1),
                         self.check('[0].type', 'Microsoft.IoTFirmwareDefense/workspaces/firmwares/passwordHashes'),
                         self.check('[0].resourceGroup', 'FirmwareAnalysisRG')]).get_output_in_json()
