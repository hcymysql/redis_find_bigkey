# redis_find_bigkey
自定义阀值查找Redis Big Key（占用内存较多的Value）的工具

```
# ./redis_find_bigkey --help
usage: redis_find_bigkey [-h] -H HOST [-P PORT] -p PASSWORD [-c] [--threshold THRESHOLD] [-v]

options:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  Redis主机IP
  -P PORT, --port PORT  Redis端口，默认为6379
  -p PASSWORD, --password PASSWORD
                        Redis密码
  -c                    连接到 Redis 集群模式
  --threshold THRESHOLD
                        阈值，默认为10240（10KB）
  -v, --version         show program's version number and exit
```

单机模式：
```
shell> chmod 755 redis_find_bigkey
shell> ./redis_find_bigkey -H 192.168.176.204 -p 123456
```

集群模式：
```
shell> chmod 755 redis_find_bigkey
shell> ./redis_find_bigkey -H 192.168.176.204 -p 123456 -c
```

