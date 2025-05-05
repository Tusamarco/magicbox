"""
PXC Processor module.

PXC Processor module contains classes and methods related to PXC cluster actions.
Classes:
 - PXC_Node 
 - PXC_cluster
 -Pxc_processor
"""

# import mysqlsh
import time
import sys
import importlib


from typing import Dict
# from mysqlsh import mysql
# shell = mysqlsh.globals.shell

from magicbox.pxcpkg import pxc_obj
from pxcpkg.pxc_obj import PXC_Node
from pxcpkg.pxc_obj import PXC_Cluster

importlib.reload(pxc_obj)

class Pxc_processor:
    """
    PXC Processor class 

    PXC Processor class, implements methods to manage the PXC Nodes and the PXC cluster

    Args:
        Require a valid URI to connect to a PXC Node
        Valid URI form: <user>:[<password>]@<ip>:[<port>]
    Returns PXC Processor objects with One pxc Node initialized 

    """
    def __init__(self,uri=False):
        self.user = None
        self.ip = None
        self.port = None
        self.members: Dict[str,PXC_Node]
        self.version = None
        self.use_ssl = 0
        self.uri = uri
        self.main_node = PXC_Node(uri)

    def get_pxc_cluster(self):
        """
        This method will read the main_node to identify the other nodes in the cluster
        to discover which nodes it will use the wsrep_incoming_addresseses and assign it to pxc_ip/port
        It will also create the pxc cluster object filled with all the information
        Args: 
            - self
        Raises:
            - exception for:
                missing pxc_node
        
        Returns         
            PXC_cluster
        """
        if self.main_node != None:
            pass
