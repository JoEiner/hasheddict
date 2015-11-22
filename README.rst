Overview
========

hasheddict is a dictionary that provides cryptographic hashes of its contents.
It is suitable for use cases where elements are frequently added and deleted in
large dictionaries as it does not require rehashing the entire dataset when
dictionary is modified. The algorithm is based on Merkle trees
(https://en.wikipedia.org/wiki/Merkle_tree).


Usage
=====

HashedDict objects can be instantiated and used just like normal Python dicts.
By default, sha256 is used to generate the cryptographic hash.

Adding and removing elements is identical to Python dicts. HashedDict feeds the
``__repr__`` attribute of any key or value into the hash algorithm. It therefore
works correctly **IF AND ONLY IF** the ``__repr__`` uniquely identifies the
objects that are stored in the dict both as key and value.

To obtain the hash of a dictionary, the ``get_hash()`` method is executed. Its
return value is the same type and size as the return of the digest() method of
the hash algorithm used. The default hash algorithm is ``hashlib.sha256`` and the
default return value is therefore a str of length ``hashlib.sha256.digest_size``
(256 bit/32 unicode characters).

The default hash algorithm and the a performance setting can be influenced when
HashedDict is instantiated. This is done by providing two arguments to the
HashedDict constructor in front of the arguments supported by Python dict:

- If exactly one argument is provided, this argument is the hash algorithm used
  by HashedDict. It has to be a hash algorithm from python hashlib or a class
  that provides the same constructor, an ``update()`` method to add content to the
  hash-function and a ``digest()`` method that returns unicode-string of the hash of
  the input.

- If two arguments are provided the first argument influences performance.
  Its default value is 3, if it is increased, the memory usage of HashedDict will
  rise and the performance of adding and removing elements from the dictionary
  will decrease. However, a higher number reduces the relative number of additions
  where adding takes the worst-case time. In general, increasing this number is
  recommended for scenarios where dicts repeatedly shrink and grow by more than
  2^log2(n) elements (n is the dict size). Reducing it is recommended if only the
  total add/remove performance is interesting, not the worst-case performance and
  where memory is scarce.

Example
-------
>>> import hashlib
>>> hashed_dict1 = HashedDict(key1="value1", key2="value2")
>>> hashed_dict2 = HashedDict(key2="value2", key1="value1")
>>> hashed_dict3 = HashedDict(hashlib.sha512, key1="value1", key2="value2")
>>> hashed_dict1.get_hash() == hashed_dict2.get_hash()
True
>>> hashed_dict1.get_hash() == hashed_dict3.get_hash()
False
>>> hashed_dict4 = HashedDict()
>>> hashed_dict4[key1] = "value1"
>>> hashed_dict4[key2] = "value2"
>>> hashed_dict1.get_hash() == hashed_dict4.get_hash()
True
>>> hashed_dict5 = HashedDict(1, hashlib.sha512, key1="value1", key2="value2")
>>> hashed_dict5.get_hash() == hashed_dict3.get_hash()
True
>>> hashed_dict = HashedDict(pangram="The quick brown fox jumps over the lazy dog")
'/\xd4\xe1\xc6z-(\xfc\xed\x84\x9e\xe1\xbbv\xe79\x1b\x93\xeb\x12'


Performance
===========
Adding and removing elements immediately recomputes the hashes the dictionary,
the invocation of get_hash() therefore does not induce any overhead.

Adding and removing elements has an average complexity of O(log n), however the
worst case complexity is O(n). Please note the worst case execution time really
takes place when the length of a dictionary is increased from 2^n to (2^n)+1.
In these cases, the entire dictionary is re-hashed which uses significant time
for very large dictionaries (ten thousands of elements)


Internals
=========

This module uses a standard Python dict and adds a balanced binary tree to
it. This binary tree contains a list at every leaf node. Using a crc32 based
mapping, every key in the dictionary is uniquely assigned to one of these lists.
The actual list entry is a cryptographic hash uniquely identifying the tuple of
dictionary key and value. Every leaf node therefore consists of a list of hash
strings which may also be empty if no dictionary keys are mapped to the leaf
node. To generate a hash of the complete dictionary, this list is sorted and
then cryptographically hashed. The leaf node therefore has a unique hash string
of its own.

Every internal node (non-leaf) is assigned a hash string through concatenation
and hashing of its two child nodes. The root of the tree (level 0) is e.g.
assigned a hash through hashing of the hashes of the two level 1 internal nodes.
The hash of the root node of the binary is also the hash of the dictionary which
is returned by get_hash()
