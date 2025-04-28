import mysqlsh
import time
import sys
import importlib

from typing import Dict
from mysqlsh import mysql
shell = mysqlsh.globals.shell

from mysqlpkg.mysql_obj import Mysql_Node

# importlib.reload(Mysql_Node)

class PXC_Node(Mysql_Node):
    def __init__(self, uri=False):
        super().__init__(uri)
        self.wsrep_provider    = Dict[str,str]
        

class PxcProcessor:
    def __init__(self,uri=False):
        self.user = None
        self.ip = None
        self.port = None
        self.members = Dict[str,PXC_Node]
        self.version = None
        self.use_ssl = 0
        self.uri = uri
        self.OperatorNode = PXC_Node(uri)


