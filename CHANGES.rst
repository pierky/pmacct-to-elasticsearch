Changelog
=========

0.3.1
-----

- Fix: ES 6.2 compatibility.

  `Issue #9 <https://github.com/pierky/pmacct-to-elasticsearch/issues/9>`.

0.3.0
-----

- New: **CSV** output support.

  The ``InputFormat`` option in the plugin configuration file can be used to instruct pmacct-to-elasticsearch to parse CSV output from pmacct.

- New: **Multithreading** support.

  The ``ReaderThreads`` option in the plugin configuration file sets the number of threads used to process pmacct's output.

- New: More command line arguments.

  The command line arguments under the *Configuration options* group can be used to override settings done on the plugin configuration file.

- Fix issue with index creation on ElasticSearch 5.x.

  Thanks to Kristoffer Olsson and Daniel Lindberg for reporting this and for their extensive support.

- Improved template for index creation.

- Fix an issue with transformations.

0.2.0
-----

- New feature: HTTP Authentication support for ES API.

0.1.0
-----

First release.
