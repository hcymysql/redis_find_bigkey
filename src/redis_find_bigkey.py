import redis
import argparse
import logging
import rediscluster
import signal
import sys,os

"""
用于连接 Redis 服务器并查找大键（占用内存较多的键）
"""

def connect_redis(host, port, password=None, db=0, cluster_mode=False):
    try:
        if cluster_mode:  # 如果是集群模式
            redis_nodes = [{'host': host, 'port': port}]
            redis_client = rediscluster.RedisCluster(startup_nodes=redis_nodes, password=password)
        else:  # 单机模式
            redis_client = redis.Redis(host=host, port=port, password=password, db=db)
        return redis_client
    except redis.exceptions.AuthenticationError as e:
        print("Failed to authenticate with Redis server. Please provide the correct password.")
        sys.exit(2)
    except redis.exceptions.ConnectionError as e:
        print(f"Failed to connect to Redis at {host}:{port}")
        sys.exit(2)    


def is_redis_cluster(host, port, password=None, db=0):
    # 这里可以根据实际情况来判断 Redis 是否处于集群模式
    # 一种简单的方式是通过执行 CLUSTER INFO 命令并检查返回结果
    try:
        redis_client = redis.Redis(host=host, port=port, password=password, db=db)

        # 获取 Redis 服务器版本信息
        version_info = redis_client.info()
        version = version_info['redis_version']

        if list(map(int, version.split('.'))) < [4, 0]:  # 判断 Redis 版本是否低于 4.0
            print(f"Redis version: {version} does not support the bigkeys feature.")
            sys.exit(1)

        info = redis_client.execute_command('CLUSTER', 'INFO')
        return b"cluster_state:ok" in info
    except redis.exceptions.ResponseError as e:
        if "cluster support disabled" in str(e):
            return False  # 非集群模式
        else:
            #raise  # 其他异常继续抛出
            pass
    except redis.exceptions.ConnectionError as e:
        print(f"Failed to connect to Redis at {host}:{port}")
        return False


def find_big_keys(redis_client, threshold, batch_size, log_file):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler(log_file)])
    logger = logging.getLogger(__name__)

    cluster_mode = isinstance(redis_client, rediscluster.RedisCluster)

    match_pattern = "*"  # 匹配所有键

    def signal_handler(sig, frame):
        if sig == signal.SIGINT:
            print("程序接收到 Ctrl+C 终止信号")
            os._exit(0)
        elif sig == signal.SIGTSTP:
            print("程序接收到 Ctrl+Z 暂停信号")
            os._exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTSTP, signal_handler)

    if cluster_mode:
        for key in redis_client.scan_iter(match=match_pattern, count=batch_size):
            key_size = redis_client.memory_usage(key)
            key_type = redis_client.type(key).decode('utf-8')

            if key_type == 'hash':
                value_count = redis_client.hlen(key)
            elif key_type == 'set':
                value_count = redis_client.scard(key)
            elif key_type == 'list':
                value_count = redis_client.llen(key)
            elif key_type == 'zset':
                value_count = redis_client.zcard(key)
            elif key_type == 'string':
                value_count = 1
            else:
                value_count = "N/A"

            if key_size > threshold:
                try:
                    logger.info(f'大键: 【{key.decode("utf-8", "ignore")}】, 类型: 【{key_type}】, 大小: 【{key_size}】 （单位：字节）, 成员数量: 【{value_count}】')
                except UnicodeDecodeError:
                    logger.info(f'大键: 【{key}】, 类型: 【{key_type}】, 大小: 【{key_size}】 （单位：字节）, 成员数量: 【{value_count}】')

    else:
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor=cursor, match=match_pattern, count=batch_size)

            for key in keys:
                key_size = redis_client.memory_usage(key)
                key_type = redis_client.type(key).decode('utf-8')

                if key_type == 'hash':
                    value_count = redis_client.hlen(key)
                elif key_type == 'set':
                    value_count = redis_client.scard(key)
                elif key_type == 'list':
                    value_count = redis_client.llen(key)
                elif key_type == 'zset':
                    value_count = redis_client.zcard(key)
                elif key_type == 'string':
                    value_count = 1
                else:
                    value_count = "N/A"

                if key_size > threshold:
                    try:
                        logger.info(f'大键: 【{key.decode("utf-8", "ignore")}】, 类型: 【{key_type}】, 大小: 【{key_size}】 （单位：字节）, 成员数量: 【{value_count}】')
                    except UnicodeDecodeError:
                        logger.info(f'大键: 【{key}】, 类型: 【{key_type}】, 大小: 【{key_size}】 （单位：字节）, 成员数量: 【{value_count}】')
      
            if cursor == 0:
                break

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', required=True, help='Redis主机IP')
    parser.add_argument('-P', '--port', type=int, default=6379, help='Redis端口，默认为6379')
    parser.add_argument('-p', '--password', required=True, help='Redis密码')
    parser.add_argument('-c', action='store_true', help='连接到 Redis 集群模式')
    parser.add_argument('--threshold', type=int, default=10240, help='阈值，默认为10240（10KB）')
    parser.add_argument('-v', '--version', action='version', version='redis_find_bigkey工具版本号: 1.0.1，更新日期：2023-11-13')

    args = parser.parse_args()

    try:
        if is_redis_cluster(args.host, args.port, password=args.password): 
            if not args.c:
                print("Redis is in cluster mode. Please specify the '-c' flag to connect to the cluster.")
                return
        else:
            if args.c:
                print("Redis is in standalone mode. Removing the '-c' flag.")
                return

        if args.c:  # 如果用户输入了 -c 参数
            redis_client = connect_redis(args.host, args.port, password=args.password, cluster_mode=True)
        else:
            redis_client = connect_redis(args.host, args.port, password=args.password)

        log_file = f"{args.host}_{args.port}_bigkeys.txt"
        find_big_keys(redis_client, threshold=args.threshold, batch_size=1000, log_file=log_file)

    except redis.exceptions.ConnectionError as e:
        print(f"Failed to connect to Redis at {args.host}:{args.port}")
        sys.exit(1)

    except redis.exceptions.ResponseError as e:
        print(f"Redis command execution error: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
