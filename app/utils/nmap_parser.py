from typing import List
from xml.etree import ElementTree as ET
from app.models import HostInfo, PortInfo


def parse_nmap_xml(xml_content: str) -> List[HostInfo]:
    """
    解析nmap输出的XML内容

    Args:
        xml_content: nmap输出的XML字符串

    Returns:
        解析得到的主机信息列表
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        # 如果无法解析XML，则返回空列表
        return []

    hosts = []

    # 查找所有host节点
    for host_elem in root.findall('host'):
        # 初始化主机信息
        host_info = HostInfo(
            ip="",
            status="",
            os="",
            vendor="",
            hostname="",
            ports=[]
        )

        # 解析IP地址
        for addr_elem in host_elem.findall('address'):
            addrtype = addr_elem.get('addrtype')
            if addrtype == 'ipv4':
                host_info.ip = addr_elem.get('addr', '')
            elif addrtype == 'mac':
                vendor = addr_elem.get('vendor', '')
                if vendor:
                    host_info.vendor = vendor

        # 解析状态
        status_elem = host_elem.find('status')
        if status_elem is not None:
            host_info.status = status_elem.get('state', '')

        # 解析操作系统
        os_elem = host_elem.find('os')
        if os_elem is not None:
            osmatch_elem = os_elem.find('osmatch')
            if osmatch_elem is not None:
                host_info.os = osmatch_elem.get('name', '')

        # 解析主机名
        hostnames_elem = host_elem.find('hostnames')
        if hostnames_elem is not None:
            hostname_elem = hostnames_elem.find('hostname')
            if hostname_elem is not None:
                host_info.hostname = hostname_elem.get('name', '')

        # 解析端口信息
        ports_elem = host_elem.find('ports')
        if ports_elem is not None:
            for port_elem in ports_elem.findall('port'):
                port_state = port_elem.find('state')
                if port_state is not None and port_state.get('state') == 'open':
                    service_elem = port_elem.find('service')

                    port_info = PortInfo(
                        port=int(port_elem.get('portid', 0)),
                        protocol=port_elem.get('protocol', ''),
                        service=service_elem.get('name', '') if service_elem is not None else '',
                        product=service_elem.get('product', '') if service_elem is not None else ''
                    )

                    host_info.ports.append(port_info)

        hosts.append(host_info)

    return hosts