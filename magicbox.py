import logging


import importlib

from pxcpkg.pxc_obj import PXCCluster

class MagicC:
    """
    The magicbox class

    The magicbox Class is going to bring you joy and candies
    """
    import logging

    # Configure basic logging (console output)
    logging.basicConfig(
        level=logging.DEBUG,  # Minimum level to log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        # format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
        format=' [%(levelname)s] - %(message)s',  # Log format
        handlers=[logging.StreamHandler()]  # Log to console
    )

    def __init__(self):
        logging.warning("magicbox")
        # return  self
        # pass
        # self.pxcprocessor = pxcprocessor.PXCProcessor()

    def create_pxc_processor(uri):
        """
        Create the PXCProcessor Object.

        Args:
            uri (string): Connection uri to any PXC node part of the cluster.

        Returns:
            The newly created PXC Processor object
        """
        processor = pxcprocessor.Pxc_processor(uri)
        return processor
        # return{
        #     'setPXCcluster': lambda uri="": processor.set_pxc_cluster(uri),
        #     'getPXCcluster': lambda: processor.get_pxc_cluster(),
        #     'refreshPXCcluster': lambda uri="": processor.refresh_pxc_cluster(uri),
        #     'setProxySQL': lambda uri="": processor.set_proxysql_node(uri),
        #     'getProxySQL': lambda: processor.get_proxy_sql_node(),
        #
        # }

    @staticmethod
    def check_all():
        hgid = 200
        # processor = MagicC.create_pxc_processor("dba:dba@192.168.4.205:3306")
        cluster: PXCCluster = PXCCluster.connect_cluster("dba:dba@10.211.55.5:3307",["10.211.55.5:3307","10.211.55.5:3308","10.211.55.5:3309"])
        # cluster.discover_nodes(["192.168.4.231","192.168.4.205","192.168.4.21"])
        # cluster:PXCCluster = processor.set_pxc_cluster(None,["192.168.4.231","192.168.4.205","192.168.4.21"])
        cluster.connect_proxysql_node("cluster1:clusterpass@10.211.55.5:6032")
        # proxy = processor.set_proxysql_node("cluster1:clusterpass@192.168.4.191:6032")
        cluster.add_nodes_to_proxysql(hgid,False)
        cluster.reconcile_cluster(hgid)
        cluster.close_connections()
        # processor.close_connections()