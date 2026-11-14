"""ColorFrame reference implementation (Python 3, standard library only).

Skeleton: public names exist so the unit tests import; behaviour is not implemented yet.
"""
from collections import namedtuple


class ValidationError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class UsageError(Exception):
    pass


Limits = namedtuple("Limits", "max_orf_nt max_path_nodes max_node_visits max_states")
DEFAULT_LIMITS = Limits(1200, 12, 2, 50000)


def is_valid_id(text):
    raise NotImplementedError


def is_valid_dna(text):
    raise NotImplementedError


def parse_colors(field):
    raise NotImplementedError


def parse_overlap(field):
    raise NotImplementedError


def intersect_colors(active, colors):
    raise NotImplementedError


def can_start_frame(sequence, offset):
    raise NotImplementedError


def startable_end(length, has_successors, overlap):
    raise NotImplementedError


def is_stop_codon(codon):
    raise NotImplementedError


def build_graphs(node_rows, edge_rows):
    raise NotImplementedError


def search(graph, policy, limits):
    raise NotImplementedError


def main(argv=None):
    raise NotImplementedError
