
# Database Governance Assessment and Migration Project

Initial experiments to transfer collection of data stored in separate Microsoft
Access databases into a consolidated data management system.

There are numerous challenges to this project:

* There are an estimated 2,000 separate database files stored on the network
  storage, which may or may not be related to project data to be archived or
  consolidated
* Database files were found in multiple directories and sub-directories. Again,
  there is no obvious way (e.g., file name conventions) to distinguish project
  data from extraneous files.
* Project database templates have changed several times over the roughly 25
  years in which they have been used. Each database may have similar but
  non-identical structure and schema.
* Some legacy project data was converted from FoxPro or DBase databases (i.e.,
  pre-1995).
* The program office has *no* formal digital data governance or strategy, but
  does have a statutory mandate to permanently *archive* and *curate* project
  data.

## Phase I -- Data gathering and exploration

* [Experimentation and testing code](db_connection_tests.py)
* [Completed utility functions code](db_utilities_extraction.py)

### Current assessment

There appear to be 909 active MS Access databases, which collective represent
118 different table schema. It is not known yet how many of these are duplicates
due to updating MS Access versions, and does not include `*.mdb.old`[^fn1] or
`*.DBF`[^fn2] files. Including these legacy databases increases the total to
2,234 files.

[^fn1]: Archive copies of databases that were updated to new versions?
[^fn2]: Old FoxPro databases, typically flat-file database structure.

There are 89 databases with unique table structures. Most of these, however,
appear to be based on the most common schema. These seem to be modified versions
of a template database, with the addition of either specialized or redundant
(copied?) tables. A relatively small portion of the databases are obviously
special-purpose applications, and some appear to be attempts to update older
DBase or FoxPro databases to MS Access.

Another common category appear to be subsets of other databases, which are used
to transfer field collection data to external curatorial databases. These would
need to be excluded since the duplicate other records.

The vast majority of the databases follow some version of the table structure:  

* Project Information table (`Project`, `Project Info`, or `Project_
  Information`)
* Site Information table (`Site` or `Site Info`)
* Provenience Information table (`Provenience`, with a few breaking provenience
  into *unit* and *level* sub-tables)
* Artifact Catalog table (sometimes split into *site* and *non-site* catalogs)
* Code List utility lookup table (`CODELIST`, `CodeList`, or `Codelist`)

These are consistent with the overall template in use for the past 15 years,
with some notable variations. Aside from variable table naming conventions,
these tables often contain variable field definitions. For example, the most
common table `Provenience` occurs in 821 of the files but has 88 distinct field
definitions.

### Next Steps

* Compile list of all unique tables (after correcting for minor naming
  convention differences) and find out how many versions of the table
  definitions exist (i.e., variations on table fields).

* Look at options for retrieving data from FoxPro files with
  [`dbfread`](https://dbfread.readthedocs.io/en/latest/index.html) or
  [`dpfpy`](https://dbfpy.sourceforge.net/).
