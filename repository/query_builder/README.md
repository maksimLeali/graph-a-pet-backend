  Dynamic SQL Query Builder

=========================

This repository contains a set of Python functions designed to dynamically build SQL queries based on provided filters, join conditions, and table relationships. The goal is to facilitate the creation of complex SQL queries without manually writing SQL code.

Table of Contents
-----------------

- [Table of Contents](#table-of-contents)
- [Requirements](#requirements)
- [Configuration](#configuration)
- [Functions](#functions)
  - [build\_join](#build_join)
  - [build\_where](#build_where)
  - [format\_main\_filters](#format_main_filters)
  - [format\_range\_filters](#format_range_filters)
  - [format\_search\_filters](#format_search_filters)
  - [format\_fixed\_filters](#format_fixed_filters)
  - [format\_list\_filters](#format_list_filters)
  - [build\_count](#build_count)
  - [build\_query](#build_query)
  - [format\_values\_to\_restore](#format_values_to_restore)
  - [build\_restore](#build_restore)
- [Logging](#logging)
- [Usage](#usage)
- [License](#license)

Requirements
------------

*   Python 3.x
*   The following Python packages:
    *   pydash
    *   api.errors (custom module)
    *   utils (custom module)
    *   utils.logger (custom module)
    *   config (custom module)

Configuration
-------------

The code uses a configuration file to retrieve metadata about the database schema and tables. This configuration is stored in `cfg` and accessed via `tables_common_properties`.

Example configuration structure:

    {
      "db_scheme": {
        "tables": {
          "table_name": {
            "alias": "alias_name",
            "children": ["child_table1", "child_table2"],
            "other_table_ref": "reference_field",
            "search_columns": ["column1", "column2"]
          }
        }
      }
    }
    

Functions
---------

### build\_join

Constructs SQL `JOIN` statements between tables based on the provided join conditions.

**Parameters:**

*   `parent`: The parent table name.
*   `join`: A dictionary of join conditions.
*   `already_joined`: A list of tables that have already been joined.
*   `join_string`: A list to store the resulting join strings.

### build\_where

Constructs SQL `WHERE` clauses based on the provided filters.

**Parameters:**

*   `table`: The table name.
*   `already_joined`: A list of tables that have already been joined.
*   `join_string`: A list to store the resulting join strings.
*   `filters`: A dictionary of filter conditions (`and`, `or`, `not`).

### format\_main\_filters

Formats the main filter conditions for a table.

**Parameters:**

*   `table`: The table name.
*   `filters`: A dictionary of filter conditions.
*   `already_joined`: A list of tables that have already been joined.
*   `join_string`: A list to store the resulting join strings.
*   `operator`: The logical operator (`AND`, `OR`, `NOT`) to connect the filters.

### format\_range\_filters

Formats range filters for fields (e.g., `field > min_value AND field < max_value`).

**Parameters:**

*   `alias`: The table alias.
*   `filters`: A dictionary of range filters.
*   `operator`: The logical operator to connect the filters (default is `AND`).

### format\_search\_filters

Formats search filters, allowing partial matches on specified fields.

**Parameters:**

*   `table`: The table name.
*   `filters`: A dictionary of search filters.

### format\_fixed\_filters

Formats fixed-value filters (e.g., `field = 'value'`).

**Parameters:**

*   `alias`: The table alias.
*   `filters`: A dictionary of fixed filters.
*   `operator`: The logical operator to connect the filters (default is `AND`).

### format\_list\_filters

Formats filters for fields that should match any value in a list.

**Parameters:**

*   `alias`: The table alias.
*   `filters`: A dictionary of list filters.
*   `operator`: The logical operator to connect the filters (default is `AND`).

### build\_count

Constructs a SQL `COUNT` query to count the number of distinct records that match the given filters.

**Parameters:**

*   `table`: The table name.
*   `filters`: A dictionary of filter conditions.

### build\_query

Constructs a SQL `SELECT` query to retrieve records based on the provided filters, pagination, and ordering.

**Parameters:**

*   `table`: The table name.
*   `pagination`: A dictionary with pagination settings (`page_size`, `page`).
*   `ordering`: A dictionary with ordering settings (`order_by`, `order_direction`).
*   `filters`: A dictionary of filter conditions.

### format\_values\_to\_restore

Formats values for insertion into the database, converting lists to arrays and dictionaries to JSON.

**Parameters:**

*   `data`: A dictionary of data to format.

### build\_restore

Constructs a SQL `INSERT` query to restore (insert) data into a table.

**Parameters:**

*   `table`: The table name.
*   `data`: A dictionary of data to insert.

Logging
-------

The code uses a custom logging module to trace the execution flow and debug the query construction process. The following logging functions are used:

*   `logger.input()`
*   `logger.output()`
*   `logger.check()`
*   `logger.error()`
*   `logger.warning()`

Usage
-----

1\. Ensure all required modules are installed.

2\. Configure the `cfg` object with your database schema and table metadata.

3\. Use the provided functions to build and execute SQL queries.

Example:

    from config import cfg
    from query_builder import build_query
    
    cfg = {
        "db_scheme": {
            "tables": {
                "users": {
                    "alias": "u",
                    "children": ["orders"],
                    "other_table_ref": "user_id",
                    "search_columns": ["name", "email"]
                },
                "orders": {
                    "alias": "o",
                    "children": [],
                    "other_table_ref": "user_id",
                    "search_columns": ["order_number"]
                }
            }
        }
    }
    
    filters = {
        "and": {
            "fixed": {"status": "active"},
            "lists": {"roles": ["admin", "user"]}
        }
    }
    
    query = build_query("users", filters=filters)
    print(query)
    

License
-------

This project is licensed under the MIT License. See the `LICENSE` file for details.