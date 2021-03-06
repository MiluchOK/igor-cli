#!/usr/bin/env python

import click
import json
from igor import igor
from request_utils import make_api_request
import types
from urllib import quote_plus

def ipmi_print(data, indent=0, composite_list=False):
    if isinstance(data, types.DictType):
        for key, value in data.iteritems():
            for i in xrange(indent):
                print '\t',

            print key + ':',
            if isinstance(value, types.DictType):
                print
                ipmi_print(value, indent+1)
            elif isinstance(value, types.ListType):
                if not composite_list:
                    print ', '.join(value)
                else:
                    print
                    for item in value:
                        ipmi_print(item, indent+1)
                        print
                    print
            else:
                print value

# IPMI operation commands

## ipmitool chassis
## ipmitool chassis power

@igor.group()
@click.pass_obj
def ipmi(config):
    """IPMI operations"""

@ipmi.group()
@click.pass_obj
def chassis(config):
    """Chassis commands"""

@chassis.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.pass_obj
def info(config, hostname):
    """View chassis information.

    Example:

    \b
    $ igor ipmi chassis info --hostname osl01
    power_on: True
    misc_chassis_state: None
    power_restore_policy: always-on
    hostname: osl01
    power_fault: None
    main_power_fault: False
    power_control_fault: False
    power_interlock: inactive
    last_power_event: None
    power_overload: False
    """

    response = make_api_request('GET', config, '/machines/' + hostname +
                                               '/chassis')
    ipmi_print(response.json())

@chassis.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.option('--state', help='Desired power state.')
@click.pass_obj
def power(config, hostname, state):
    """View or set the chassis power.

    Example:

    \b
    $ igor ipmi chassis power --hostname osl01
    power_on: True
    hostname: osl01

    \b
    $ igor ipmi chassis power --hostname osl01 --state cycle
    power_on: True
    hostname: osl01
    """

    if not state:
        response = make_api_request('GET', config, '/machines/' + hostname +
                                                   '/chassis/power')
    else:
        data = json.dumps({'state': state})
        response = make_api_request('POST', config, '/machines/' + hostname +
                                                 '/chassis/power', data=data)
    ipmi_print(response.json())

@chassis.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.option('--state', help='Desired power policy.')
@click.pass_obj
def policy(config, hostname, state):
    """View or set the chassis power policy on the event of power failure.

    Example:

    \b
    $ igor ipmi chassis policy --hostname osl01
    policy: always-on
    hostname: osl01

    \b
    $ igor ipmi chassis power --hostname osl01 --state always-off
    policy: always-off
    hostname: osl01
    """

    if not state:
        response = make_api_request('GET', config, '/machines/' + hostname +
                                                   '/chassis/policy')
    else:
        data = json.dumps({'state': state})
        response = make_api_request('POST', config, '/machines/' + hostname +
                                                 '/chassis/policy', data=data)
    ipmi_print(response.json())

## ipmitool sensor list
## ipmitool sensor get
## ipmitool sensor thresh

@ipmi.group()
@click.pass_obj
def sensor(config):
    """Sensors commands"""

@sensor.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.pass_obj
def list(config, hostname, sensor):
    """Display sensor readings.

    Example:

    \b
    $ igor ipmi sensor list --hostname osl01
    Ambient Temp     | 18 degrees C      | ok
    Planar Temp      | disabled          | ns
    CMOS Battery     | 0x00              | ok
    ...
    """

    print 'Fetching all sensor readings, may take a while...'
    response = make_api_request('GET', config, '/machines/' + hostname +
                                               '/sensors')

    for record in response.json()['records']:
        print record

@sensor.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.option('--sensor', prompt=True, multiple=True,
                          help='Sensors to retrieve')
