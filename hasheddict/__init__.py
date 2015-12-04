#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from zlib import crc32
from hashlib import sha256
from math import log, ceil
import collections
import threading

__all__     = ['HashedDict']

__version__   = "0.1.0"
__author__    = "Johannes Schreiner, johannes@schreiner.io"
__credits__   = ["Johannes Schreiner"]
__url__       = "https://github.com/JoEiner/hasheddict"
__copyright__ = "(c) 2015 Johannes Schreiner"
__license__   = "GNU General Public License v3 or later (GPLv3+)"


class HashedDict(dict):
    """
    A dictionary that provides cryptographic hashes of its contents.
    See package documentation for usage instructions.
    """

    def __init__(self, *args, **kwargs):
        """
        Possible ways of instantiation:

        HashedDict([algorithm[, trees_cache_size], ])
        HashedDict([algorithm[, trees_cache_size], ]**kwargs)
        HashedDict([algorithm[, trees_cache_size], ]iterable, **kwargs)
        HashedDict([algorithm[, trees_cache_size], ]mapping, **kwargs)

        @param algorithm:        algorithm is a class that provides an interface
                                 similar to hashlib.sha*() interface (see Lib/hashlib.py)
        @type  trees_cache_size: int
        @param trees_cache_size: The number of internal trees the HashedDict buffers.
                                 Raising this number increases memory usage, yet reduces
                                 time consumption when the dictionary grows over its boundaries
                                 Use only positive integers.

        Examples::

              >>> a = dict(one=1, two=2, three=3)
              >>> b = dict(zip(['one', 'two', 'three'], [1, 2, 3]))
              >>> c = dict([('two', 2), ('one', 1), ('three', 3)])
              >>> d = dict({'three': 3, 'one': 1, 'two': 2})

              >>> from hashlib import md5, sha512
              >>> e = dict(md5, one=1, two=2, three=3)
              >>> f = dict(1, sha512, zip(range(100000), reversed(range(100000))))
        """
        dictargs = [arg for arg in args if isinstance(arg, collections.Iterable) or
                                           isinstance(arg, collections.Mapping)]
        if len(dictargs) > 1:
                raise TypeError("HashedDict expected at most 1 iterable or mapping "
                                "argument, got %d" % len(args))

        hashargs = [arg for arg in args if not isinstance(arg, collections.Iterable) and
                                           not isinstance(arg, collections.Mapping)]

        self.__hashalg          = args[0] if len(hashargs) >= 1 else sha256
        self.__trees_cache_size = args[1] if len(hashargs) >= 2 else 3

        self.__key_to_hash = dict()
        depth = self.__get_depth_for_length(0)

        initial_tree = HashTree(self.__key_to_hash, self.__hashalg, depth)
        initial_tree.start()
        initial_tree.join()

        self.__trees = {depth: initial_tree}

        self.update(*dictargs, **kwargs)

    def get_hash(self):
        tree_nr = self.__get_depth_for_length(len(self))
        return self.__trees[tree_nr].get_hash()

    def __setitem__(self, key, value):
        hash_value = self.__hash_item(key, value)
        self.__key_to_hash[key] = hash_value

        if key in self:
            for tree in self.__trees.itervalues():
                tree.delete(key, hash_value)

        super(HashedDict, self).__setitem__(key, value)

        for tree in self.__trees.itervalues():
            tree.add(key, hash_value)

        self.__manage_cached_trees()


    def __delitem__(self, key):
        self.__manage_cached_trees()

        for tree in self.__trees.itervalues():
            tree.delete(key, self.__key_to_hash[key])
        del self.__key_to_hash[key]

        super(HashedDict, self).__delitem__(key)


    def update(self, *args, **kwargs):
        if args:
            if len(args) > 1:
                raise TypeError("update expected at most 1 arguments, "
                                "got %d" % len(args))
            other = dict(args[0])
            for key in other:
                self[key] = other[key]
        for key in kwargs:
            self[key] = kwargs[key]

    def setdefault(self, key, value=None):
        if key not in self:
            self[key] = value
        return self[key]

    def __manage_cached_trees(self):
        dict_length = len(self)
        curr_depth = self.__get_depth_for_length(dict_length)

        range_start = max(0, curr_depth - (self.__trees_cache_size/2))
        range_end = range_start + self.__trees_cache_size
        allowed_trees = set(xrange(range_start, range_end))
        existing_trees = set(self.__trees.keys())

        deprecated_keys = existing_trees - allowed_trees
        new_keys = allowed_trees - existing_trees

        for tree_key in deprecated_keys:
            del self.__trees[tree_key]

        for tree_key in new_keys:
            new_tree = HashTree(self.__key_to_hash,
                                self.__hashalg, tree_key)
            new_tree.start()
            self.__trees[tree_key] = new_tree

    @staticmethod
    def __get_depth_for_length(length):
        if length == 0:
            return 0
        else:
            return int(ceil(log(length, 2)))

    def __hash_item(self, key, value):
        return (self.__hashalg(self.__hashalg(repr(key)).digest() +
                               self.__hashalg(repr(value)).digest()).digest())


