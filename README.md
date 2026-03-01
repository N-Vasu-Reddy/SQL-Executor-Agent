# Intelligent SQL ReAct Agent

## Overview

This project implements a dual-mode SQL assistant built using
LangChain's ReAct agent architecture.
The system can either execute SQL queries against a live database or
generate SQL queries from a provided schema.

The core architectural objective is to preserve autonomous tool
selection in execution mode while maintaining safe, schema-grounded
query generation.

------------------------------------------------------------------------

## Operating Modes

### 1. Execution Mode (Database Connected)

If a database URI is provided, the agent:

1.  Fetches schema dynamically from the database
2.  Generates SQL grounded strictly in the schema
3.  Executes the SQL query
4.  Returns structured output including:
    -   Executed SQL
    -   Query results

### 2. Generation Mode (Schema Only)

If no database URI is provided, the system:

1.  Accepts schema as text input
2.  Generates SQL using the provided schema
3.  Returns SQL only (no execution)

------------------------------------------------------------------------

## Architecture

### High-Level Flow

![Sys Architecture](https://github.com/N-Vasu-Reddy/SQL-Executor-Agent/blob/main/architecture/Screenshot%202026-03-01%20174657.png)
------------------------------------------------------------------------

## ReAct Execution Flow

![Agent Execution Flow](https://github.com/N-Vasu-Reddy/SQL-Executor-Agent/blob/main/architecture/Screenshot%202026-03-01%20174946.png)

------------------------------------------------------------------------

## Core Components

### Tools

-   **fetch_schema_tool** -- Retrieves schema directly from the database
-   **generate_sql_tool** -- Generates SQL strictly grounded in schema
-   **execute_sql_tool** -- Executes SQL safely and returns structured results

### Safety Controls

-   Blocks destructive statements (`DROP`, `DELETE`, `ALTER`, `TRUNCATE`)
-   Prevents multi-statement execution
-   Blocks SQL comment-based injection
-   Uses transactional execution (`engine.begin()`)

------------------------------------------------------------------------

## Output Format

**Execution** mode returns:

``` json
{
  "executed_sql": "...",
  "result": "..."
}
```

**Generation** mode returns raw SQL only.

------------------------------------------------------------------------

## Installation

Install dependencies:

``` bash
pip install -r requirements.txt
```

Create a `.env` file:

    GROQ_API_KEY=your_api_key_here

Run the application:

``` bash
streamlit run app.py
```

------------------------------------------------------------------------

## Design Principles

1.  Preserve autonomous ReAct reasoning in execution mode
2.  Ground all SQL in validated schema
3.  Separate reasoning from execution
4.  Return structured, verifiable outputs
5.  Support both connected and offline use cases

------------------------------------------------------------------------
