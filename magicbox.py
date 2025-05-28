from pxcpkg import pxcprocessor

import importlib
importlib.reload(pxcprocessor)

class MagicC:
    """
    The magicbox class

    The magicbox Class is going to bring you joy and candies
    """
    def __init__(self):
        print("magicbox")
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