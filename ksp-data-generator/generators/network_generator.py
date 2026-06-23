import random

import networkx as nx

from .utils import simple_id


FIELDS = [
    "edge_id", "source_accused_id", "target_accused_id", "relationship",
    "gang_id", "strength", "first_seen_fir",
]


RELATIONSHIPS = ["co_accused", "known_associate", "gang_member", "phone_contact", "financial_link", "vehicle_shared"]


def rows(count, accused_count, gang_count, fir_count):
    graph = nx.barabasi_albert_graph(max(2, accused_count), min(3, max(1, accused_count - 1)), seed=42)
    edges = list(graph.edges())
    random.shuffle(edges)
    produced = 0
    while produced < count and edges:
        source, target = edges[produced % len(edges)]
        produced += 1
        gang_id = simple_id("GANG", random.randint(1, gang_count)) if gang_count and random.random() < 0.45 else ""
        yield {
            "edge_id": simple_id("EDGE", produced),
            "source_accused_id": simple_id("ACC", source + 1),
            "target_accused_id": simple_id("ACC", target + 1),
            "relationship": random.choice(RELATIONSHIPS),
            "gang_id": gang_id,
            "strength": round(random.uniform(0.15, 0.98), 3),
            "first_seen_fir": simple_id("FIR", random.randint(1, max(1, fir_count))).replace("FIR-", "FIR-"),
        }

