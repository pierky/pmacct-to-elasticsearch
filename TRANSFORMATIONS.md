BE WARNED: Transformations and Conditions are highly experimental, test them
before using them in a production system.

Transofrmations allow pmacct-to-elasticsearch to analyze input data and add
additional information to the output that it sends to ElasticSearch. These
additional fields may be useful to enhance graphs and reports legibility, or
to add a further level of aggregation or filtering.

For example: given an input set of data reporting the ingress router and
interface, a transformation matrix allow to add a new field with the peer's
friendly name:

     pmacct output = pmacct-to-elasticsearch input:
     { "peer_ip_src": "10.0.0.1", "iface_in": 10, "packets": 2, "bytes": 100 }

     pmacct-to-elasticsearch output = ElasticSearch indexed document:
     { "peer_ip_src": "10.0.0.1", "iface_in": 10, "packets": 2, "bytes": 100, "peer_name": "MyUpstreamProvider" }

Transofrmations are based on **Conditions** and **Actions**: if a condition is
satisfied then all its actions are performed.

For each record received from pmacct, pmacct-to-elasticsearch verifies if its
fields match one or more conditions and, in case, performs the related actions.

## Syntax

Syntax is JSON based and refers to the "Transformations" key referenced in the
[CONFIGURATION.md](CONFIGURATION.md) file:

     {
        ...
        "Transformations": [
                {
                        "Conditions": <Conditions>,
                        "Actions": <Actions>
                },
                {
                        "Conditions": <Conditions>,
                        "Actions": <Actions>
                },
                {
                        ...
                }
        ]
        ...
     }

### Conditions

- **Conditions** = `[ ( "AND"|"OR" ), <Criteria1>, <Criteria2>, <CriteriaN> ]`

   If omitted, "AND" is used.

- **Criteria** = `<Conditions> | { "<name>": <value> (, "__op__": "[ = | < | <= | > | >= | != | in | notin ] " ) }`

   If omitted, operator is "=" (equal).
   For "in" and "notin" operators, a list is expected as *value*:

          { "field": [ "a", "b" ], "__op__": "in" }

Examples:

       Bob, older than 15:
               [ { "Name": "Bob" }, { "Age": 16, "__op__": ">=" } ]

       Bob or Tom:
               [ "OR", { "Name": "Bob" }, { "Name": "Tom" } ]

       Bob, only if he's older than 15, otherwise Tom or Lisa, only if she's older than 20

               [ "OR", [ { "Name": "Bob" }, { "Age": 16, "__op__": ">=" } ], { "Name": "Tom" }, [ { "Name": "Lisa" }, { "Age": 20, "__op__": ">="  } ] ]

### Actions

- **Actions** = ```[ { "Type": "<ActionType>", <action's details> },
                { "Type": "<ActionType>", <action's details> },
                { ... } ]```

- **ActionType** == "**AddField**", action's details =

        "Name": "<destination_field_name>",
        "Value": "<new_value>"

   Sets the "*destination_field_name*" field to "*new_value*"; if
   "*destination_field_name*" field does not exist, creates it.

   Macros can be used in "*new_value*".

- **ActionType** == "**AddFieldLookup**", action's details =

        "Name": "<destination_field_name>",
        "LookupFieldName": "<key_field>",
        "LookupTable": {
                "<key1>": "<new_value1>",
                "<key2>": "<new_value2>",
                "<keyN>": "<new_valueN>"
        }
        "LookupTableFile": "<path_to_table>"

   If "*key_field*" field is present in the input, searches the lookup
   table for "*key_field*" value and, eventually, sets
   "*destination_field_name*" field to the "*new_value*" found.
   If "*key_field*" is not present in the input dataset but a "*" key is
   present in the lookup table then its value is used to set
   "*destination_field_name*" field.

   The lookup table can be written directly in the configuration file
   (using "LookupTable" key) or referenced as an external file
   ("LookupTableFile" key).

   Macros can be used in "*new_value*".

- **ActionType** == "**DelField**", action's details =

        "Name": "<field_name>"

   If "*field_name*" is present in the output dataset, it is removed.

## Macros

Macros can be used to refer to fields already present in the output dataset;
their syntax is $fieldname.

