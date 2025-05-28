# What is this?


## when using without MySQL shell
from magicbox import MagicC

## Commands

create initial processor:
```python
processor = magicbox.create_pxc_processor("dba:dba@192.168.4.205:3306")
```
Create Cluster inside processor"
```python
cluster = processor.setPXCcluster()
```

Create ProxySQL inside processor:
```python
proxy = processor.setProxySQL("cluster1:clusterpass@192.168.4.191:6032")
```


