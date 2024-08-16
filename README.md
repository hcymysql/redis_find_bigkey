# redis_find_bigkey工具 - 自定义阀值查找Redis Big Keys
# https://github.com/hcymysql/redis_find_bigkey

Redis大key是指在Redis中存储的Value值非常大的键，当一个命令需要处理大的键值时，Redis将会花费更多的时间来执行这个命令，这会导致其他客户端发起的命令需要等待更长的时间才能得到响应。在高并发的场景下，这可能会导致整个系统的性能下降，甚至出现请求超时的情况。

当一个键的值很大时，会引发一些潜在的危害和问题：

- Redis是基于内存的数据库，当一个键的值非常大时，会占用大量的内存资源。如果大量的大key存在，可能会导致系统的内存不足，从而引发性能问题甚至导致系统崩溃。
   
- 网络传输延迟：当一个键的值很大时，会增加网络传输的压力，可能导致网络拥塞和性能下降。

- 在Redis集群环境中，键值通常会根据一定的规则进行分片存储。当一个键的值很大时，可能无法均匀地进行分片，导致负载不均衡和数据倾斜的问题。
-----------------------------------------------

# 使用
```
shell> ./redis_find_bigkey --help
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
![image](https://github.com/hcymysql/redis_find_bigkey/assets/19261879/bfee2452-d413-4a78-a01b-89d452f0f279)

会在当前目录下，把big keys信息保存在{IP}_{PORT}_bigkeys.txt文件里。

### 注：redis_find_bigkey 不能低于Redis 4.0版本使用，适用于CentOS 7系统。
