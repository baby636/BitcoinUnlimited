#!/usr/bin/env python3
# Copyright (c) 2018 The Bitcoin Unlimited developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import time
from sys import stdin, stdout
import shlex

keyTypes = {"i":"initial", "c":"changeable"}

valueTypes = ["u64c", "vector"]

cmdTable = {}

def readKEY(tokens):
    keytype = next(tokens)
    name = next(tokens)
    prefix = int(next(tokens), 0)
    suffix = int(next(tokens), 0)
    valtype = next(tokens)
    if keytype not in keyTypes:
        raise RuntimeError("Unknown key type '%s'." % type)
    if valtype not in valueTypes:
        raise RuntimeError("Unknown value type '%s'." % valtype)
    if prefix<0 or prefix>0xffff:
        raise RuntimeError("Prefix out of range (%d)." % prefix)
    if suffix<0 or suffix>0xffff:
        raise RuntimeError("Suffix out of range (%d)." % suffix)
    return name, {
        "keytype" : keytype,
        "name" : name,
        "prefix" : prefix,
        "suffix" : suffix,
        "valtype" : valtype }

cmdTable.update({"KEY" : readKEY})

def readTable(infile):
    tokens = shlex.shlex(infile)

    result = {}
    while True:
        try:
            tok = next(tokens)
        except StopIteration:
            return result

        if tok not in cmdTable:
            raise RuntimeError("Unknown command '%s'." % tok)

        k, v = cmdTable[tok](tokens)
        if k in result:
            raise RuntimeError("Duplicate key '%s'." % k)
        result[k] = v

def writeTableCPPH(outfile, table):
    """ Write data of interest from key table as C++ header file suitable
    for inclusion into a bitcoind build. """
    print(
"""// Extended version message key definition file
// WARNING: This file has been autogenerated.
// DO NOT CHANGE. CHANGES WILL BE OVERWRITTEN.

#ifndef BITCOIN_XVERSIONKEYS_H
#define BITCOIN_XVERSIONKEYS_H
#include <unordered_map>
namespace XVer
{
""", file = outfile)

    # set keys in enum
    print("enum {", file = outfile)
    for k in sorted(table.keys()):
        x = table[k]
        print ("      %40s = 0x%016xUL," % (x["name"], (x["prefix"]<<16)|x["suffix"]),
               file = outfile)
    print("}; // enum keys\n\n\n", file = outfile)

    # map keys to their string values (for printing etc)
    print("const std::unordered_map<uint64_t, std::string> name = {", file = outfile)
    for k in sorted(table.keys()):
        x = table[k]
        print ("    {%40s, %42s }," % (x["name"], '"'+x["name"]+'"'), file = outfile)
    print("}; // const unordered_map name\n\n\n", file = outfile)

    # value types (note that the value of the enum can change for new value types and
    # should never be used directly!)
    print("enum {", file = outfile)
    valtypes = set(x["valtype"] for x in table.values())
    for x in sorted(valtypes):
        print ("    %20s," % ("xvt_"+x), file = outfile)
    print("}; // enum valtypes\n\n\n", file = outfile)


    # map keys to their expected value type
    print("const std::unordered_map<uint64_t, int> valtype = {", file = outfile)
    for k in sorted(table.keys()):
        x = table[k]
        print ("    {%40s, %42s }," % (x["name"], "xvt_"+x["valtype"]), file = outfile)
    print("}; // const unordered_map valtype\n\n\n", file = outfile)

    # set key types in enum
    print("enum keyType {", file = outfile)
    for x in keyTypes:
        print ("    "+keyTypes[x]+",", file = outfile)
    print("}; // enum keyType\n\n\n", file = outfile)

    # map keys to their expected value type
    print("const std::unordered_map<uint64_t, keyType> mapKeyType = {", file = outfile)
    for k in sorted(table.keys()):
        x = table[k]
        print ("    {%40s, %42s }," % (x["name"], keyTypes[x["keytype"]]), file = outfile)
    print("}; // const unordered_map keytype\n\n\n", file = outfile)

    print(
"""
} // namespace XVer
#endif
""", file = outfile)


if __name__ == "__main__":
    table = readTable(stdin)
    writeTableCPPH(stdout, table)