@click.pass_obj
def get(config, hostname, sensor):
    """Display details for the specified sensors.

    Example:

    \b
    $ igor ipmi sensor get --hostname osl01 --sensor 'Ambient Temp' \
                                            --sensor 'Planar Temp'
    sensors:
        sensor_type_(discrete): Critical Interrupt (0x13)
        entity_id: 34.1 (BIOS)
        event_message_control: Per-threshold
        sensor_id: PCIE Fatal Err (0x18)
        sensor_reading: No Reading

        sensor_type_(discrete): Unknown (0xC3) (0xc3)
        entity_id: 34.1 (BIOS)
        event_message_control: Per-threshold
        sensor_id: Fatal IO Error (0x27)
        sensor_reading: No Reading
    """

    print 'Locating sensor records, may take a while...'
    data = json.dumps({'sensors': [{'id': i} for i in sensor]})
    response = make_api_request('POST', config, '/machines/' + hostname +
                                                '/sensors', data=data)

    ipmi_print(response.json(), composite_list=True)

@sensor.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.option('--sensor', prompt=True,
                          help='Sensor to set threshold of')
@click.option('--threshold', prompt=True,
                             help='Threshold setting')
@click.option('--value', prompt=True, type=click.FLOAT, multiple=True,
                         help='Threshold value(s)')
@click.pass_obj
def thresh(config, hostname, sensor, threshold, value):
    """Set thresholds for the specified sensor.

    Example:

    \b
    $ igor ipmi sensor thresh --hostname osl01 --sensor 'Ambient Temp' \
                              --threshold 'ucr' --value 47.0
    message: Locating sensor record 'Ambient Temp'...
    Setting sensor "Ambient Temp" Upper Critical threshold to 47.000

    \b
    $ igor ipmi sensor thresh --hostname osl01 --sensor 'Ambient Temp' \
                              --threshold 'lower' \
                              --value 3.0 --value 3.0 --value 8.0
    message: Locating sensor record 'Ambient Temp'...
    Setting sensor "Ambient Temp" Lower Non-Recoverable threshold to 3.000
    Setting sensor "Ambient Temp" Lower Critical threshold to 3.000
    Setting sensor "Ambient Temp" Lower Non-Critical threshold to 8.000
    """

    data = json.dumps({'threshold': threshold,
                       'values': value})
    response = make_api_request('POST', config, '/machines/' + hostname +
                                                '/sensors/' + quote_plus(sensor)
                                      , data=data)

    ipmi_print(response.json())

## ipmitool lan
## ipmitool lan set
## ipmitool lan alert
## ipmitool lan alert set

@ipmi.group()
@click.pass_obj
def lan(config):
    """LAN channel commands"""

@lan.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.option('--channel', type=click.INT,
                           help='The lan channel number')
@click.pass_obj
def info(config, hostname, channel):
    """Display lan channel information.

    Example:

    \b
    $ igor ipmi lan info --hostname osl01
    auth_type_support: NONE, MD2, MD5, PASSWORD
    snmp_community_string: 4h519bu64
    n_802_1q_vlan_priority: 0
    cipher_suite_priv_max: aaaaaaaaaaaaaaa
    ip_address_source: Static Address
    subnet_mask: 255.255.254.0
    ...
    
    \b
    $ igor ipmi lan info --hostname osl01 --channel 0
    Server response: Invalid channel: 0 (HTTP error 400)

    \b
    $ igor ipmi lan info --hostname osl01 --channel 1
    auth_type_support: NONE, MD2, MD5, PASSWORD
    snmp_community_string: 4h519bu64
    n_802_1q_vlan_priority: 0
    cipher_suite_priv_max: aaaaaaaaaaaaaaa
    ip_address_source: Static Address
    subnet_mask: 255.255.254.0
    ...
    """

    endpoint = '/machines/' + hostname + '/lan'
    if channel is not None:
        endpoint += '/' + str(channel)
    response = make_api_request('GET', config, endpoint)
    ipmi_print(response.json())

@lan.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.option('--channel', prompt=True, type=click.INT,
                           help='The lan channel number')
@click.option('--command', prompt=True,
                           help='The lan command to set')
@click.option('--param', prompt=True,
                         help='The lan command parameter')
