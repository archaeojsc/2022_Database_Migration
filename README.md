
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

There appear to be 909 separate MS Access databases, which collective represent
118 different table schema. Not known yet how many of these are duplicates due
to updating MS Access versions. There are 89 databases with unique table
structures. Most of these, however, appear to be based on the most common
schema. These seem to be modified versions of a template database, with the
addition of either specialized or redundant (copied?) tables.

A relatively small portion of the databases are obviously special-purpose
applications, and some appear to be attempts to update older DBase or FoxPro
databases to MS Access.

The vast majority of the databases follow some version of the table structure:  

* Project Information table (`Project`, `Project Info`, or `Project_
  Information`)
* Site Information table (`Site` or `Site Info`)
* Provenience Information table (`Provenience`, with a few breaking provenience
  into *unit* and *level* sub-tables)
* Artifact Catalog table (sometimes split into *site* and *non-site* catalogs)
* Code List utility lookup table (`CODELIST`, `CodeList`, or `Codelist`)

### Next Step

Compile list of all unique tables (after correcting for minor naming convention
differences) and find out how many versions of the table definitions exist
(i.e., variations on table fields).
