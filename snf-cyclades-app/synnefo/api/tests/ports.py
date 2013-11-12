# Copyright 2011-2013 GRNET S.A. All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
#   1. Redistributions of source code must retain the above
#      copyright notice, this list of conditions and the following
#      disclaimer.
#
#   2. Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials
#      provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY GRNET S.A. ``AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL GRNET S.A OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and
# documentation are those of the authors and should not be
# interpreted as representing official policies, either expressed
# or implied, of GRNET S.A.i

from django.conf import settings
from snf_django.utils.testing import BaseAPITest, override_settings
from django.utils import simplejson as json
from synnefo.cyclades_settings import cyclades_services
from synnefo.lib.services import get_service_path
from synnefo.lib import join_urls
from mock import patch
import synnefo.db.models_factory as dbmf

NETWORK_URL = get_service_path(cyclades_services, 'network',
                               version='v2.0')
PORTS_URL = join_urls(NETWORK_URL, "ports/")


class PortTest(BaseAPITest):
    def test_get_ports(self):
        url = join_urls(PORTS_URL)
        response = self.get(url)
        self.assertEqual(response.status_code, 200)
        ports = json.loads(response.content)
        self.assertEqual(ports, {"ports": []})

    def test_get_port_unfound(self):
        url = join_urls(PORTS_URL, "123")
        response = self.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_port(self):
        nic = dbmf.NetworkInterfaceFactory()
        url = join_urls(PORTS_URL, str(nic.id))
        response = self.get(url, user=nic.userid)
        self.assertEqual(response.status_code, 200)

    @patch("synnefo.db.models.get_rapi_client")
    def test_delete_port(self, mrapi):
        nic = dbmf.NetworkInterfaceFactory(device_owner='vm')
        url = join_urls(PORTS_URL, str(nic.id))
        mrapi().ModifyInstance.return_value = 42
        with override_settings(settings, GANETI_USE_HOTPLUG=True):
            response = self.delete(url, user=nic.userid)
        self.assertEqual(response.status_code, 204)
        with override_settings(settings, GANETI_USE_HOTPLUG=False):
            response = self.delete(url, user=nic.userid)
        self.assertEqual(response.status_code, 400)

    def test_remove_nic_malformed(self):
        url = join_urls(PORTS_URL, "123")
        response = self.delete(url)
        self.assertItemNotFound(response)

    def test_update_port_name(self):
        nic = dbmf.NetworkInterfaceFactory(device_owner='vm')
        url = join_urls(PORTS_URL, str(nic.id))
        request = {'port': {"name": "test-name"}}
        response = self.put(url, params=json.dumps(request),
                            user=nic.userid)
        self.assertEqual(response.status_code, 200)
        res = json.loads(response.content)
        self.assertEqual(res['port']['name'], "test-name")

    def test_update_port_sg_unfound(self):
        sg1 = dbmf.SecurityGroupFactory()
        nic = dbmf.NetworkInterfaceFactory(device_owner='vm')
        nic.security_groups.add(sg1)
        nic.save()
        url = join_urls(PORTS_URL, str(nic.id))
        request = {'port': {"security_groups": ["123"]}}
        response = self.put(url, params=json.dumps(request),
                            user=nic.userid)
        self.assertEqual(response.status_code, 404)

    def test_update_port_sg(self):
        sg1 = dbmf.SecurityGroupFactory()
        sg2 = dbmf.SecurityGroupFactory()
        sg3 = dbmf.SecurityGroupFactory()
        nic = dbmf.NetworkInterfaceFactory(device_owner='vm')
        nic.security_groups.add(sg1)
        nic.save()
        url = join_urls(PORTS_URL, str(nic.id))
        request = {'port': {"security_groups": [str(sg2.id), str(sg3.id)]}}
        response = self.put(url, params=json.dumps(request),
                            user=nic.userid)
        res = json.loads(response.content)
        self.assertEqual(res['port']['security_groups'],
                         [str(sg2.id), str(sg3.id)])

    def test_create_port_no_network(self):
        request = {
            "port": {
                "device_id": "123",
                "name": "port1",
                "network_id": "123"
            }
        }
        response = self.post(PORTS_URL, params=json.dumps(request))
        self.assertEqual(response.status_code, 404)

    @patch("synnefo.db.models.get_rapi_client")
    def test_create_port_private_net(self, mrapi):
        net = dbmf.NetworkFactory(public=False)
        dbmf.IPv4SubnetFactory(network=net)
        dbmf.IPv6SubnetFactory(network=net)
        sg1 = dbmf.SecurityGroupFactory()
        sg2 = dbmf.SecurityGroupFactory()
        vm = dbmf.VirtualMachineFactory(userid=net.userid)
        request = {
            "port": {
                "name": "port1",
                "network_id": str(net.id),
                "device_id": str(vm.id),
                "security_groups": [str(sg1.id), str(sg2.id)]
            }
        }
        mrapi().ModifyInstance.return_value = 42
        with override_settings(settings, GANETI_USE_HOTPLUG=False):
            response = self.post(PORTS_URL, params=json.dumps(request),
                                 user=net.userid)
        self.assertEqual(response.status_code, 400)
        with override_settings(settings, GANETI_USE_HOTPLUG=True):
            response = self.post(PORTS_URL, params=json.dumps(request),
                                 user=net.userid)
        self.assertEqual(response.status_code, 201)

    def test_create_port_public_net_no_ip(self):
        net = dbmf.NetworkFactory(public=True)
        vm = dbmf.VirtualMachineFactory(userid=net.userid)
        request = {
            "port": {
                "name": "port1",
                "network_id": str(net.id),
                "device_id": str(vm.id),
            }
        }
        response = self.post(PORTS_URL, params=json.dumps(request),
                             user=net.userid)
        self.assertEqual(response.status_code, 400)

    def test_create_port_public_net_wrong_ip(self):
        net = dbmf.NetworkFactory(public=True)
        vm = dbmf.VirtualMachineFactory(userid=net.userid)
        request = {
            "port": {
                "name": "port1",
                "network_id": str(net.id),
                "device_id": str(vm.id),
                "fixed_ips": [{"ip_address": "8.8.8.8"}]
            }
        }
        response = self.post(PORTS_URL, params=json.dumps(request),
                             user=net.userid)
        self.assertEqual(response.status_code, 404)

    def test_create_port_public_net_conflict(self):
        net = dbmf.NetworkFactory(public=True)
        fip = dbmf.FloatingIPFactory(nic=None, userid=net.userid)
        vm = dbmf.VirtualMachineFactory(userid=net.userid)
        request = {
            "port": {
                "name": "port1",
                "network_id": str(net.id),
                "device_id": str(vm.id),
                "fixed_ips": [{"ip_address": fip.address}]
            }
        }
        response = self.post(PORTS_URL, params=json.dumps(request),
                             user=net.userid)
        self.assertEqual(response.status_code, 409)

    def test_create_port_public_net_taken_ip(self):
        net = dbmf.NetworkFactory(public=True)
        fip = dbmf.FloatingIPFactory(network=net, userid=net.userid)
        vm = dbmf.VirtualMachineFactory(userid=net.userid)
        request = {
            "port": {
                "name": "port1",
                "network_id": str(net.id),
                "device_id": str(vm.id),
                "fixed_ips": [{"ip_address": fip.address}]
            }
        }
        response = self.post(PORTS_URL, params=json.dumps(request),
                             user=net.userid)
        self.assertEqual(response.status_code, 409)

    @patch("synnefo.db.models.get_rapi_client")
    def test_create_port_with_floating_ip(self, mrapi):
        vm = dbmf.VirtualMachineFactory()
        fip = dbmf.FloatingIPFactory(network__public=True, nic=None,
                                     userid=vm.userid)
        request = {
            "port": {
                "name": "port1",
                "network_id": str(fip.network_id),
                "device_id": str(vm.id),
                "fixed_ips": [{"ip_address": fip.address}]
            }
        }
        mrapi().ModifyInstance.return_value = 42
        with override_settings(settings, GANETI_USE_HOTPLUG=True):
            response = self.post(PORTS_URL, params=json.dumps(request),
                                 user=vm.userid)
        self.assertEqual(response.status_code, 201)

    @patch("synnefo.db.models.get_rapi_client")
    def test_create_port_with_address(self, mrapi):
        """Test creation if IP address is specified."""
        mrapi().ModifyInstance.return_value = 42
        vm = dbmf.VirtualMachineFactory()
        net = dbmf.NetworkWithSubnetFactory(userid=vm.userid,
                                            public=False,
                                            subnet__cidr="192.168.2.0/24",
                                            subnet__gateway=None,
                                            subnet__pool__size=1,
                                            subnet__pool__offset=1)
        request = {
            "port": {
                "name": "port_with_address",
                "network_id": str(net.id),
                "device_id": str(vm.id),
                "fixed_ips": [{"ip_address": "192.168.2.1"}]
            }
        }
        with override_settings(settings, GANETI_USE_HOTPLUG=True):
            response = self.post(PORTS_URL, params=json.dumps(request),
                                 user=vm.userid)
        self.assertEqual(response.status_code, 201)
        new_port_ip = json.loads(response.content)["port"]["fixed_ips"][0]
        self.assertEqual(new_port_ip["ip_address"], "192.168.2.1")

        # But 409 if address is already used
        with override_settings(settings, GANETI_USE_HOTPLUG=True):
            response = self.post(PORTS_URL, params=json.dumps(request),
                                 user=vm.userid)
        self.assertConflict(response)

        # And bad request if IPv6 address is specified
        request["port"]["fixed_ips"][0]["ip_address"] = "babe::"
        with override_settings(settings, GANETI_USE_HOTPLUG=True):
            response = self.post(PORTS_URL, params=json.dumps(request),
                                 user=vm.userid)
        self.assertBadRequest(response)

    def test_create_port_without_device(self):
        net = dbmf.NetworkWithSubnetFactory(userid="test_user",
                                            public=False,
                                            subnet__cidr="192.168.2.0/24",
                                            subnet__gateway=None,
                                            subnet__pool__size=3,
                                            subnet__pool__offset=1)
        request = {
            "port": {
                "name": "port_with_address",
                "network_id": str(net.id),
            }
        }
        response = self.post(PORTS_URL, params=json.dumps(request),
                             user="test_user")
        self.assertEqual(response.status_code, 201)
        new_port = json.loads(response.content)["port"]
        self.assertEqual(new_port["device_id"], None)
        # And with address
        request["port"]["fixed_ips"] = [{"ip_address": "192.168.2.2"}]
        with override_settings(settings, GANETI_USE_HOTPLUG=True):
            response = self.post(PORTS_URL, params=json.dumps(request),
                                 user="test_user")
        self.assertEqual(response.status_code, 201)
        new_port = json.loads(response.content)["port"]
        self.assertEqual(new_port["device_id"], None)
        self.assertEqual(new_port["fixed_ips"][0]["ip_address"], "192.168.2.2")

    def test_add_nic_to_deleted_network(self):
        user = 'userr'
        vm = dbmf.VirtualMachineFactory(name='yo', userid=user,
                                        operstate="ACTIVE")
        net = dbmf.NetworkFactory(state='ACTIVE', userid=user,
                                  deleted=True)
        request = {
            "port": {
                "device_id": str(vm.id),
                "name": "port1",
                "network_id": str(net.id)
            }
        }
        response = self.post(PORTS_URL, params=json.dumps(request),
                             user=net.userid)
        self.assertBadRequest(response)

    def test_add_nic_to_public_network(self):
        user = 'userr'
        vm = dbmf.VirtualMachineFactory(name='yo', userid=user)
        net = dbmf.NetworkFactory(state='ACTIVE', userid=user, public=True)
        request = {
            "port": {
                "device_id": str(vm.id),
                "name": "port1",
                "network_id": str(net.id)
            }
        }
        response = self.post(PORTS_URL, params=json.dumps(request),
                             user=net.userid)
        self.assertBadRequest(response)
        #self.assertFault(response, 403, 'forbidden')

    def test_add_nic_malformed_2(self):
        user = 'userr'
        vm = dbmf.VirtualMachineFactory(name='yo', userid=user)
        net = dbmf.NetworkFactory(state='ACTIVE', userid=user)
        request = {
            "port": {
                "device_id": str(vm.id),
                "name": "port1"
            }
        }
        response = self.post(PORTS_URL, params=json.dumps(request),
                             user=net.userid)
        self.assertBadRequest(response)

    def test_add_nic_not_active(self):
        """Test connecting VM to non-active network"""
        user = 'dummy'
        vm = dbmf.VirtualMachineFactory(name='yo', userid=user)
        net = dbmf.NetworkFactory(state='PENDING', userid=user)
        request = {
            "port": {
                "device_id": str(vm.id),
                "name": "port1",
                "network_id": str(net.id)
            }
        }
        response = self.post(PORTS_URL, params=json.dumps(request),
                             user=net.userid)
        # Test that returns BuildInProgress
        self.assertEqual(response.status_code, 409)

#    def test_add_nic_full_network(self, mrapi):
#        """Test connecting VM to a full network"""
#        user = 'userr'
#        vm = dbmf.VirtualMachineFactory(name='yo', userid=user,
#                                            operstate="STARTED")
#        net = dbmf.NetworkFactory(state='ACTIVE', subnet='10.0.0.0/30',
#                                      userid=user, dhcp=True)
#        pool = net.get_pool()
#        while not pool.empty():
#            pool.get()
#        pool.save()
#        pool = net.get_pool()
#        self.assertTrue(pool.empty())
#        request = {'add': {'serverRef': vm.id}}
#        response = self.mypost('networks/%d/action' % net.id,
#                               net.userid, json.dumps(request), 'json')
#        # Test that returns OverLimit
#        self.assertEqual(response.status_code, 413)
#        self.assertFalse(mrapi.called)
