#!/usr/bin/env python 

import os
import json
from time import sleep
import optparse
import yaml
import sys

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

# Parameters optioning
parser = optparse.OptionParser(
    usage="%prog -r <region_name> \nAuthor:\t\tInsiya Khandwala",
    prog='openstack_data_add.py',
    version='1.0',
    )
parser.add_option('-r', '--region',
                  dest="region_name",
                  # action="store",
                  type="string",
                  help="provide region"
                  )
parser.add_option('-p', '--ports',
                  dest="ports",
                  action="store_true",
                  help="add ports"
                  )
parser.add_option('-n', '--networking',
                  dest="networks",
                  action="store_true",
                  help="add networks"
                  )
parser.add_option('-f', '--flavors',
                  dest="flavors",
                  action="store_true",
                  help="add flavors"
                  )
parser.add_option('-a', '--aggregate',
                  dest="aggregate",
                  action="store_true",
                  help="add nova aggregates"
                  )
parser.add_option('-d', '--designate',
                  dest="designate",
                  action="store_true",
                  help="generate designate yaml"
                  )
parser.add_option('-c', '--commit',
                  dest="commit",
                  action="store_true",
                  help="commit changes, does not run in dry-mode"
                  )
parser.add_option('-s', '--sub_n_segs',
                  dest="subs_n_segs",
                  action="store_true",
                  help="add subnets and segments"
                  )                  

(options, args) = parser.parse_args()
if not options.region_name:   # if region is not given
    parser.error('Region not given , use --help option if needed')

def _commit(COMMAND):
    if options.commit:
        print(COMMAND)
        os.system(COMMAND)
        sleep(1.5)
    else:
        print(COMMAND)

def _open_json_file(FILE):
    if os.path.exists(FILE):
        try:
            data = json.load(open(FILE))
            return data
        except:
            print("script was not able to open data file")
    else:
        print(str(FILE) + " doesnt not exists")

# def _get_network_data():
#     datax = os.popen("openstack network list -f json").read()
#     data_json = json.loads(datax)
#     return data_json

def _delete_segments():
    datax = os.popen('openstack network segment list -f json').read()
    data_json = json.loads(datax)
    for segment in data_json:
        command = "openstack network segment delete " + str(segment['ID'])
        _commit(command)

def port():
    data_network = _open_json_file(networks_json)
    data = _open_json_file(ports_json)
    data_subnets = _open_json_file(subnets_json)
    for network in data_network:
        if network['location']['project']['id'] == "admin":     
            for port in data:
                if port['network_id'] == network['id']:
                    command = "openstack port create --network " + str(network['name']) + "  --project " + str(port['project_id'])
                    for ip in port['Fixed IP Addresses']:
                        for subnet in data_subnets:
                            if subnet['id'] == ip['subnet_id']:
                                blah = "  --fixed-ip subnet="+ str(subnet['name']) + ",ip-address=" + str(ip['ip_address'])
                                command = command + blah
                    if len(port['allowed_address_pairs']) > 0:
                        for pairs in port['allowed_address_pairs']:
                            blah2 = " --allowed-address mac-address=" + pairs['mac_address'] + ",ip-address=" + pairs['ip_address']
                            command = command + blah2
                    if port['NAME']:
                        command = command + " " + str(port['NAME'])
                        _commit(command)

def networks():
    try:
        data = _open_json_file(networks_json)
        command = ""
        for network in data:
            if network['location']['project']['id'] == "admin":
                command = "openstack network create --share " + " --mtu " + str(network['mtu']) + " " + str(network['name'])
                _commit(command)
    except Exception as e:
        print("something went wrong !")
        print(e)

