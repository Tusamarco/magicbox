"""
PXC Processor module.

PXC Processor module contains classes and methods related to PXC cluster actions.
Classes:
 - PXC_Node 
 - PXC_cluster
 - Pxc_processor
"""

# import mysqlsh
import time
import sys
import importlib


from typing import Dict
# from mysqlsh import mysql
# shell = mysqlsh.globals.shell

try:
    from pxcpkg import pxc_obj
except:
    pass

from pxcpkg.pxc_obj import PXC_Node
from pxcpkg.pxc_obj import PXC_Cluster
from proxysqlpkg.proxysql_obj import ProxySQL_Node
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
        self.proxysql_node:ProxySQL_Node = None

    def set_pxc_cluster(self,uri=None):
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
        # Only if self.cluster is None otherwise ignore 
        if self.cluster is None or len(self.cluster) == 0 :
            # We also check the uri if is different
            # We close the connection on Main Node and rebuild the processor based on the new uri
            # If uri is not valid we do not reset the object and raise an error
            try:
                if not len(uri) == 0 and not uri == self.uri and dbtools.validate_uri(uri):
                    self.uri = uri
                    self.main_node.close_connection
                    self.main_node = None
                else:
                    print("The uri: "  + uri + " does not resolve correctly. Will use the Main Node one: " +self.uri)
            finally:
                if dbtools.validate_uri(self.uri):
                    if self.main_node is not None:
                        self.main_node.close_connection()
                        self.main_node = None
                        
                    self.__init__(self.uri)
                
            self.cluster = PXC_Cluster(self.main_node)
            return self.get_pxc_cluster()
        else:
            print("Cluster " + self.cluster.name + " is already define and filled, if you want to modify it use refreshPxcCluster method")
            return self.get_pxc_cluster()
        
                           
    def get_pxc_cluster(self):
        """
        Return the identified PXC cluster

        Returns:
            PXC Cluster: The cluster identified reading the PXC node we connect to
        """
        if self.cluster is None:
            return None
        else:
            return self.cluster
        
    def refresh_pxc_cluster(self,uri):
        """
        Refresh action force the given cluster to close all conenctions to the nodes
        Then to reopen them pointing to the given uri if given, otherwise the previously assigned uri will be used

        Args:
            uri (_type_): Require a well form uri to connect "user:[pass]@host:port" 
                          If Password is not in it will ask it interactively 

        Returns:
            PXC_cluster
        """
        if self.cluster is not None and len(self.cluster) > 0 :
            self.cluster.close_all()
            return self.set_pxc_cluster(uri)
        else:
            if self.cluster is None:
                print("Cluster not initialized, nothing to refresh, use processor.setPXCcluster() first")
            else:    
                print(self.cluster.name +" has no nodes, nothing to refresh")

    def set_proxysql_node(self,uri=None):
        """
        This method will add a proxysql node to the processor
        Then we can use this node to setup/manage the PXC cluster
        
        Args: 
            - self
            - uri
                if a valid URI to connect to the MySQL node is pass and the main ode is not present 
                then the main node is created
                Valid URI form: <user>:[<password>]@<ip>:[<port>]

        Raises:
            - exception for:
                missing proxysql node

        
        Returns         
            proxysql node
            or None if invalid uri
        """
        if dbtools.validate_uri(uri):
            self.proxysql_node = ProxySQL_Node(uri)
            return self.get_proxysql_node()
        else:
            return None
                           
    def get_proxysql_node(self):
        """
        Return the identified PXC cluster

        Returns:
            PXC Cluster: The cluster identified reading the PXC node we connect to
        """
        if self.proxysql_node is None:
            return None
        else:
            return self.proxysql_node