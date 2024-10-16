import redis
import rediscluster
from redis import sentinel

# Scheduler settings
SCHEDULER_PERSIST = True
SCHEDULER_QUEUE_CLASS = 'scrapy_redis_bloomfilter_block_cluster.queue.FifoQueue'
SCHEDULER_QUEUE_KEY = '%(spider)s:requests'
DUPEFILTER_CLASS = 'scrapy_redis_bloomfilter_block_cluster.dupefilter.LockRFPDupeFilter'
DUPEFILTER_DEBUG = False
DUPEFILTER_KEY = '%(spider)s:dupefilter'

DUPEFILTER_KEY_LIST = '%(spider)s:dupefilter_list'
DUPEFILTER_RULES_LIST = []

# Lock settings for Redis BloomFilter, used with LockRFPDupeFilter
DUPEFILTER_LOCK_KEY = '%(spider)s:lock'
DUPEFILTER_LOCK_NUM = 16  # Possible values: 16, 256, 4096
DUPEFILTER_LOCK_TIMEOUT = 15

SCHEDULER_FLUSH_ON_START = False
SCHEDULER_IDLE_BEFORE_CLOSE = 0

CLOSE_EXT_ENABLED = True
IDLE_NUMBER_BEFORE_CLOSE = 360  # Idle cycle duration: ~5 seconds

# Pipeline settings
REDIS_PIPELINE_KEY = '%(spider)s:items'
REDIS_PIPELINE_SERIALIZER = 'scrapy.utils.serialize.ScrapyJSONEncoder'

# Redis settings
REDIS_START_URLS_KEY = '%(spider)s:start_urls'
REDIS_START_URLS_AS_SET = False
REDIS_START_URLS_AUTO_INSERT = True  # Automatically insert start URLs on startup

REDIS_ENCODING = 'utf-8'
COMMON_REDIS_PARAMS = {
    'socket_timeout': 30,
    'socket_connect_timeout': 30,
    'retry_on_timeout': True,
    'password': None,
    'encoding': REDIS_ENCODING,
}

REDIS_PARAMS = COMMON_REDIS_PARAMS.copy()
REDIS_CLUSTER_PARAMS = COMMON_REDIS_PARAMS.copy()
REDIS_SENTINEL_PARAMS = {
    **COMMON_REDIS_PARAMS,
    'service_name': 'my_sentinel',
}

REDIS_CLS = redis.Redis
REDIS_CLUSTER_CLS = rediscluster.RedisCluster
REDIS_SENTINEL_CLS = sentinel.Sentinel

# BloomFilter settings
BLOOMFILTER_HASH_NUMBER = 15
BLOOMFILTER_BIT = 32
BLOOMFILTER_BLOCK_NUM = 1

BLOOMFILTER_HASH_NUMBER_LIST = 15
BLOOMFILTER_BIT_LIST = 32
BLOOMFILTER_BLOCK_NUM_LIST = 1