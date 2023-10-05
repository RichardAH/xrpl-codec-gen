if (process.argv.length != 3)
{
    console.log("Usage: " + process.argv[0] + " " + process.argv[1] + " path/to/rippled/src/ripple/")
    process.exit(1);
}

////////////////////////////////////////////////////////////////////////
//  Get all necessary files from rippled
////////////////////////////////////////////////////////////////////////
const sfield_h_fn = process.argv[2] + '/protocol/SField.h'
const sfield_cpp_fn = process.argv[2] + '/protocol/impl/SField.cpp'
const ledgerformats_h_fn = process.argv[2] + '/protocol/LedgerFormats.h'
const ter_h_fn = process.argv[2] + '/protocol/TER.h'
const txformats_h_fn = process.argv[2] + '/protocol/TxFormats.h'

const fs = require('fs')

const sfield_h = fs.readFileSync(sfield_h_fn).toString('utf-8');
const sfield_cpp = fs.readFileSync(sfield_cpp_fn).toString('utf-8');
const ledgerformats_h = fs.readFileSync(ledgerformats_h_fn).toString('utf-8');
const ter_h = fs.readFileSync(ter_h_fn).toString('utf-8')
const txformats_h = fs.readFileSync(txformats_h_fn).toString('utf-8');

const capitalization_exceptions = {
    "NFTOKEN": "NFToken",
    "URITOKEN": "URIToken",
    "UNL": "UNL",
    "XCHAIN": "XChain",
    "ID": "ID",
    "AMM": "AMM",
}

// Translate from rippled string format to what the binary codecs expect
function translate(inp) {
    try
    {
        if (inp.match(/^UINT/m))
            if (inp.match(/256/m) || inp.match(/160/m) || inp.match(/128/m))
                return inp.replace("UINT", "Hash");
            else
                return inp.replace("UINT", "UInt");
        if (inp == 'OBJECT' || inp == 'ARRAY')
            return 'ST' + inp.substr(0,1).toUpperCase() + inp.substr(1).toLowerCase();
        if (inp == 'AMM')
            return inp;
        if (inp == 'ACCOUNT')
            return 'AccountID';
        if (inp == 'LEDGERENTRY')
            return 'LedgerEntry';
        if (inp == 'NOTPRESENT')
            return 'NotPresent';
        if (inp == 'PATHSET')
            return 'PathSet';
        if (inp == 'VL')
            return 'Blob';
        if (inp == 'DIR_NODE')
            return 'DirectoryNode';
        if (inp == 'PAYCHAN')
            return 'PayChannel';
        if (inp == 'URI_TOKEN')
            return 'URIToken';

        const parts = inp.split('_');
        let result = '';
        for (x in parts)
            if (capitalization_exceptions[parts[x]] != null) {
                result += capitalization_exceptions[parts[x]];
            } else
                result += parts[x].substr(0,1).toUpperCase() + parts[x].substr(1).toLowerCase();
        return result;
    } catch (e) {
        console.log(e, 'inp="' + inp + '"')
    }
};

////////////////////////////////////////////////////////////////////////
//  Serialized type processing
////////////////////////////////////////////////////////////////////////
console.log('{')
console.log('  "TYPES": {')
console.log('    "Done": -1,');

let hits = [... sfield_h.matchAll(/^ *STI_([^ ]*?) *= *([0-9-]+) *,?$/mg)];
for (let x = 0; x < hits.length; ++x)
    console.log("    \"" + translate(hits[x][1]) + "\": " +  hits[x][2] + (x < hits.length - 1 ? ",": ""))

console.log('  },');

////////////////////////////////////////////////////////////////////////
//  Ledger entry type processing
////////////////////////////////////////////////////////////////////////
console.log('  "LEDGER_ENTRY_TYPES": {')
console.log('    "Invalid": -1,')

const unhex = (x)=>{
    x = ('' + x).trim();
    if (x.substr(0,2) == '0x')
        return '' + parseInt(x)
    if (x.substr(0,1) == "'" && x.length == 3)
        return x.charCodeAt(1);
    return x
}
hits = [... ledgerformats_h.matchAll(/ *lt([A-Z_]+)[^\n=]*= *([^,]+),?$/mg)];
for (let x = 0; x < hits.length; ++x)
    if (hits[x][1] === 'ANY')
        console.log("    \"" + translate(hits[x][1])  + "\": " +  -3 + (x < hits.length - 1 ? ",": ""))
    else if (hits[x][1] === 'CHILD')
        console.log("    \"" + translate(hits[x][1])  + "\": " +  -2 + (x < hits.length - 1 ? ",": ""))
    else
        console.log("    \"" + translate(hits[x][1])  + "\": " +  unhex(hits[x][2]) + (x < hits.length - 1 ? ",": ""))