@click.pass_obj
def set(config, hostname, channel, command, param):
    """Set lan channel information.

    For a list of valid commands, visit the ipmitool manpage.

    Example:

    \b
    $ igor ipmi lan set --hostname osl01
    Channel: 1
    Command: ipsrc
    Param: static

    auth_type_support: NONE, MD2, MD5, PASSWORD
    snmp_community_string: 4h519bu64
    n_802_1q_vlan_priority: 0
    cipher_suite_priv_max: aaaaaaaaaaaaaaa
    ip_address_source: Static Address
    ...

    \b
    $ igor ipmi lan set --hostname osl01 --channel 1 --command ipsrc \
                        --param static

    auth_type_support: NONE, MD2, MD5, PASSWORD
    snmp_community_string: 4h519bu64
    n_802_1q_vlan_priority: 0
    cipher_suite_priv_max: aaaaaaaaaaaaaaa
    ip_address_source: Static Address
    ...
    """

    data = json.dumps({'command': command, 'param': param})
    response = make_api_request('POST', config, '/machines/' + hostname
                                                + '/lan/' + str(channel),
                                                data=data)
    ipmi_print(response.json())

@lan.group()
@click.pass_obj
def alert(config):
    """LAN alert commands"""

@alert.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.option('--channel', type=click.INT,
                           help='The lan channel number')
@click.pass_obj
def info(config, hostname, channel):
    """Display lan alert information.

    Example:

    \b
    $ igor ipmi lan alert info --hostname osl01
    auth_type_support: NONE, MD2, MD5, PASSWORD
    snmp_community_string: 4h519bu64
    n_802_1q_vlan_priority: 0
    cipher_suite_priv_max: aaaaaaaaaaaaaaa
    ip_address_source: Static Address
    subnet_mask: 255.255.254.0
    ...

    \b
    $ igor ipmi lan alert info --hostname osl01 --channel 0
    Server response: Invalid channel: 0 (HTTP error 400)

    \b
    $ igor ipmi lan alert info --hostname osl01 --channel 1
    auth_type_support: NONE, MD2, MD5, PASSWORD
    snmp_community_string: 4h519bu64
    n_802_1q_vlan_priority: 0
    cipher_suite_priv_max: aaaaaaaaaaaaaaa
    ip_address_source: Static Address
    subnet_mask: 255.255.254.0
    ...
    """

    endpoint = '/machines/' + hostname + '/lan'
    if channel is not None:
        endpoint += '/' + str(channel)
    endpoint += '/alert'
    response = make_api_request('GET', config, endpoint)
    ipmi_print(response.json(), composite_list=True)

@alert.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.option('--channel', prompt=True, type=click.INT,
                           help='The lan channel number')
@click.option('--dest', prompt='Alert destination', type=click.INT,
                        help='The alert destination channel')
@click.option('--command', prompt=True,
                           help='The lan command to set')
@click.option('--param', prompt=True,
                         help='The lan command parameter')
@click.pass_obj
def set(config, hostname, channel, dest, command, param):
    """Set lan alert channel information.

    For a list of valid commands, visit the ipmitool manpage.

    Example:

    \b
    $ igor ipmi lan alert set --hostname osl01
    Channel: 1
    Alert destination: 0
    Command: ipsrc
    Param: static

    alerts:
        retry_interval: 0
        number_of_retries: 0
        alert_gateway: Default
        alert_mac_address: 00:00:00:00:00:00
        alert_acknowledge: Unacknowledged
        alert_ip_address: 0.0.0.0
        alert_destination: 0
        destination_type: PET Trap

        retry_interval: 0
        number_of_retries: 0
        alert_gateway: Default
        alert_mac_address: 00:00:00:00:00:00
        alert_acknowledge: Unacknowledged
        alert_ip_address: 0.0.0.0
        alert_destination: 1
        destination_type: PET Trap
        ...

    \b
    $ igor ipmi lan alert set --hostname osl01 --channel 1 --dest 0 \
                              --command ipsrc --param static

    alerts:
        retry_interval: 0
        number_of_retries: 0
        alert_gateway: Default
        alert_mac_address: 00:00:00:00:00:00
        alert_acknowledge: Unacknowledged
        alert_ip_address: 0.0.0.0
        alert_destination: 0
        destination_type: PET Trap

        retry_interval: 0
        number_of_retries: 0
        alert_gateway: Default
        alert_mac_address: 00:00:00:00:00:00
        alert_acknowledge: Unacknowledged
        alert_ip_address: 0.0.0.0
        alert_destination: 1
        destination_type: PET Trap
        ...
    """

    data = json.dumps({'dest': dest, 'command': command, 'param': param})
    response = make_api_request('POST', config, '/machines/' + hostname
                                                + '/lan/' + str(channel)
                                                + '/alert',
                                                data=data)
    ipmi_print(response.json(), composite_list=True)

