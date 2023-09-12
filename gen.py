import sys
import re

if len(sys.argv) != 2:
    print("Usage: python " + sys.argv[0] + " path/to/rippled/src/ripple/")
    sys.exit(1)


def read_file(filename):
    with open(filename) as f:
        return f.read()


sfield_h_fn = sys.argv[1] + "/protocol/SField.h"
sfield_cpp_fn = sys.argv[1] + "/protocol/impl/SField.cpp"
ledgerformats_h_fn = sys.argv[1] + "/protocol/LedgerFormats.h"
ter_h_fn = sys.argv[1] + "/protocol/TER.h"
txformats_h_fn = sys.argv[1] + "/protocol/TxFormats.h"

sfield_h = read_file(sfield_h_fn)
sfield_cpp = read_file(sfield_cpp_fn)
ledgerformats_h = read_file(ledgerformats_h_fn)
ter_h = read_file(ter_h_fn)
txformats_h = read_file(txformats_h_fn)

capitalization_exceptions = {
    "NFTOKEN": "NFToken",
    "UNL": "UNL",
    "XCHAIN": "XChain",
    "ID": "ID",
    "AMM": "AMM",
}


def translate(inp):
    inp_pattern = re.compile(inp)
    if re.match(r"^UINT", inp):
        if re.search(r"256|160|128", inp):
            return inp.replace("UINT", "Hash")
        else:
            return inp.replace("UINT", "UInt")
    if inp == "OBJECT" or inp == "ARRAY":
        return "ST" + inp[0:1].upper() + inp[1:].lower()
    if inp == "ACCOUNT":
        return "AccountID"
    if inp == "LEDGERENTRY":
        return "LedgerEntry"
    if inp == "NOTPRESENT":
        return "NotPresent"
    if inp == "PATHSET":
        return "PathSet"
    if inp == "VL":
        return "Blob"
    if inp == "DIR_NODE":
        return "DirectoryNode"
    if inp == "PAYCHAN":
        return "PayChannel"

    if "_" in inp:
        parts = inp.split("_")
        inp = ""
        for part in parts:
            if part in capitalization_exceptions:
                inp += capitalization_exceptions[part]
            else:
                inp += part[0:1].upper() + part[1:].lower()
        return inp
    return inp[0:1].upper() + inp[1:].lower()


print("{")
print('  "TYPES": {')
print('    "Done": -1,')

type_hits = re.findall(r"^ *STI_([^ ]*?) *= *([0-9-]+) *,?$", sfield_h, re.MULTILINE)
for x in range(len(type_hits)):
    print(
        '    "'
        + translate(type_hits[x][0])
        + '": '
        + type_hits[x][1]
        + ("," if x < len(type_hits) - 1 else "")
    )

print("  },")
print('  "LEDGER_ENTRY_TYPES": {')
print('    "Invalid": -1,')


def unhex(x):
    if (x + "")[0:2] == "0x":
        return str(int(x, 16))
    return x


lt_hits = re.findall(
    r" *lt([A-Z_]+)[^\n=]*= *([^,]+),?$", ledgerformats_h, re.MULTILINE
)
for x in range(len(lt_hits)):
    if lt_hits[x][0] == "ANY":
        print(
            '    "'
            + translate(lt_hits[x][0])
            + '": '
            + "-3"
            + ("," if x < len(lt_hits) - 1 else "")
        )
    elif lt_hits[x][0] == "CHILD":
        print(
            '    "'
            + translate(lt_hits[x][0])
            + '": '
            + "-2"
            + ("," if x < len(lt_hits) - 1 else "")
        )
    else:
        print(
            '    "'
            + translate(lt_hits[x][0])
            + '": '
            + unhex(lt_hits[x][1])
            + ("," if x < len(lt_hits) - 1 else "")
        )
