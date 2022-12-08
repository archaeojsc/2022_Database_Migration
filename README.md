
# Database Migration Project

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
  does have a statutory mandate to *permanently archive and curate* project
  data!

## Phase I -- Data gathering and exploration

* [Experimentation and testing code](db_connection_tests.py)
* [Completed utility functions code](db_utilities_extraction.py)

