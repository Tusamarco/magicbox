# What is this?


## modules
pip install mysql-connector-python
pip install scipy

## when using without MySQL shell
1) Open Python console
2) Import the magicbox top class (that simulate the plugin call in shell)
    ``` python 
   from magicbox import MagicC
   ```
3) use MagicC instead magicbox in the following commands
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


