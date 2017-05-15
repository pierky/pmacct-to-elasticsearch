pmacct-to-elasticsearch
=======================

**pmacct-to-elasticsearch** is a python script designed to read output from **pmacct** daemons, to process it and to store it into **ElasticSearch**. It works with both *memory* and *print* plugins and, optionally, it can perform **manipulations on data** (such as to add fields on the basis of other values).

.. image:: img/data_flow.png
        :align: center

1. **pmacct daemons** collect IP accounting data and process them with their plugins;
2. data are stored into **in-memory-tables** (*memory* plugins), **JSON or CSV files** (*print* plugins);
3. **crontab jobs** (*memory* plugins) or **trigger scripts** (*print* plugins) are invoked to execute pmacct-to-elasticsearch;
4. pmacct's output records are finally processed by **pmacct-to-elasticsearch**, which reads them from stdin (*memory* plugins) or directly from file.

Optionally, some **data transformations** can be configured, to allow pmacct-to-elasticsearch to **add or remove fields** to/from the output documents that are sent to ElasticSearch for indexing. These additional fields may be useful to enhance graphs and reports legibility, or to add a further level of aggregation or filtering.

Installation
------------

Install the program using pip:

.. code:: bash

  pip install pmacct-to-elasticsearch
        
Then clone the repository and run the ./install script to setup your system:

.. code:: bash

  cd /usr/local/src/
  git clone https://github.com/pierky/pmacct-to-elasticsearch.git
  cd pmacct-to-elasticsearch/
  ./install
  
Configuration
-------------

Please refer to the `CONFIGURATION.md`_ file. The `TRANSFORMATIONS.md`_ file contains details about data transformations configuration.

.. _CONFIGURATION.md: CONFIGURATION.md
.. _TRANSFORMATIONS.md: TRANSFORMATIONS.md

A simple tutorial on pmacct integration with ElasticSearch/Kibana using pmacct-to-elasticsearch can be found at http://blog.pierky.com/integration-of-pmacct-with-elasticsearch-and-kibana.

Future work
-----------

- Add support of more pmacct output formats (Apache Avro, ...).

Author
------

Pier Carlo Chiodi - https://pierky.com/

Blog: https://blog.pierky.com/ Twitter: `@pierky <https://twitter.com/pierky>`_
