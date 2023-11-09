import sys
import re

CAPITALIZATION_EXCEPTIONS = {
    "NFTOKEN": "NFToken",
    "URITOKEN": "URIToken",
    "URI": "URI",
    "UNL": "UNL",
    "XCHAIN": "XChain",
    "DID": "DID",
    "ID": "ID",
    "AMM": "AMM",
}

if len(sys.argv) != 2:
    print("Usage: python " + sys.argv[0] + " path/to/rippled/src/ripple/")
    sys.exit(1)

########################################################################
#  Get all necessary files from rippled
########################################################################


def read_file(filename):
    with open(filename, "r") as f:
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


# Translate from rippled string format to what the binary codecs expect
def translate(inp):
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

    parts = inp.split("_")
    result = ""
    for part in parts:
        if part in CAPITALIZATION_EXCEPTIONS:
            result += CAPITALIZATION_EXCEPTIONS[part]
        else:
            result += part[0:1].upper() + part[1:].lower()
    return result


########################################################################
#  Serialized type processing
########################################################################
print("{")
print('  "TYPES": {')
print('    "Done": -1,')

type_hits = re.findall(
    r"^ *STYPE\(STI_([^ ]*?) *, *([0-9-]+) *\) *\\?$", sfield_h, re.MULTILINE
)
if len(type_hits) == 0:
    type_hits = re.findall(
        r"^ *STI_([^ ]*?) *= *([0-9-]+) *,?$", sfield_h, re.MULTILINE
    )
for x in range(len(type_hits)):
    print(
        '    "'
        + translate(type_hits[x][0])
        + '": '
        + type_hits[x][1]
        + ("," if x < len(type_hits) - 1 else "")
    )

print("  },")

########################################################################
#  Ledger entry type processing
########################################################################
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


########################################################################
#  SField processing
########################################################################
print('  "FIELDS": [')
# The ones that are harder to parse directly from SField.cpp
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
    if t == "LEDGERENTRY" or t == "TRANSACTION" or t == "VALIDATION" or t == "METADATA":
        return "false"
    return "true"


def isSigningField(t, notSigningField):
    if notSigningField == "notSigning":
        return "false"
    if t == "LEDGERENTRY" or t == "TRANSACTION" or t == "VALIDATION" or t == "METADATA":
        return "false"
    return "true"


# Parse SField.cpp for all the SFields and their serialization info
sfield_hits = re.findall(
    r'^ *CONSTRUCT_[^\_]+_SFIELD *\( *[^,\n]*,[ \n]*"([^\"\n ]+)"[ \n]*,[ \n]*([^, \n]+)[ \n]*,[ \n]*([0-9]+)(,.*?(notSigning))?',
    sfield_cpp,
    re.MULTILINE,
)
for x in range(len(sfield_hits)):
    print("    [")
    print('      "' + sfield_hits[x][0] + '",')
    print("      {")
    print('        "nth": ' + sfield_hits[x][2] + ",")
    print('        "isVLEncoded": ' + isVLEncoded(sfield_hits[x][1]) + ",")
    print('        "isSerialized": ' + isSerialized(sfield_hits[x][1]) + ",")
    print(
        '        "isSigningField": '
        + isSigningField(sfield_hits[x][1], sfield_hits[x][4])
        + ","
    )
    print('        "type": "' + translate(sfield_hits[x][1]) + '"')
    print("      }")
    print("    ]" + ("," if x < len(sfield_hits) - 1 else ""))

print("  ],")

########################################################################
#  TER code processing
########################################################################
print('  "TRANSACTION_RESULTS": {')
ter_h = str(ter_h).replace("[[maybe_unused]]", "")

ter_code_hits = re.findall(
    r"^ *((tel|tem|tef|ter|tes|tec)[A-Z_]+)( *= *([0-9-]+))? *,? *(\/\/[^\n]*)?$",
    ter_h,
    re.MULTILINE,
)
upto = -1
last = ""

for x in range(len(ter_code_hits)):
    if ter_code_hits[x][3] != "":
        upto = int(ter_code_hits[x][3])

    current = ter_code_hits[x][1]
    if current != last and last != "":
        print("")
        pass
    last = current

    print(
        '    "'
        + ter_code_hits[x][0]
        + '": '
        + str(upto)
        + ("," if x < len(ter_code_hits) - 1 else "")
    )

    upto += 1

print("  },")

########################################################################
#  Transaction type processing
########################################################################
print('  "TRANSACTION_TYPES": {')
print('    "Invalid": -1,')


# Translate TX types from rippled names to the actual string names
def translate_tx_types(inp):
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
            if part in CAPITALIZATION_EXCEPTIONS:
                inp += CAPITALIZATION_EXCEPTIONS[part]
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
        + translate_tx_types(hits[x][0])
        + '": '
        + hits[x][2]
        + ("," if x < len(hits) - 1 else "")
    )

print("  }")
print("}")
