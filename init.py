# init.py
# -------
import importlib

import magicbox

try:
    import mysqlsh
    from mysqlsh.plugin_manager import plugin, plugin_function
except:
    pass



import logging

# Configure basic logging (console output)
logging.basicConfig(
    level=logging.DEBUG,  # Minimum level to log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    # format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    format='[%(levelname)s] - %(message)s',  # Log format
    handlers=[logging.StreamHandler()]  # Log to console
)


@plugin
class Magicbox:
    """
    The magicbox plugin 

    The magicbox plugin is going to bring you joy and candies
    """
    # def __init__(self):
    #     pass
    #
    # def createPxcProcessor(uri):
    #     """
    #     Create the PXCProcessor Object.
    #
    #     Args:
    #         uri (string): Connection uri to any PXC node part of the cluster.
    #
    #     Returns:
    #         The newly created PXC Processor object
    #     """
    #     processor = pxcprocessor.Pxc_processor(uri)
    #     # return processor
    #     return{
    #         'setPXCcluster': lambda uri="": processor.set_pxc_cluster(uri),
    #         'getPXCcluster': lambda: processor.get_pxc_cluster(),
    #         'refreshPXCcluster': lambda uri="": processor.refresh_pxc_cluster(uri),
    #         'setProxySQL': lambda uri="": processor.set_proxysql_node(uri),
    #         'getProxySQL': lambda: processor.get_proxy_sql_node(),
    #
    #     }


import debugpy
debugpy.listen(("localhost", 5678))
print("Waiting for debugger attach...")
debugpy.wait_for_client()
print("Debugger attached.")



# @plugin_function("magicbox.helloWorld")
# def hello_world():
#     """
#     Simple function that prints "Hello world!"

#     Just say Hello World

#     Returns:
#         Nothing
#     """
#     print("Hello world!")
#     print("Just joking!")

# @plugin_function("magicbox.showSchemas")
# def show_schemas(session=None):
#     """
#     Lists all database schemas

#     Sample function that works either with a session passed as parameter or
#     with the global session of the MySQL Shell.

#     Args:
#         session (object): The optional session object used to query the
#             database. If omitted the MySQL Shell's current session will be used.

#     Returns:
#         Nothing
#     """
#     if session is None:
#         shell = mysqlsh.globals.shell
#         session = shell.get_session()
#         if session is None:
#             print("No session specified. Either pass a session object to this "
#                 "function or connect the shell to a database")
#             return
#     if session is not None: 
#         r = session.run_sql("show schemas")
#         shell.dump_rows(r)

# from proxysqlpkg import proxysql

@plugin_function("magicbox.createProxysql")
def createProxy(uri):
    """
    Create the ProxySQL Object.

    Args:
        uri (string): Connection uri to ProxySQL's admin interface.

    Returns:
        The newly created ProxySQL object
    """
    my_proxy = proxysql.ProxySQL(uri)
    return {
         'status': lambda loop=False: my_proxy.get_status(loop),
         'configure': lambda: my_proxy.configure(),
         'hosts': lambda: my_proxy.get_hosts(),
         'version': lambda: my_proxy.get_version(),
         'hostgroups': lambda: my_proxy.get_hostgroups(),
         'getUsers': lambda hostgroup="": my_proxy.get_user_hostgroup(hostgroup),
         'setUser': lambda hostgroup="", user="", password=False: my_proxy.set_user_hostgroup(hostgroup,user,password),
         'importUsers': lambda hostgroup="", user_search="": my_proxy.import_users(hostgroup, user_search),
         'setUserHostgroup': lambda hostgroup="", user_search="": my_proxy.set_host_group(hostgroup, user_search)
    }
    
    
@plugin_function("magicbox.create_pxc_processor")
def create_pxc_processor(uri):
    """
    Create the PXCProcessor Object.

    Args:
        uri (string): Connection uri to any PXC node part of the cluster.

    Returns:
        The newly created PXC Processor object
    """
    processor = pxcprocessor.Pxc_processor(uri)
    # return processor
    return{
        'setPXCcluster': lambda uri="": processor.set_pxc_cluster(uri),
        'getPXCcluster': lambda: processor.get_pxc_cluster(),
        'refreshPXCcluster': lambda uri="": processor.refresh_pxc_cluster(uri),
        'setProxySQL': lambda uri="": processor.set_proxysql_node(uri),
        'getProxySQL': lambda: processor.get_proxy_sql_node(),

    }

from magicbox.magicbox import MagicC
@plugin_function("magicbox.checkAll")
def check_all():
    MagicC.check_all()
    
@plugin_function("magicbox.checkMonitor")
def check_monitor():
    MagicC.test_monitor()
    
    