import pytest
from app.utils.nmap_parser import parse_nmap_xml
from app.models import HostInfo, PortInfo
from xml.etree import ElementTree as ET


def test_parse_single_host():
    """测试解析单个主机的XML"""
    xml_content = '''<?xml version="1.0"?>
<nmaprun>
  <host>
    <address addr="192.168.1.1" addrtype="ipv4"/>
    <status state="up"/>
    <os>
      <osmatch name="Linux 4.15 - 5.6" accuracy="100"/>
    </os>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh" product="OpenSSH" version="8.0"/>
      </port>
    </ports>
    <hostnames>
      <hostname name="router" type="PTR"/>
    </hostnames>
  </host>
</nmaprun>'''

    result = parse_nmap_xml(xml_content)
    assert len(result) == 1
    host = result[0]
    assert host.ip == "192.168.1.1"
    assert host.status == "up"
    assert host.os == "Linux 4.15 - 5.6"
    assert host.hostname == "router"
    assert len(host.ports) == 1
    assert host.ports[0].port == 22
    assert host.ports[0].protocol == "tcp"
    assert host.ports[0].service == "ssh"
    assert host.ports[0].product == "OpenSSH"


def test_parse_multiple_hosts():
    """测试解析多个主机的XML"""
    xml_content = '''<?xml version="1.0"?>
<nmaprun>
  <host>
    <address addr="192.168.1.1" addrtype="ipv4"/>
    <status state="up"/>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh"/>
      </port>
    </ports>
  </host>
  <host>
    <address addr="192.168.1.2" addrtype="ipv4"/>
    <status state="down"/>
  </host>
</nmaprun>'''

    result = parse_nmap_xml(xml_content)
    assert len(result) == 2
    assert result[0].ip == "192.168.1.1"
    assert result[0].status == "up"
    assert result[1].ip == "192.168.1.2"
    assert result[1].status == "down"


def test_parse_empty_xml():
    """测试解析空XML"""
    xml_content = '''<?xml version="1.0"?>
<nmaprun>
</nmaprun>'''

    result = parse_nmap_xml(xml_content)
    assert len(result) == 0


def test_parse_with_vendor_info():
    """测试解析包含厂商信息的XML"""
    xml_content = '''<?xml version="1.0"?>
<nmaprun>
  <host>
    <address addr="192.168.1.1" addrtype="ipv4"/>
    <address addr="AA:BB:CC:DD:EE:FF" addrtype="mac" vendor="Cisco"/>
    <status state="up"/>
    <ports>
      <port protocol="tcp" portid="80">
        <state state="open"/>
        <service name="http" product="Apache" version="2.4"/>
      </port>
    </ports>
  </host>
</nmaprun>'''

    result = parse_nmap_xml(xml_content)
    assert len(result) == 1
    host = result[0]
    assert host.ip == "192.168.1.1"
    assert host.vendor == "Cisco"  # Should extract vendor from mac address
    assert len(host.ports) == 1
    assert host.ports[0].port == 80
    assert host.ports[0].service == "http"
    assert host.ports[0].product == "Apache"