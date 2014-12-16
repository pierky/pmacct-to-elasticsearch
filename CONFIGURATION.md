# Configuration of pmacct-to-elasticsearch

## How it works

pmacct-to-elasticsearch reads pmacct JSON output and sends it to ElasticSearch.

It works properly with two kinds of pmacct plugins: "memory" and "print".
The former, "memory", needs data to be passed to pmacct-to-elasticsearch's
stdin, while the latter, "print", needs a file to be written by pmacct
daemons, where pmacct-to-elasticsearch is instructed to read data from.

For "print" plugins, a crontab job is needed to run pmacct client and to
redirect its output to pmacct-to-elasticsearch; for "memory" plugins the pmacct
daemon can directly execute pmacct-to-elasticsearch. More details will follow
within the rest of this document.

<p align="center"><img src="https://raw.github.com/pierky/pmacct-to-elasticsearch/master/img/config_files.png"/></p>

Print plugins are preferable because, in case of pmacct daemon graceful
restart or shutdown, data are written to the output file and the trigger
is regularly executed.

## 1-to-1 mapping with pmacct plugins

For each pmacct's plugin you want to be processed by pmacct-to-elasticsearch
a configuration file must be present in the *CONF_DIR* directory to tell the
program how to process its output.

Configuration file's name must be in the format *PluginName*.conf, where
*PluginName* is the name of the pmacct plugin to which the file refer to.

Example:

     /etc/pmacct/nfacctd.conf:

        ! nfacctd configuration example
        plugins: memory[my_mem], print[my_print]

     /etc/p2es/my_mem.conf
     /etc/p2es/my_print.conf

Basically these files tell pmacct-to-elasticsearch:

1. where to read pmacct's output from;

2. how to send output to ElasticSearch;

3. (optionally) which transformations must be operated.

To run pmacct-to-elasticsearch the first argument must be the *PluginName*,
in order to allow it to figure out what to do:

        pmacct-to-elasticsearch my_print

## Configuration file syntax

These files are in JSON format and contain the following keys:

- **LogFile** [required]: path to the log file used by pmacct-to-elasticsearch
   to write any error encountered while processing the output.

   It can contain some macros, which are replaced during execution:
   *$PluginName*, *$IndexName*, *$Type*

   Log file will be automatically rotated every 1MB, for 3 times.

   **Default**: "/var/log/pmacct-to-elasticsearch-$PluginName.log"

- **ES_URL** [required]: URL of ElasticSearch HTTP API.

   **Default**: "http://localhost:9200"

- **ES_IndexName** [required]: name of the ElasticSearch index used to store
   pmacct-to-elasticsearch output.

   It may contain Python strftime codes (http://strftime.org/) in order
   to have periodic indices.

   Example:
     "netflow-%Y-%m-%d" to have daily indices (netflow-YYYY-MM-DD)

   Default: no default provided

- **ES_Type** [required]: ElasticSearch document type (_type field) used to store
   pmacct-to-elasticsearch output. Similar to tables in relational DB.

   From the official reference guide
   http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/_basic_concepts.html#_type:

   > Within an index, you can define one or more types. A type is a logical
   > category/partition of your index whose semantics is completely up to
   > you. In general, a type is defined for documents that have a set of
   > common fields. For example, let.s assume you run a blogging platform
   > and store all your data in a single index. In this index, you may
   > define a type for user data, another type for blog data, and yet
   > another type for comments data."

   Default: no default provided

- **ES_IndexTemplateFileName** [required]: name of the file containing the
   template to be used when creating a new index. The file must be in the
   *CONF_DIR* directory.

   **Default**: new-index-template.json (included in pmacct-to-elasticsearch)

   The default template provided with pmacct-to-elasticsearch has the
   _source field enabled; if you want to save some storage disable it
   by editing the new-index-template.json file:

           "_source" : { "enabled" : false }

- **ES_FlushSize** [required]: how often to flush data to ElasticSearch BULK API.

   Set it to 0 to only send data once the whole input has been processed.

   **Default**: 5000 lines

- **InputFile** [optional]: used mainly when configuring pmacct print plugins.
   File used by pmacct-to-elasticsearch to read input data from (it
   should coincide with pmacct's print plugin output file).
   If omitted pmacct-to-elasticsearch will read data from stdin.

- **Transformations** [optional]: the transformation matrix used to add new
   fields to the output document sent to ElasticSearch for indexing.

   More details in the [TRANSFORMATIONS.md](TRANSFORMATIONS.md) file.

This is an example of a basic configuration file:

     {
          "ES_IndexName": "netflow-%Y-%m-%d",
          "ES_Type": "ingress_traffic",
          "InputFile": "/var/lib/pmacct/ingress_traffic.json",
     }

## Plugins configuration

### Memory plugins

For "memory" plugins, a crontab job is needed in order to periodically read
(and clear) the in-memory-table that pmacct uses to store data:

Example of a command scheduled in crontab:

        pmacct -l -p /var/spool/pmacct/my_mem.pipe -s -O json -e | pmacct-to-elasticsearch my_mem

In the example above, the pmacct client reads the in-memory-table
referenced by the **/var/spool/pmacct/my_mem.pipe** file and write the JSON
output to stdout, which in turn is redirected to the stdin of
pmacct-to-elasticsearch, that is executed with the **my_mem** argument in order
to let it to load the right configuration from **/etc/p2es/my_mem.conf**.

### Print plugins

For "print" plugins, the crontab job is not required but a feature of pmacct
may be used instead: the **print_trigger_exec** config key.
The print_trigger_exec key allows pmacct to directly run
pmacct-to-elasticsearch once the output has been fully written to the output
file. Since pmacct does not allow to pass arguments to programs executed using
the print_trigger_exec key, a trick is needed in order to let
pmacct-to-elasticsearch to understand what configuration to use: a trigger
file must be created for each "print" plugin and it has to execute the
program with the proper argument.

Example:

     /etc/pmacct/nfacctd.conf:

        ! nfacctd configuration example
        plugins: print[my_print]
        print_output_file[my_print]: /var/lib/pmacct/my_print.json
        print_output[my_print]: json
        print_trigger_exec[my_print]: /etc/p2es/triggers/my_print

     /etc/p2es/triggers/my_print:

        #!/bin/sh
        /usr/local/bin/pmacct-to-elasticsearch my_print &

     # chmod u+x /etc/p2es/triggers/my_print

     /etc/p2es/my_print.conf:

        {
                ...
                "InputFile": "/var/lib/pmacct/my_print.json"
                ...
        }

In the example, the nfacctd daemon has a plugin named **my_print** that writes
its JSON output to **/var/lib/pmacct/my_print.json** and, when done, executes
the **/etc/p2es/triggers/my_print** program. The trigger program, in turn, runs
pmacct-to-elasticsearch with the **my_print** argument and detaches it.
The **my_print.conf** file contains the "InputFile" configuration key that points
to the aforementioned JSON output file (**/var/lib/pmacct/my_print.json**), where
the program will read data from.

The trigger program may also be a symbolic link to the **default_trigger** script
provided, which runs pmacct-to-elasticsearch with its own file name as first
argument:

     # cd /etc/p2es/triggers/
     # ln -s default_trigger my_print
     
     /etc/p2es/triggers/default_trigger:
          
          #!/bin/sh
          PLUGIN_NAME=`basename $0`
          /usr/local/bin/pmacct-to-elasticsearch $PLUGIN_NAME &

Otherwise, remember to use the full path of pmacct-to-elasticsearch in order 
to avoid problems with a stripped version of the *PATH* environment variable.