print("  },")
print('  "FIELDS": [')
print(
    """    [
      "Generic",
      {
        "nth": 0,
        "isVLEncoded": false,
        "isSerialized": false,
        "isSigningField": false,
        "type": "Unknown"
      }
    ],
    [
      "Invalid",
      {
        "nth": -1,
        "isVLEncoded": false,
        "isSerialized": false,
        "isSigningField": false,
        "type": "Unknown"
      }
    ],
    [
      "ObjectEndMarker",
      {
        "nth": 1,
        "isVLEncoded": false,
        "isSerialized": true,
        "isSigningField": true,
        "type": "STObject"
      }
    ],
    [
      "ArrayEndMarker",
      {
        "nth": 1,
        "isVLEncoded": false,
        "isSerialized": true,
        "isSigningField": true,
        "type": "STArray"
      }
    ],
    [
      "hash",
      {
        "nth": 257,
        "isVLEncoded": false,
        "isSerialized": false,
        "isSigningField": false,
        "type": "Hash256"
      }
    ],
    [
      "index",
      {
        "nth": 258,
        "isVLEncoded": false,
        "isSerialized": false,
        "isSigningField": false,
        "type": "Hash256"
      }
    ],
    [
      "taker_gets_funded",
      {
        "nth": 258,
        "isVLEncoded": false,
        "isSerialized": false,
        "isSigningField": false,
        "type": "Amount"
      }
    ],
    [
      "taker_pays_funded",
      {
        "nth": 259,
        "isVLEncoded": false,
        "isSerialized": false,
        "isSigningField": false,
        "type": "Amount"
      }
    ],"""
)


def isVLEncoded(t):
    if t == "VL" or t == "ACCOUNT" or t == "VECTOR256":
        return "true"
    return "false"


def isSerialized(t):
    if t == "LEDGERENTRY" or t == "TRANSACTION" or t == "VALIDATION":
        return "false"
    return "true"


def isOne(t, v):
    if t == "LEDGERENTRY" or t == "TRANSACTION" or t == "VALIDATION" or t == "METADATA":
        return "1,"
    return v


def isSigningField(t):
    if t == "notSigning":
        return "false"
    return "true"


hits = re.findall(
    r'^ *CONSTRUCT_[^\_]+_SFIELD *\( *[^,\n]*,[ \n]*"([^\"\n ]+)"[ \n]*,[ \n]*([^, \n]+)[ \n]*,[ \n]*([0-9]+)(,.*?(notSigning))?',
    sfield_cpp,
    re.MULTILINE,
)
for x in range(len(hits)):
    print("    [")
    print('      "' + hits[x][0] + '",')
    print("      {")
    print('        "nth": ' + isOne(hits[x][1], hits[x][2] + ","))
    print('        "isVLEncoded": ' + isVLEncoded(hits[x][1]) + ",")
    print('        "isSerialized": ' + isSerialized(hits[x][1]) + ",")
    print('        "isSigningField": ' + isSigningField(hits[x][4]) + ",")
    print('        "type": "' + translate(hits[x][1]) + '"')
    print("      }")
    print("    ]" + ("," if x < len(hits) - 1 else ""))

print("  ],")
print('  "TRANSACTION_RESULTS": {')
ter_h = str(ter_h).replace("[[maybe_unused]]", "")

hits = re.findall(
    r"^ *((tel|tem|tef|ter|tes|tec)[A-Z_]+)( *= *([0-9-]+))? *,? *(\/\/[^\n]*)?$",
    ter_h,
    re.MULTILINE,
)
upto = -1
last = ""
for x in range(len(hits)):
    # print(hits[x])
    if hits[x][3] != "":
        upto = int(hits[x][3])

    current = hits[x][1]
    if current != last and last != "":
        print("")
        pass
    last = current

    print('    "' + hits[x][0] + '": ' + str(upto) + ("," if x < len(hits) - 1 else ""))

    upto += 1

print("  },")
print('  "TRANSACTION_TYPES": {')
print('    "Invalid": -1,')


def ttranslate(inp):
    if inp == "REGULAR_KEY_SET":
        inp = "SET_REGULAR_KEY"

    if inp == "NICKNAME_SET":
        inp = "NICK_NAME_SET"

    if inp == "AMENDMENT":
        inp = "ENABLE_AMENDMENT"

    if inp == "FEE":
        inp = "SET_FEE"

    if inp == "SPINAL_TAP":
        inp = "TICKET_CANCEL"

    if inp == "HOOK_SET":
        inp = "SET_HOOK"

    inp = inp.replace("PAYCHAN", "PAYMENT_CHANNEL")

    if "_" in inp:
        parts = inp.split("_")
        inp = ""
        for part in parts:
            if part in capitalization_exceptions:
                inp += capitalization_exceptions[part]
            else:
                inp += part[0:1].upper() + part[1:].lower()
        return inp
    return inp[0:1].upper() + inp[1:].lower()


hits = re.findall(
    r"^ *tt([A-Z_]+) *(\[\[[^\]]+\]\])? *= *([0-9]+) *,?.*$", txformats_h, re.MULTILINE
)
for x in range(len(hits)):
    print(
        '    "'
        + ttranslate(hits[x][0])
        + '": '
        + hits[x][2]
        + ("," if x < len(hits) - 1 else "")
    )

print("  }")
print("}")
