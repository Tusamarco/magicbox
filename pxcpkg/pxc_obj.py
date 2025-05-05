# object module defining all mysql related class tp PXC
#import mysqlsh
import time
import sys
import importlib

from typing import Dict

from common import utils_mb
from magicbox.mysqlpkg.mysql_obj import Mysql_Node # mysqlpkg.mysql_obj import Mysql_Node

class PXC_Node(Mysql_Node):
    """
    PXC_Node
    
    PCX_Node class extends the Mysql_Node class

    Class implement methods to manage the specifics of a PXC node
    PXC ip and port can be different from the superclass given they reflects the
    information coming from wsrep_node_incoming_address. 
    """
    def __init__(self, uri=False):
        super().__init__(uri)
        self.wsrep_provider    = Dict[str,str]
        self.parse_provider()

        try:
            if self.variables["wsrep_node_incoming_address"] != None and \
                len(self.variables["wsrep_node_incoming_address"]) >0:
                    
                if self.variables["wsrep_node_incoming_address"].index(":") > 0:
                    pxc_ip:str = self.variables["wsrep_node_incoming_address"][:self.variables["wsrep_node_incoming_address"].index(":") -1 ]
                    pxc_port   = self.variables["wsrep_node_incoming_address"][self.variables["wsrep_node_incoming_address"].index(":") +1: ]
                else:
                    pxc_ip:str = self.variables["wsrep_node_incoming_address"]
                    pxc_port = 3306

            cluster_name:str = self.variables["wsrep_cluster_name"]
            pxc_node_name:str = self.variables["wsrep_node_name"]

        except:
            # sys.tracebacklimit = 1
            raise KeyError("Wrong Key name or wrong resource parsed variables: wsrep_node_incoming_address")
                                                                      
        
        
    def parse_provider(self):
        if self.variables !=None \
            and len(self.variables) > 0:
                self.wsrep_provider = utils_mb.parse_label_value_pairs(self.variables["wsrep_provider_options"], ";")
#                print(self.wsrep_provider)

class PXC_Cluster():
    """
    PXC_Cluster 
    
    PXC_Cluster, represent the cluster and provide information about it and methods to manage it 
    
    """
    def __init__(self, pxc_node:PXC_Node):
        if pxc_node.cluster_name != None and len(pxc_node.cluster_name) > 0:
            self.name:str = pxc_node.cluster_name
        else:
            raise Pxc_Exception("Invalid Cluster name in PXC_node")
        
        
class Pxc_Exception(Exception):
    pass