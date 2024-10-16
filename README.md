# ScrapyRedisBloomFilterBlockCluster

# Table of Contents

- [ScrapyRedisBloomFilterBlockCluster](#scrapyredisbloomfilterblockcluster)
- [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Installation](#installation)
  - [Instructions](#instructions)
    - [Add appropriate configuration to scrapy crawler settings.py](#add-appropriate-configuration-to-scrapy-crawler-settingspy)
    - [Modify Spider](#modify-spider)
  - [**Example**](#example)
    - [**Download Demo and Start**](#download-demo-and-start)
    - [**Add `start_urls` to Redis**](#add-start_urls-to-redis)
  - [**Additional Information**](#additional-information)

## Introduction

ScrapyRedisBloomFilterBlockCluster is based on scrapy-redis + bloomfilter algorithm to deduplicate, supports allocation of multiple Redis memory blocks (Redis 1 string maximum 512MB), and supports Redis stand-alone, Redis Sentinel and Redis-Cluster clusters, suitable for ultra-large distributed scrapy crawlers.

This project is based on the following projects:

- [scrapy-redis](https://github.com/rmax/scrapy-redis)
- [ScrapyRedisBloomFilter](https://github.com/Python3WebSpider/ScrapyRedisBloomFilter)
- [scrapy_redis_cluster](https://github.com/thsheep/scrapy_redis_cluster)
- [Scrapy_Redis_Bloomfilter](https://github.com/LiuXingMing/Scrapy_Redis_Bloomfilter)


Based on python 3.7, scrapy 1.8.0, and tested on standalone Redis 3.2.100, Redis Sentinel 5.0.5 and cluster Redis Cluster 5.0.7.

## Installation

Using pip:
```
pip install scrapy-redis-bloomfilter-block-cluster
```
- Other dependencies: twisted==19.10.0, scrapy==1.8.0,  redis-py-cluster==2.0.0, redis==3.0.1

## Instructions

### Add appropriate configuration to scrapy crawler settings.py

The following are all supported configurations:
```python
# Enable scrapy_redis_bloomfilter_block_cluster
SCHEDULER = "scrapy_redis_bloomfilter_block_cluster.scheduler.Scheduler"

# -------------------------------- Scheduler Configuration --------------------------------

# True: the queue and deduplication queue won't be deleted when exiting, default is True
SCHEDULER_PERSIST = True

# Queue class, supports FifoQueue, LifoQueue, PriorityQueue, SimpleQueue, default is FifoQueue
SCHEDULER_QUEUE_CLASS = 'scrapy_redis_bloomfilter_block_cluster.queue.FifoQueue'

# Queue key, used to save scrapy request objects (serialized), default %(spider)s:requests (the current crawler name)
SCHEDULER_QUEUE_KEY = '%(spider)s:requests'

# Deduplication class (RFPDupeFilter, LockRFPDupeFilter or ListLockRFPDupeFilter), the latter two will be locked when using
# BloomFilter will lock when judging to ensure accuracy, but the performance will be reduced by about 30%. It is recommended for distributed crawlers.

lockrfpdupefilter_description = """

# Incremental Scraping with Dynamic List Pages Problem: 

When developing a web scraper, especially one targeting news websites, you might face the following issue:  
- News websites often have list pages such as `/page/1`, `/page/2`, etc., where each page contains a fixed number of news article links.
- The crawler first extracts links from these list pages and then scrapes the content from the news articles linked on those pages.

For a one-time scraping session, this is straightforward. But incremental scraping (where the crawler periodically revisits the site to gather new content) introduces a challenge. Here’s what happens:
1. During the first scraping run, the URLs for list pages like `/page/1` are stored in the Bloom filter for deduplication.
2. On a subsequent scraping run, even though the content on `/page/1` has changed (with new articles), the Bloom filter prevents the crawler from re-fetching `/page/1` because it has already seen this URL.

This prevents the crawler from collecting new article links, causing it to miss important content.

---

# Solution with `ListLockRFPDupeFilter`:

`ListLockRFPDupeFilter` introduces a temporary deduplication mechanism that treats list pages (e.g., `/page/1`, `/page/2`) differently from the article pages.

  - List pages (like `/page/1`, `/page/2`) are saved in a separate temporary deduplication instance.
  - Article pages (the actual news content) are stored in another persistent deduplication instance.
  - Once a scraping session finishes, the Redis key storing the temporary deduplication data for list pages is deleted.  
  - This allows the crawler to re-fetch list pages on the next scraping run, ensuring it doesn’t miss newly added links.

---

# Note:

By default, Scrapy spiders do not exit when the request queue is empty—they wait indefinitely for new requests.  
However, for `ListLockRFPDupeFilter` to work correctly, the spider must exit automatically after scraping, so the Redis key for list pages can be deleted. 

To enable this behavior, you need to configure the "smart exit" extension in Scrapy, ensuring the spider exits properly when all tasks are complete.

"""

# -------------------------------- Deduplication Configuration --------------------------------

DUPEFILTER_CLASS = 'scrapy_redis_bloomfilter_block_cluster.dupefilter.LockRFPDupeFilter'
DUPEFILTER_DEBUG = False    # Deduplicating DEBUG flag , default is False
DUPEFILTER_KEY = '%(spider)s:dupefilter'    # Redis key used for the Bloom filter that stores deduplicated URLs
DUPEFILTER_KEY_LIST = '%(spider)s:dupefilter_list'  # Redis key for the second deduplication instance (specifically for list pages, e.g., /page/1, /page/2).
DUPEFILTER_RULES_LIST = []  # A list of regular expressions that determine which URLs will use the secondary deduplication instance. If defined in the spider’s code, those settings take precedence over this one.

# -------------------------------- Redis Lock Configuration for Deduplication --------------------------------

DUPEFILTER_LOCK_KEY = '%(spider)s:lock' # Redis key for the Bloom filter lock
DUPEFILTER_LOCK_NUM = 16    # The number of locks. Possible values: 16, 256, or 4096
DUPEFILTER_LOCK_TIMEOUT = 15    # Lock expiration time in seconds

SCHEDULER_FLUSH_ON_START = False

# -------------------------------- Smart Exit Extension --------------------------------

EXTENSIONS = {
    # ...Other extensions
    'scrapy_redis_bloomfilter_block_cluster.extensions.RedisSpiderSmartIdleClosedExensions': 300,
    # ...Other extensions
}
CLOSE_EXT_ENABLED = True    # Enables the smart exit extension (default: True)
IDLE_NUMBER_BEFORE_CLOSE = 360  # If the spider stays idle for 360 idle cycles (~5 seconds per cycle), it will terminate automatically.

# -------------------------------- Redis Pipeline Settings --------------------------------

ITEM_PIPELINES = {
    # ...Other pipelines
    'scrapy_redis_bloomfilter_block_cluster.pipelines.RedisPipeline': 300,
    # ...Other pipelines
}
REDIS_PIPELINE_KEY = '%(spider)s:items'   # Redis key to store scraped data
REDIS_PIPELINE_SERIALIZER = 'scrapy.utils.serialize.ScrapyJSONEncoder'  # Data serialization method

# -------------------------------- Redis Configuration --------------------------------

REDIS_START_URLS_KEY = '%(spider)s:start_urls'  # Key for storing start URLs in Redis
REDIS_START_URLS_AS_SET = False # If True, stores URLs in a set (avoiding duplicates). Default: False (uses a list).
REDIS_START_URLS_AUTO_INSERT = True # Automatically inserts start URLs into Redis when the spider starts (default: True).
REDIS_ENCODING = 'utf-8'    # Redis encoding

# -------------------------------- Redis Connection Settings --------------------------------

REDIS_URL = 'redis://localhost:6379/0'	# with authentication: 'redis://:admin123@localhost:6379/0
# REDIS_HOST = 'localhost'	# Redis address
# REDIS_PORT = 6379		# Redis port
# REDIS_PASSWORD = None	# Password for authentication (if required)
# REDIS_PARAMS = {	# Additional connection parameters
#     'socket_timeout': 30,
#     'socket_connect_timeout': 30,
#     'db': 0,
#     # ...Other parameters
# }

# -------------------------------- Redis Sentinel Setup --------------------------------

# REDIS_SENTINEL_NODES = [  # List of Sentinel nodes
#     ('localhost', 26379),
#     ('localhost', 26380),
#     ('localhost', 26381)
# ]
# REDIS_SENTINEL_SERVICE_NAME = 'mymaster'  # Name of the Sentinel service
# REDIS_SENTINEL_PASSWORD = '123456'		# Password for Sentinel authentication (if needed)
# REDIS_SENTINEL_PARAMS = { # Connection parameters for Sentinel
#     'socket_timeout': 30,
#     'socket_connect_timeout': 30,
#     'retry_on_timeout': True,
#     'db': 0,  # Redis database index
#     # ...Other parameters
# }

# -------------------------------- Redis Cluster Configuration --------------------------------

# REDIS_CLUSTER_URL = 'redis://localhost:7001/' # URL for connecting to the Redis cluster. This has higher priority than individual node settings
# REDIS_CLUSTER_NODES = [   # List of all available nodes
#    {"host": "localhost", "port": "7001"},
#    {"host": "localhost", "port": "7002"},
#    {"host": "localhost", "port": "7003"},
#    {"host": "localhost", "port": "7004"},
#    {"host": "localhost", "port": "7005"},
#    {"host": "localhost", "port": "7006"}
# ]
# REDIS_CLUSTER_PASSWORD = '123456'		# Password for cluster authentication (if required).
# REDIS_CLUSTER_PARAMS = {    # Cluster connection parameters, including timeouts and retry settings
#     'socket_timeout': 30,
#     'socket_connect_timeout': 30,
#     'retry_on_timeout': True,
#     # ...Other parameters
# }

# Redis connection priority: Cluster > Sentinel > Standalone

# -------------------------------- Primary Bloom Filter Configuration --------------------------------

BLOOMFILTER_HASH_NUMBER = 15    # Number of hash functions used in the Bloom filter. Increasing the number reduces the false-positive rate but slows down performance
BLOOMFILTER_BIT = 32    # Bit size of the Bloom filter. Default is 32 (2^32). Redis has a string size limit of 2^32 bits
BLOOMFILTER_BLOCK_NUM = 1   # Number of Redis strings used. A higher number increases deduplication capacity but consumes more Redis resources

# -------------------------------- 2nd Bloom Filter ListLockRFPDupeFilter Settings --------------------------------
# These settings are used for the secondary deduplication instance (specifically for list pages, e.g., /page/1, /page/2)

BLOOMFILTER_HASH_NUMBER_LIST = 15
BLOOMFILTER_BIT_LIST = 32
BLOOMFILTER_BLOCK_NUM_LIST = 1

```

### Modify Spider  
Refer to the example for specific details.

---

## **Example**

### **Download Demo and Start**
```bash
$ git clone https://github.com/leffss/ScrapyRedisBloomFilterBlockCluster.git
$ cd ScrapyRedisBloomFilterBlockCluster/demo/CnblogsSpider
$ scrapy crawl cnblogs
```
- Make sure the Redis environment is ready beforehand.

---

### **Add `start_urls` to Redis**

**For Redis Standalone & Sentinel Version:**
```bash
$ redis-cli
redis 127.0.0.1:6379> lpush cnblogs:start_urls https://www.cnblogs.com/sitehome/p/1
```

**For Redis Cluster Version:**
```bash
$ redis-cli -c
redis 127.0.0.1:7001> lpush cnblogs:start_urls https://www.cnblogs.com/sitehome/p/1
```

- If `auto_insert = True` or `REDIS_START_URLS_AUTO_INSERT = True` is set, you don’t need to perform the above operation. Refer to the earlier configuration instructions for more details.

---

## **Additional Information**

To calculate the **optimal size of the bit array (m)**, the **number of hash functions (k)**, the **memory usage (mem)**, and the **number of Redis 512MB memory blocks (block_num)** needed, based on the **number of unique items to deduplicate (n)** and the **acceptable false positive rate (p)**, use the following method:

```python
from scrapy_redis_bloomfilter_block_cluster.bloomfilter import calculation_bloom_filter

n = 100000000   # Number of items to deduplicate: 100 million
p = 0.00000001  # False positive rate: 1 in 100 million
m, k, mem, block_num = calculation_bloom_filter(n, p)
print(m, k, mem, block_num)
```

- **Result:**
  - Bit array size: 3,834,023,351 (approximately 3.8 billion)
  - Number of hash functions: 27  
  - Memory usage: 458 MB  
  - Number of Redis string memory blocks: 1

- **Conclusion:**  
  Although the memory usage is relatively low, the number of hash functions is high, meaning that **the quality of the hash functions** will have the most significant impact on BloomFilter’s deduplication performance.