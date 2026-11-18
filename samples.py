"""
Densify - samples.py
Demo ke liye ready-made data. Har node ek jaisa hai.
"""

from scheduler import Container

# Har node ki capacity: 4 CPU cores, 8 GiB memory
NODE_CPU = 4000   # millicores
NODE_MEM = 8192   # MiB

# Ek company ke microservices, usi order mein jaise deploy hone aaye.
# Kuch CPU-heavy hain (video-encoder), kuch memory-heavy (memcached, postgres-db).
MICROSERVICES = [
    Container("video-encoder",    2000,  256),
    Container("user-service",      500, 1536),
    Container("order-service",    1500, 1536),
    Container("redis-cache",       500, 3072),
    Container("api-gateway",      1000, 1024),
    Container("postgres-db",       500, 4096),
    Container("search-indexer",    750, 3072),
    Container("auth-service",      750,  256),
    Container("memcached",         250, 4096),
    Container("ml-inference",     1500, 2048),
    Container("payment-service",  1500, 1536),
    Container("batch-report",     1500, 1536),
    Container("kafka-broker",     1500, 2048),
    Container("analytics-worker", 1500, 3072),
    Container("log-collector",     250,  512),
]

# Replicas wala sample (anti-affinity): ek group ke containers alag nodes par hone chahiye,
# taaki ek node gire to bhi service chalti rahe.
REPLICATED = [
    Container("web-1",          1000, 1024, "web"),
    Container("web-2",          1000, 1024, "web"),
    Container("web-3",          1000, 1024, "web"),
    Container("api-1",           750, 1536, "api"),
    Container("api-2",           750, 1536, "api"),
    Container("api-3",           750, 1536, "api"),
    Container("db-primary",     1000, 4096, "db"),
    Container("db-replica",     1000, 4096, "db"),
    Container("cache-1",         250, 2048, "cache"),
    Container("cache-2",         250, 2048, "cache"),
    Container("kafka-1",        1000, 2048, "kafka"),
    Container("kafka-2",        1000, 2048, "kafka"),
    Container("kafka-3",        1000, 2048, "kafka"),
    Container("video-encoder",  2000,  256),
    Container("ml-inference",   1500, 2048),
    Container("batch-report",   1500, 1536),
    Container("log-collector",   250,  512),
    Container("metrics-agent",   250,  256),
]