@ipmi.group()
@click.pass_obj
def sel(config):
    """System event log commands"""

@sel.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.pass_obj
def info(config, hostname):
    """Display system event log information.

    Example:

    \b
    $ igor ipmi sel info --hostname osl01
    hostname: osl01
    supported_cmds: Reserve
    last_add_time: 1970-01-01 00:00:59
    free_space: 8144
    version:
        compliant: v1.5, v2
        number: 1.5
    entries: 3
    overflow: False
    last_del_time: 2013-05-10 20:14:10
    """

    endpoint = '/machines/' + hostname + '/sel'
    response = make_api_request('GET', config, endpoint)
    ipmi_print(response.json())

@sel.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.option('--time', help='(YYYY-MM-DD hh:mm:ss) Desired SEL clock time.')
@click.pass_obj
def time(config, hostname, time):
    """Display or set the SEL clock time.

    Example:

    \b
    $ igor ipmi sel time --hostname osl01
    hostname: osl01
    time: 2014-07-31 03:38:01

    \b
    $ igor ipmi sel time --time '1990-05-22 23:15:50' --hostname osl01
    hostname: osl01
    time: 1990-05-22 23:15:50
    """

    if not time:
        response = make_api_request('GET', config, '/machines/' + hostname +
                                                   '/sel/time')
    else:
        data = json.dumps({'time': time})
        response = make_api_request('POST', config, '/machines/' + hostname +
                                                 '/sel/time', data=data)
    ipmi_print(response.json())

@sel.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.option('--extended', is_flag=True, default=False,
                            help='Display the extended SEL record list.')
@click.pass_obj
def list(config, hostname, extended):
    """Display the SEL record list.

    Example:

    \b
    $ igor ipmi sel list --hostname osl01
    1 | 07/31/2014 | 05:25:23 | Event Logging Disabled #0x72 | Log area reset
    \b
    $ igor ipmi sel list --hostname osl01 --extended
    1 | 07/31/2014 | 05:25:23 | Event Logging Disabled #0x72 | Log area reset
    """

    response = make_api_request('GET', config, '/machines/' + hostname +
                                               '/sel/records?extended=' +
                                               str(extended))
    for record in response.json()['records']:
        print record

@sel.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.pass_obj
def clear(config, hostname):
    """Clear the SEL record list.

    Example:

    \b
    $ igor ipmi sel clear --hostname osl01
    1 | 07/31/2014 | 05:25:23 | Event Logging Disabled #0x72 | Log area
    """

    click.confirm('Clear all SEL records for ' + hostname + '?', abort=True)

    response = make_api_request('DELETE', config, '/machines/' + hostname +
                                                  '/sel/records')
    ipmi_print(response.json())

@sel.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.option('--id', prompt=True, type=click.INT, multiple=True,
                      help='The SEL record IDs to get')
@click.pass_obj
def get(config, hostname, id):
    """View the SEL entries for the provided record IDs. Unavailable
    record IDs are not displayed.

    Example:

    \b
    $ igor ipmi sel get --hostname osl01 --id 1 --id 2
    1 | 07/31/2014 | 05:25:23 | Event Logging Disabled #0x72 | Log area
    """

    data = json.dumps({'records': [{'id': i} for i in id]})
    response = make_api_request('POST', config, '/machines/' + hostname +
                                                '/sel/records', data=data)
    for record in response.json()['records']:
        print record

@sel.command()
@click.option('--hostname', prompt=True,
                            help='The short hostname for this machine.')
@click.option('--id', prompt=True, type=click.INT,
                      help='The SEL record ID to delete')
@click.pass_obj
def get(config, hostname, id):
    """Delete the SEL entry for the provided record ID.

    Example:

    \b
    $ igor ipmi sel get --hostname osl01 --id 1
    hostname: osl01
    message: Deleted record 1
    """

    response = make_api_request('DELETE', config, '/machines/' + hostname +
                                                  '/sel/records/' + id)
    ipmi_print(response.json())
