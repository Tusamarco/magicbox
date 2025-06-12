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
        cluster.add_cluster_to_proxysql(hgid,False)
        cluster.reconcile_cluster(hgid)

        # processor.close_connections()
        # json_text='''
        # {"cluster":{"nodes":[{"id": {"hg_id": 8200, "server_ip": "10.211.55.5", "server_port": 3307}, "gtid_port": "0", "status": "ONLINE",
        #  "weight": "1000", "compression": "0", "max_connections": "2000", "max_replication_lag": "0", "use_ssl": "1",
        #  "max_latency_ms": "0", "comment": ""},
        # {"id":{"hg_id": 8201, "server_ip": "10.211.55.5", "server_port": 3307}, "gtid_port": "0", "status": "ONLINE",
        # "weight": "997", "compression": "0", "max_connections": "2000", "max_replication_lag": "0", "use_ssl": "1",
        # "max_latency_ms": "0", "comment": ""}]}}
        # '''

        json_text = '''
         {"cluster":{"nodes":[{"id": {"hg_id": 8200, "server_ip": "10.211.55.5", "server_port": 3307},
          "weight": "1000", "compression": "0", "max_connections": "2000", "max_replication_lag": "0", "use_ssl": "1",
          "max_latency_ms": "0", "comment": "Primary Writer"},
         {"id":{"hg_id": 8201, "server_ip": "10.211.55.5", "server_port": 3307}, "gtid_port": "0", "status": "ONLINE",
         "weight": "997", "compression": "0", "max_connections": "2000", "max_replication_lag": "0", "use_ssl": "1",
         "max_latency_ms": "0", "comment": "Not Primary Reader"}]}}
         '''
        cluster.proxysql_node.config_nodes(json_text)

        hgsid:list = cluster.get_hostgroup_ids_by_handler_support(200)
        json_request=[]
        for hgid in hgsid:
            json_request.append(hgid.hg_id)

        print(cluster.proxysql_node.get_json_by_hostgroups(json_request))
        pxc = cluster.get_node_by_pxc_name("node1")
        backend = cluster.get_Proxysql_backend_by_pxc_name("node2",201)

        print(pxc.pxc_node_name + " " + pxc.pxc_ip + ":"+ pxc.pxc_port)
        if backend is not None:
            print(backend.id.hg_id + " " + backend.id.server_ip + ":" + backend.id.server_port)

        cluster.close_connections()