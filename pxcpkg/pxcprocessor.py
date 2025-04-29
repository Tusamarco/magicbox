"""
PXC Processor module.

PXC Processor module contains classes and methods related to PXC cluster actions.
Classes:
 - PXC_Node 
 - PXC_CLuster
 -Pxc_processor
"""

# import mysqlsh
import time
import sys
import importlib

from typing import Dict
# from mysqlsh import mysql
# shell = mysqlsh.globals.shell

from magicbox.mysqlpkg.mysql_obj import Mysql_Node # mysqlpkg.mysql_obj import Mysql_Node

# importlib.reload(Mysql_Node)

class PXC_Node(Mysql_Node):
    """
    PCX_Node class extends the Mysql_Node class

    Class implement methods to manage the specifics of a PXC node
    """
    def __init__(self, uri=False):
        super().__init__(uri)
        self.wsrep_provider    = Dict[str,str]
        
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
        self.OperatorNode = PXC_Node(uri)


