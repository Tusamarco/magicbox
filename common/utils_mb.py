"""
_summary_
Module collecting useful common functions

"""
import ipaddress
import socket
import re
from ipaddress import ip_address

def is_same_c_network(ip1, ip2):
    """
    Check if two IP addresses belong to the same Class C network.
    
    Args:
        ip1 (str): First IP address
        ip2 (str): Second IP address
    
    Returns:
        bool: True if both IPs are in the same Class C network, False otherwise
    """
    try:
        # Parse the IP addresses
        ip1_obj = ipaddress.IPv4Address(ip1)
        ip2_obj = ipaddress.IPv4Address(ip2)
        
        # Get the network portion for Class C (first 3 octets)
        network1 = ipaddress.IPv4Network(f"{ip1_obj}/24", strict=False)
        network2 = ipaddress.IPv4Network(f"{ip2_obj}/24", strict=False)
        
        return network1 == network2
    except ValueError:
        # Handle invalid IP addresses
        return False

def is_valid_ip(ip_str):
    """
    Check if the given string is a valid IPv4 or IPv6 address.
    
    Args:
        ip_str (str): String to check for valid IP address format
    
    Returns:
        bool: True if valid IP, False otherwise
    """
    try:
        # Try to create an IPv4 or IPv6 address object
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False
    
    

# def is_valid_dns_and_resolves(dns_name):
#     """
#     Check if a DNS name is valid and resolves to a valid IP address.
    
#     Args:
#         dns_name (str): The DNS name to validate and resolve
        
#     Returns:
#         tuple: (is_valid: bool, ip_address: str or None)
#                is_valid indicates if DNS is valid and resolves
#                ip_address contains the first resolved IP if valid, None otherwise
#     """
#     # First check basic DNS name format validity
#     if not re.match(
#         r'^([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$', 
#         dns_name
#     ):
#         return (False, None)
    
#     try:
#         # Perform DNS resolution
#         ips = socket.getaddrinfo(dns_name, None)
#         if not ips:
#             return (False, None)
        
#         # Extract the first IP address (can be IPv4 or IPv6)
#         first_ip = ips[0][4][0]
        
#         # Validate it's a proper IP
#         ip_address(first_ip)  # Will raise ValueError if invalid
#         return (True, first_ip)
        
#     except (socket.gaierror, ValueError, UnicodeError):
#         # DNS resolution failed or IP is invalid
#         return (False, None)

import socket
import re
from ipaddress import ip_address, IPv4Address, IPv6Address

def validate_and_check_connection(address, timeout=2):
    """
    Check if an address is a valid IP or DNS name and if it can establish a connection.
    
    Args:
        address (str): IP address or DNS name to validate
        timeout (int): Connection timeout in seconds (default: 2)
        
    Returns:
        dict: {
            'valid': bool,
            'type': 'ipv4'|'ipv6'|'dns'|None,
            'resolved_ip': str or None,
            'reachable': bool,
            'ports_reachable': dict,
            'error': str or None
        }
    """
    result = {
        'valid': False,
        'type': None,
        'resolved_ip': None,
        'reachable': False,
        'ports_reachable': {},
        'error': None
    }
    
    # Common ports to test (HTTP, HTTPS)
    # test_ports = [80, 443]
    
    try:
        # Check if it's an IP address first
        try:
            ip = ip_address(address)
            result['valid'] = True
            result['resolved_ip'] = address
            if isinstance(ip, IPv4Address):
                result['type'] = 'ipv4'
            else:
                result['type'] = 'ipv6'
        except ValueError:
            # Not an IP, check if it's a valid DNS name
            if not re.match(
                r'^([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$',
                address
            ):
                result['error'] = "Invalid DNS name format"
                return result
            
            try:
                # Resolve DNS
                ips = socket.getaddrinfo(address, None)
                if not ips:
                    result['error'] = "DNS resolution failed"
                    return result
                
                first_ip = ips[0][4][0]
                ip_address(first_ip)  # Validate resolved IP
                result['valid'] = True
                result['type'] = 'dns'
                result['resolved_ip'] = first_ip
            except (socket.gaierror, ValueError) as e:
                result['error'] = f"DNS resolution error: {str(e)}"
                return result
        
        # # If valid, check connection to test ports
        # if result['valid']:
        #     target_ip = result['resolved_ip']
        #     for port in test_ports:
        #         try:
        #             sock = socket.create_connection((target_ip, port), timeout=timeout)
        #             sock.close()
        #             result['ports_reachable'][port] = True
        #             result['reachable'] = True
        #         except (socket.timeout, socket.error):
        #             result['ports_reachable'][port] = False
            
        #     # If none of the ports worked, set general reachable to False
        #     if not any(result['ports_reachable'].values()):
        #         result['reachable'] = False
                
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
    
    return result