def segments_n_subnets():
    data_network = _open_json_file(networks_json)
    data = _open_json_file(segments_json)
    data_subnets = _open_json_file(subnets_json)
    for network in data_network:
        if network['location']['project']['id'] == "admin":
            for segment in data:
                command_segment = "openstack network segment create --physical-network "
                if segment['network_id'] == network['id']:
                    command_segment = command_segment + str(segment['physical_network']) + " --network-type " + str(segment['network_type']) + " --segment " + \
                    str(segment['segmentation_id']) + " --network " + str(network['name']) + " " + str(segment['name'])
                    _commit(command_segment)
                for subnet in data_subnets:
                    command_subnet =  "openstack subnet create "
                    if subnet['segment_id'] == segment['id'] and subnet['network_id'] == network['id']:
                        if subnet['enable_dhcp'] == False:
                            command_subnet = command_subnet + "--no-dhcp "
                        if len(subnet['dns_nameservers']) > 1:
                            command_subnet =  command_subnet + " --dns-nameserver " + ",".join(subnet['dns_nameservers'])
                        elif len(subnet['dns_nameservers']) == 1:
                            command_subnet = command_subnet +  " --dns-nameserver " + str(subnet['dns_nameservers'][0])
                        if subnet['gateway_ip']:
                            command_subnet = command_subnet + " --gateway " + str(subnet['gateway_ip'])
                        command_subnet = command_subnet + " --network " + str(network['name']) + " --network-segment " + str(segment['name']) + " --ip-version " + \
                        str(subnet['ip_version']) + " --allocation-pool start=" + str(subnet['allocation_pools'][0]['start']) + ",end=" + str(subnet['allocation_pools'][0]['end']) + \
                        " --subnet-range " + str(subnet['cidr']) + " " + str(subnet['name'])
                        _commit(command_subnet)
def flavors():
    data = _open_json_file(flavors_json)
    for flavor in data:
        command = "openstack flavor create --id " + str(flavor['id']) + " --swap " + str(flavor['swap']) + " --ram " + str(flavor['ram']) + " --disk " +  str(flavor['disk']) + \
        " --vcpus " + str(flavor['vcpus']) 
        if flavor['OS-FLV-EXT-DATA:ephemeral'] > 0:
            command = command + " --ephemeral " + str(flavor['OS-FLV-EXT-DATA:ephemeral'])
        if flavor['os-flavor-access:is_public'] is True:
            command = command + " --public "
        command = command + " " + flavor['name']
        _commit(command)


def aggregate():
    data = _open_json_file(aggregate_json)
    for aggregate in data:
        command = "openstack aggregate create " + " --zone " + str(aggregate['availability_zone']) + " " + str(aggregate['name']) 
        _commit(command)
        for host in aggregate['hosts']:
            blah = "openstack aggregate add host " + str(aggregate['name'])  + " " + host
            _commit(blah)

def designate():
    data = _open_json_file(designate_json)
    recordsets_list = []
    recordsets_yaml = {}
    for record in data[0]:
        if "p4gen" in record['name']:
            continue
        recordsets_yaml['name'] = record['name']
        recordsets_yaml['zone'] = record['zone_name']
        recordsets_yaml['type'] = record['type']
        recordsets_yaml['ttl'] = record['ttl']
        recordsets_yaml['records'] = record['data'].split(",")
        recordsets_list.append(recordsets_yaml.copy())
    
    final_yaml = {'zones': [x['name'][:-1] for x in data[1]] ,'recordsets': recordsets_list}
    print(yaml.dump(final_yaml, Dumper=NoAliasDumper))

networks_json = "data/" + options.region_name + ".network_info.json"
ports_json = "data/" + options.region_name + ".port_info.json"
segments_json = "data/" + options.region_name + ".segments_info.json"
subnets_json = "data/" + options.region_name + ".subnet_info.json"
flavors_json = "data/" + options.region_name + ".flavors.json"
aggregate_json = "data/" + options.region_name + ".aggregate.json"
designate_json = "data/" + options.region_name + ".designate.json"

if options.networks:
    try:
        networks()
        _delete_segments()
    except Exception as e:
        print("something went wrong during networks, segments and subnets creations")
        print(e)
elif options.subs_n_segs:
    try:
        segments_n_subnets()
    except Exception as e:
        print("something went wrong during segments and subnets creation")
        print(e)
elif options.ports:
    try:
        port()
    except Exception as e:
        print("something went wrong during port creation")
        print(e)
elif options.flavors:
    try:
        flavors()
    except Exception as e:
        print("something went wrong during creation of flavors")
        print(e)
elif options.aggregate:
    try:
        aggregate()
    except Exception as e:
        print("something went wrong during creating nova host aggregates")
        print(e)
elif options.designate:
    try:
        designate()
    except Exception as e:
        print("something went wrong generating designate yaml")
        print(e)
else:
    parser.error('No other option was selected ,use --help option if needed')