## Examples

1. Add peer's friendly name to ingress traffic:

          { ...
          "Transformations": [
                  {
                          "Conditions": [ { "peer_ip_src": "10.0.0.1" }, { "iface_in": 1 } ],
                          "Actions": [ { "Type": "AddField", "Name": "peer_name", "Value": "MyUpstream1" } ]
                  },
                  {
                          "Conditions": [ { "peer_ip_src": "192.168.0.1" }, { "iface_in": 10 } ],
                          "Actions": [ { "Type": "AddField", "Name": "peer_name", "Value": "MyUpstream2" } ]
                  }
          ]
          ... }

   If "peer_ip_src" = "10.0.0.1" and "iface_in" = 1, set "peer_name" to
   "MyUpstream1". Similar for the second condition.

          input:
             { "peer_ip_src": "10.0.0.1", "iface_in": 1, "packets": 2, "bytes": 100 }
             { "peer_ip_src": "192.168.0.1", "iface_in": 10, "packets": 4, "bytes": 400 }
          output:
             { "peer_ip_src": "10.0.0.1", "iface_in": 1, "packets": 2, "bytes": 100, "peer_name": "MyUpstream1" }
             { "peer_ip_src": "192.168.0.1", "iface_in": 10, "packets": 4, "bytes": 400, "peer_name": "MyUpstream2" }

2. Add Autonomous System name to source AS:

          { ...
          "Transformations": [
                  "Conditions": [ { "as_src": "", "__op__": "!=" } ],
                  "Actions": [
                          { "Type": "AddFieldLookup", "Name": "as_src_name",
                          "LookupFieldName": "as_src",
                          "LookupTableFile": "/etc/p2es/AS_map.json"
                  ]
          ]
          ... }


          /etc/p2es/AS_map.json:

               {
                     "36040":        "$as_src - YouTube",
                     "15169":        "$as_src - Google",
                     "20940":        "$as_src - Akamai",
                     "*":            "$as_src"
               }

     If "as_src" is not empty, use its value to lookup the table in
     **/etc/p2es/AS_map.json**; if a corresponding value is found, use it to fill the
     new "as_src_name" field with "ASN - Name" values, otherwise fill if with
     only the ASN.

          input:
                    { "as_src": 36040, "packets": 1, "flows": 1, "bytes": 100 }
                    { "as_src": 20940, "packets": 5, "flows": 5, "bytes": 500 }
                    { "as_src": 32934, "packets": 8, "flows": 4, "bytes": 300 }
          output:
                    { "as_src": 36040, "packets": 1, "flows": 1, "bytes": 100, "as_src_name": "36040 - YouTube" }
                    { "as_src": 20940, "packets": 5, "flows": 5, "bytes": 500, "as_src_name": "20940 - Akamai" }
                    { "as_src": 32934, "packets": 8, "flows": 4, "bytes": 300, "as_src_name": "32934" }

3. Another version of example 1: add peer's friendly name to ingress traffic:


          { ...
          "Transformations": [
                  {
                          "Conditions": [ "AND", { "peer_ip_src": "", "__op__": "!=" }, { "iface_in": "", "__op__": "!=" } ],
                          "Action": [ { "Type": "AddField", "Name": "temporary1", "Value": "$peer_ip_src-$iface_in" } ]
                  },
                  {
                          "Conditions": [ { "temporary1": "", "__op__": "!=" } ],
                          "Actions": [
                                  {
                                          "Type": "AddFieldLookup",
                                          "Name": "peer_name",
                                          "LookupFieldName": "temporary1",
                                          "LookupTable": {
                                                  "10.0.0.1-1": "MyUpstream1",
                                                  "192.168.0.1-10": "MyUpstream2"
                                          }
                                  },
                                  { "Type": "DelField", "Name": "temporary1" }
                          ]
                  }
          ]
          ... }

     If "peer_ip_src" and "iface_in" are not empty, add a new temporary field named
     "temporary1" with "*peer_ip_src*-*iface_in*". Next, if "temporary1" field has
     been filled and it's not empty, use it to lookup the table in order to find the
     corresponding peer's friendly name. Finally, remove the temporary field from
     the output dataset.
