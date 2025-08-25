import logging

# We have different entry points to load modules.
# When inside MySQL Shell we need full path
try:
    from monitorpkg.monitor import Monitor
    from proxysqlpkg.proxysql_obj import ProxySQLCluster, ProxySQLNode, ProxyMysqlDataNode
    from pxcpkg.pxc_obj import PXCCluster
except ImportError as e:
    # print(f"An error occurred: {e}")
    from magicbox.monitorpkg.monitor import Monitor
    from magicbox.proxysqlpkg.proxysql_obj import ProxySQLCluster, ProxySQLNode, ProxyMysqlDataNode
    from magicbox.pxcpkg.pxc_obj import PXCCluster
    pass

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


    @staticmethod
    def test_monitor(refresh_rate = 1):
        hgid:int = 100
        # processor = MagicC.create_pxc_processor("dba:dba@192.168.4.205:3306")
        #cluster: PXCCluster = PXCCluster.connect_cluster("dba:dba@10.211.55.5:3307",["10.211.55.5:3307","10.211.55.5:3308","10.211.55.5:3309"])


        cluster: PXCCluster = PXCCluster.connect_cluster("dba:dba@192.168.4.205:3306",
                                                         ["192.168.4.231","192.168.4.205","192.168.4.21"])
        cluster.number_of_writers = 1
        cluster.connect_proxysql_node("cluster1:clusterpass@192.168.4.191:6032")
        cluster.proxysql_node.set_current_cluster_writer_id(hgid)

        monitor = Monitor(cluster.proxysql_node)
        monitor.start(refresh_rate)
        # monitor.stop()

    @staticmethod
    def check_all():
        hgid:int = 200
        # processor = MagicC.create_pxc_processor("dba:dba@192.168.4.205:3306")
        #cluster: PXCCluster = PXCCluster.connect_cluster("dba:dba@10.211.55.5:3307",["10.211.55.5:3307","10.211.55.5:3308","10.211.55.5:3309"])


        cluster: PXCCluster = PXCCluster.connect_cluster("dba:dba@192.168.4.205:3306",
                                                         ["192.168.4.231","192.168.4.205","192.168.4.21"])
        cluster.set_handler(ProxyMysqlDataNode.HANDLER_INTERNAL)
        cluster.number_of_writers = 1

        # cluster.discover_nodes(["192.168.4.231","192.168.4.205","192.168.4.21"])
        # cluster:PXCCluster = processor.set_pxc_cluster(None,["192.168.4.231","192.168.4.205","192.168.4.21"])
        # cluster.connect_proxysql_node("cluster1:clusterpass@10.211.55.5:6032")
        cluster.connect_proxysql_node("cluster1:clusterpass@192.168.4.191:6032")
        # proxy = processor.set_proxysql_node("cluster1:clusterpass@192.168.4.191:6032")
        cluster.add_cluster_to_proxysql(hgid,False)

        cluster.reconcile_cluster(hgid)

        cluster.proxysql_node.delete_cluster(None,True)

        cluster.number_of_writers = 2

        cluster.add_cluster_to_proxysql(hgid,False)

        cluster.put_cluster_offline()

        cluster.put_cluster_onine()
        # processor.close_connections()

        # json_text = '''
        #  {"cluster":{"nodes":[{"id": {"hg_id": 8200, "server_ip": "10.211.55.5", "server_port": 3307},
        #   "weight": "1000", "compression": "0", "max_connections": "2000", "max_replication_lag": "0", "use_ssl": "1",
        #   "max_latency_ms": "0", "comment": "Primary Writer"},
        #  {"id":{"hg_id": 8201, "server_ip": "10.211.55.5", "server_port": 3307}, "gtid_port": "0", "status": "ONLINE",
        #  "weight": "997", "compression": "0", "max_connections": "2000", "max_replication_lag": "0", "use_ssl": "1",
        #  "max_latency_ms": "0", "comment": "Not Primary Reader"}]}}
        #  '''
        json_text = '''
         {"cluster":{"nodes":[{"id": {"hg_id": 8200, "server_ip": "192.168.4.205", "server_port": 3306},
          "weight": "1000", "compression": "0", "max_connections": "2000", "max_replication_lag": "0", "use_ssl": "1",
          "max_latency_ms": "0", "comment": "Primary Writer"},
         {"id":{"hg_id": 8201, "server_ip": "192.168.4.205", "server_port": 3306}, "gtid_port": "0", "status": "ONLINE",
         "weight": "997", "compression": "0", "max_connections": "2000", "max_replication_lag": "0", "use_ssl": "1",
         "max_latency_ms": "0", "comment": "Not Primary Reader"}
         ]}}
         '''

        modified_nodes =  cluster.proxysql_node.config_nodes(json_text)
        cluster.proxysql_node.update_nodes(modified_nodes,True)

        hgsid:list = cluster.get_hostgroup_ids_by_handler_support(hgid)
        json_request=[]
        for hgid_obj in hgsid:
            json_request.append(hgid_obj.hg_id)

        print(cluster.proxysql_node.get_json_by_hostgroups(json_request))
        pxc = cluster.get_node_by_pxc_name("node1")

        backend = cluster.get_Proxysql_backend_by_pxc_name("node2",hgid + 1)

        print(pxc.pxc_node_name + " " + pxc.pxc_ip + ":"+ pxc.pxc_port)
        if backend is not None:
            print(str(backend.id.hg_id) + " " + backend.id.server_ip + ":" + str(backend.id.server_port))
            print(backend.serialize_proxysql_node())


        cluster.proxysql_node.setup_cluster_manager()
        cluster.proxysql_node.activate_cluster_manager()
        cluster.proxysql_node.deactivate_cluster_manager()
        cluster.proxysql_node.delete_cluster_manager()

        cluster.proxysql_node.delete_cluster(None,True)


        cluster.close_connections()