console.log('  },');

////////////////////////////////////////////////////////////////////////
//  SField processing
////////////////////////////////////////////////////////////////////////
console.log('  "FIELDS": [');
// The ones that are harder to parse directly from SField.cpp
console.log(`    [
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
    ],`);

const isVLEncoded = (t)=>{
    if (t == 'VL' || t == 'ACCOUNT' || t == 'VECTOR256')
        return 'true';
    return 'false';
}

const isSerialized = (t)=>{
    if (t == 'LEDGERENTRY' || t == 'TRANSACTION' || t == 'VALIDATION')
        return 'false';
    return 'true';
}

const isOne = (t, v)=>{
    if (t == 'LEDGERENTRY' || t == 'TRANSACTION' || t == 'VALIDATION' || t == 'METADATA')
        return 1 + ','
    return v;
}

const isSigningField = (t)=>{
    if (t == 'notSigning')
        return 'false';
    return 'true';
}

// Parse SField.cpp for all the SFields and their serialization info
hits = [... sfield_cpp.matchAll(
    /^ *CONSTRUCT_[^\_]+_SFIELD *\( *[^,\n]*,[ \n]*"([^\"\n ]+)"[ \n]*,[ \n]*([^, \n]+)[ \n]*,[ \n]*([0-9]+)(,.*?(notSigning))?/mg) ]
    for (let x = 0; x < hits.length; ++x)
{
    console.log('    [');
    console.log('      "' + hits[x][1] + '",')
    console.log('      {')
    console.log('        "nth": ' + isOne(hits[x][2], hits[x][3] + ','))
    console.log('        "isVLEncoded": ' + isVLEncoded(hits[x][2]) + ',')
    console.log('        "isSerialized": ' + isSerialized(hits[x][2]) + ',')
    console.log('        "isSigningField": ' + isSigningField(hits[x][5]) + ',')
    console.log('        "type": "' + translate(hits[x][2]) + '"')
    console.log('      }')
    console.log('    ]' + (x < hits.length - 1 ? ',' : ''));
}

console.log('  ],')

////////////////////////////////////////////////////////////////////////
//  TER code processing
////////////////////////////////////////////////////////////////////////
console.log('  "TRANSACTION_RESULTS": {')
const cleaned_ter_h = (''+ter_h).replace("[[maybe_unused]]", '')

hits = [... cleaned_ter_h.matchAll(/^ *((tel|tem|tef|ter|tes|tec)[A-Z_]+)( *= *([0-9-]+))? *,? *(\/\/[^\n]*)?$/mg) ]
let upto = -1;
let last = ""
for (let x = 0; x < hits.length; ++x)
{
    if (hits[x][4] !== undefined)
        upto = hits[x][4];

    let current = hits[x][2]
    if (current != last && last != "")
        console.log("")
    last = current

    console.log('    "' + hits[x][1] + '": ' + upto + (x < hits.length - 1 ? ',' : ''))

    upto++;
}

console.log('  },');

////////////////////////////////////////////////////////////////////////
//  Transaction type processing
////////////////////////////////////////////////////////////////////////
console.log('  "TRANSACTION_TYPES": {');
console.log('    "Invalid": -1,');

// Translate TX types from rippled names to the actual string names
function translate_tx_names(inp) {
    try
    {
        if (inp == 'REGULAR_KEY_SET')
            inp = 'SET_REGULAR_KEY'

        if (inp == 'NICKNAME_SET')
            inp = 'NICK_NAME_SET'

        if (inp == 'AMENDMENT')
            inp = 'ENABLE_AMENDMENT'

        if (inp == 'FEE')
            inp = 'SET_FEE'

        if (inp == 'SPINAL_TAP')
            inp = 'TICKET_CANCEL'

        if (inp == 'HOOK_SET')
            inp = 'SET_HOOK'

        inp = inp.replace("PAYCHAN", 'PAYMENT_CHANNEL')

        const parts = inp.split('_');
        let result = '';
        for (x in parts)
        {
            if (capitalization_exceptions[parts[x]] != null) {
            result += capitalization_exceptions[parts[x]];;
            } else
            result += parts[x].substr(0,1).toUpperCase() + parts[x].substr(1).toLowerCase();

        }
        return result;
    } catch (e) {
        console.log(e, 'inp="' + inp + '"')
    }
};

hits = [ ... txformats_h.matchAll(/^ *tt([A-Z_]+) *(\[\[[^\]]+\]\])? *= *([0-9]+) *,?.*$/mg) ]
for (let x = 0; x < hits.length; ++x)
{
    console.log('    "' + translate_tx_names(hits[x][1]) + '": ' + hits[x][3] + (x < hits.length - 1 ? ',' : ''));
}

console.log('  }');
console.log('}');
