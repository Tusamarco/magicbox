# What is this?


## modules
pip install mysql-connector-python
pip install scipy
pip install keyboard <- No

from rich.console import Console
from pynput import keyboard

## Logger
We use logging to print out messages on the console.
During the execution by defaul the log level is WARNING
But we can easily change it doing:

```python
import logging
logging.getLogger().setLevel(logging.INFO)
```
To modify the format on the fly in the code :
```python
originalhan = logging.getLogger().handlers[0]
modahnd = logging.StreamHandler()
modahnd.setFormatter(logging.Formatter("%(message)s"))
logging.getLogger().handlers[0]=modahnd

# To put bacj the original
logging.getLogger().handlers[0]=originalhan
```

to see what levels are supported: 
https://docs.python.org/3.13/library/logging.html#logging-levels

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