class HashTree(threading.Thread):
    def __init__(self, key_to_hash, hashalg, tree_depth):
        threading.Thread.__init__(self)
        self.__key_to_hash = key_to_hash.copy()
        self.__tree_depth = tree_depth
        self.__hashalg = hashalg

    def run(self):
        self.__tree = self.__build_tree()
        self.__leaf_hashes = self.__build_leaf_items()
        self.__rehash_all()

    def get_hash(self):
        self.join()

        return self.__tree[0][0]

    def add(self, key, hash_value):
        self.join()

        position = (crc32(key) & 0xffffffff) & ((1 << self.__tree_depth) - 1)

        self.__leaf_hashes[position].append(hash_value)
        self.__rehash(position)

    def delete(self, key, hash_value):
        self.join()

        position = (crc32(key) & 0xffffffff) & ((1 << self.__tree_depth) - 1)

        while hash_value in self.__leaf_hashes[position]:
            self.__leaf_hashes[position].remove(hash_value)

        self.__rehash(position)

    def __build_tree(self):
        tree = []

        for i in xrange(self.__tree_depth+1):
            current_row = [None for j in xrange(1 << i)]
            tree.append(current_row)

        return tree

    def __build_leaf_items(self):
        leaf_count = 1 << self.__tree_depth
        new_leaf_items = [[] for i in xrange(leaf_count)]

        for key, hash_value in self.__key_to_hash.iteritems():
            position = (crc32(key) & 0xffffffff) % leaf_count
            new_leaf_items[position].append(hash_value)

        return new_leaf_items

    def __rehash_all(self):
        self.__tree[-1] = [self.__hash_leaf(leaf_items) for leaf_items in self.__leaf_hashes]

        for row_nr in xrange(self.__tree_depth,0,-1):
            row = self.__tree[row_nr]
            for current_position in xrange(0, (len(row)+1)/2):
                self.__rehash_parent(row_nr, current_position)

    def __rehash(self, leaf_position):
        leaf_items = self.__leaf_hashes[leaf_position]
        self.__tree[-1][leaf_position] = self.__hash_leaf(leaf_items)

        lchild_pos = leaf_position
        for row_nr in xrange(self.__tree_depth, 0, -1):
            #current_position = self.__rehash_parent(row_nr, current_position)

            rchild_pos = lchild_pos | (1 << (row_nr - 1))
            lchild_pos = lchild_pos & ((1 << (row_nr - 1)) - 1)

            children_row = self.__tree[row_nr]
            parent_row = self.__tree[row_nr-1]

            parent_row[lchild_pos] = self.__hashalg(children_row[lchild_pos] + \
                                                    children_row[rchild_pos]).digest()

    def __hash_leaf(self, leaf_items):
        leaf_items.sort()

        hashalg = self.__hashalg()
        for item in leaf_items:
            hashalg.update(item)

        return hashalg.digest()

    def __rehash_parent(self, row_nr, element_pos):
            lchild_pos = element_pos & ((1 << (row_nr - 1)) - 1)
            rchild_pos = element_pos | (1 << (row_nr - 1))
            #parent_pos = lchild_pos

            children_row = self.__tree[row_nr]
            parent_row = self.__tree[row_nr-1]

            #lchild_hash = children_row[lchild_pos]
            #rchild_hash = children_row[rchild_pos]
            #parent_row[parent_pos] = self.__hashalg(lchild_hash + \
            #                                        rchild_hash).digest()

            parent_row[lchild_pos] = self.__hashalg(children_row[lchild_pos] + \
                                                    children_row[rchild_pos]).digest()


if __name__ == '__main__':
    pangram = HashedDict(pangram="The quick brown fox jumps over the lazy dog")
    assert pangram.get_hash() == '\xe9|\xdcJ=\xda\x84\xbd\xa6\x8e\xea\x9c=\x16\x93' + \
                                 'x\xb2\xff9\x83S!\xfbE\xbc\x0c\x83\xb8`H\x94\xa6'


    hd1 = HashedDict()
    empty_hash = hd1.get_hash()
    assert empty_hash == "\xe3\xb0\xc4B\x98\xfc\x1c\x14\x9a\xfb\xf4\xc8\x99" + \
                         "o\xb9$'\xaeA\xe4d\x9b\x93L\xa4\x95\x99\x1bxR\xb8U"
    hd1["key1"] = "value1"
    new_hash = hd1.get_hash()
    del hd1["key1"]

    assert empty_hash == hd1.get_hash()

    hd2 = HashedDict(key1="value1", key2="value2")
    del hd2["key2"]
    assert hd2.get_hash() == new_hash
    del hd2["key1"]
    assert hd2.get_hash() == empty_hash

    hd3 = HashedDict()
    assert hd3.get_hash() == empty_hash

    hashList = []
    for i in xrange(1026):
        hashList.append(hd3.get_hash())
        hd3[str(i)] = i

    for i in xrange(1025, -1, -1):
        del hd3[str(i)]
        assert hashList[i] == hd3.get_hash()

    print "all tests successful"
