from hashlib import md5
import mmh3
import math


class HashMap:
    def __init__(self, m, seed):
        self.m = m
        self.seed = seed

    def hash(self, value):
        return mmh3.hash(value, self.seed, signed=False) % self.m


def calculate_bloom_filter(n, p):
    m = - (n * math.log(p)) / (math.log(2) ** 2)
    k = (m / n) * math.log(2)
    mem = math.ceil(m / 8 / 1024 / 1024)
    block_num = math.ceil(mem / 512)
    return math.ceil(m), math.ceil(k), mem, block_num


class BloomFilter:
    SEEDS = [
        543, 460, 171, 876, 796, 607, 650, 81, 837, 545, 591, 946, 846, 521, 
        913, 636, 878, 735, 414, 372, 344, 324, 223, 180, 327, 891, 798, 933, 
        493, 293, 836, 10, 6, 544, 924, 849, 438, 41, 862, 648, 338, 465, 562, 
        693, 979, 52, 763, 103, 387, 374, 349, 94, 384, 680, 574, 480, 307, 580, 
        71, 535, 300, 53, 481, 519, 644, 219, 686, 236, 424, 326, 244, 212, 909, 
        202, 951, 56, 812, 901, 926, 250, 507, 739, 371, 63, 584, 154, 7, 284, 
        617, 332, 472, 140, 605, 262, 355, 526, 647, 923, 199, 518
    ]

    def __init__(self, server, key, bit, hash_number, block_num):
        self.m = min(1 << bit, 1 << 32)
        self.seeds = self.SEEDS[:min(hash_number, len(self.SEEDS))]
        self.server = server
        self.key = key
        self.block_num = block_num
        self.value_split_num = min(3, max(1, (block_num - 1).bit_length() // 4))
        self.maps = [HashMap(self.m, seed) for seed in self.seeds]

    def _get_redis_key(self, value):
        return self.key + str(int(value[:self.value_split_num], 16) % self.block_num)

    def exists(self, value):
        if not value:
            return False
        redis_key = self._get_redis_key(value)
        with self.server.pipeline() as pipe:
            for map in self.maps:
                pipe.getbit(redis_key, map.hash(value))
            return all(pipe.execute())

    def insert(self, value):
        redis_key = self._get_redis_key(value)
        with self.server.pipeline() as pipe:
            for map in self.maps:
                pipe.setbit(redis_key, map.hash(value), 1)
            pipe.execute()


class BloomFilterNew(BloomFilter):
    def __init__(self, server, key, capacity=100_000_000, error_rate=0.00001):
        bit, hash_number, _, block_num = calculate_bloom_filter(capacity, error_rate)
        super().__init__(server, key, bit, hash_number, block_num)


class CountBloomFilter:
    SEEDS = BloomFilter.SEEDS
    value_split_num = 3

    def __init__(self, server, key, bit, hash_number, block_num):
        self.m = min(1 << bit, 1 << 32)
        self.seeds = self.SEEDS[:min(hash_number, len(self.SEEDS))]
        self.server = server
        self.key = key
        self.block_num = block_num
        self.maps = [HashMap(self.m, seed) for seed in self.seeds]

    def _get_redis_key(self, value):
        return self.key + str(int(value[:self.value_split_num], 16) % self.block_num)

    def exists(self, value):
        if not value:
            return False
        redis_key = self._get_redis_key(value)
        with self.server.pipeline() as pipe:
            for map in self.maps:
                pipe.get(redis_key + str(map.hash(value)))
            return all(int(d.decode()) > 0 for d in pipe.execute())

    def insert(self, value):
        if not self.exists(value):
            redis_key = self._get_redis_key(value)
            with self.server.pipeline() as pipe:
                for map in self.maps:
                    pipe.incrby(redis_key + str(map.hash(value)))
                pipe.execute()

    def remove(self, value):
        if self.exists(value):
            redis_key = self._get_redis_key(value)
            with self.server.pipeline() as pipe:
                for map in self.maps:
                    pipe.decrby(redis_key + str(map.hash(value)))
                pipe.execute()


if __name__ == '__main__':
    n = 100_000_000
    p = 0.000001
    m, k, mem, block_num = calculate_bloom_filter(n, p)
    print(m, k, mem, block_num)