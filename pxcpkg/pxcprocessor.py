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
import common.dbtools as dbtools

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
        self.cluster:PXC_Cluster = None

    def set_pxc_cluster(self,uri):
        """
        This method will read the main_node to identify the other nodes in the cluster
        
        Args: 
            - self
            - uri
                if a valid URI to connect to the MySQL node is pass and the main ode is not present 
                then the main node is created
                Valid URI form: <user>:[<password>]@<ip>:[<port>]

        Raises:
            - exception for:
                missing pxc_node
                pxc_node not in primary state
        
        Returns         
            PXC_cluster
        """
        if self.main_node == None and dbtools.validate_uri(uri):
            self.__init__(uri)
            
        self.cluster = PXC_Cluster(self.main_node)
                           
    def get_pxc_cluster(self):
        """
        Return the identified PXC cluster

        Returns:
            PXC Cluster: The cluster identified reading the PXC node we connect to
        """
        if self.cluster == None:
            return None
        else:
            return self.cluster