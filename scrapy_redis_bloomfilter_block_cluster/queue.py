from rediscluster import RedisCluster
from scrapy.http import Request
from scrapy.utils.misc import load_object
from . import picklecompat

class Base:
    def __init__(self, server, spider, key):
        self.server = server
        self.spider = spider
        self.key = key % {'spider': spider.name}
        self.serializer = picklecompat

    def _encode_request(self, request):
        obj = request.to_dict()
        return self.serializer.dumps(obj)

    def _decode_request(self, encoded_request):
        obj = self.serializer.loads(encoded_request)
        return Request.from_dict(obj)

    def __len__(self):
        raise NotImplementedError

    def push(self, request):
        raise NotImplementedError

    def pop(self, timeout=0):
        raise NotImplementedError

    def clear(self):
        self.server.delete(self.key)

class FifoQueue(Base):
    def __len__(self):
        return self.server.llen(self.key)

    def push(self, request):
        self.server.lpush(self.key, self._encode_request(request))

    def pop(self, timeout=0):
        data = self.server.brpop(self.key, timeout)[1] if timeout > 0 else self.server.rpop(self.key)
        if data:
            return self._decode_request(data)

class PriorityQueue(Base):
    def __len__(self):
        return self.server.zcard(self.key)

    def push(self, request):
        data = self._encode_request(request)
        score = -request.priority
        self.server.execute_command('ZADD', self.key, score, data)

    def pop(self, timeout=0):
        if isinstance(self.server, RedisCluster):
            pop_script = """
                local result = redis.call('zrange', KEYS[1], 0, 0)
                if result[1] then
                    redis.call('zremrangebyrank', KEYS[1], 0, 0)
                    return result[1]
                else
                    return nil
                end
            """
            script = self.server.register_script(pop_script)
            result = script(keys=[self.key])
            if result:
                return self._decode_request(result)
        else:
            pipe = self.server.pipeline()
            pipe.multi()
            pipe.zrange(self.key, 0, 0).zremrangebyrank(self.key, 0, 0)
            result, _ = pipe.execute()
            if result:
                return self._decode_request(result[0])

class LifoQueue(Base):
    def __len__(self):
        return self.server.llen(self.key)

    def push(self, request):
        self.server.lpush(self.key, self._encode_request(request))

    def pop(self, timeout=0):
        data = self.server.blpop(self.key, timeout)[1] if timeout > 0 else self.server.lpop(self.key)
        if data:
            return self._decode_request(data)
