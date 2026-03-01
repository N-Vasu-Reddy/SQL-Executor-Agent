import os
import re
import ast
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.agents import create_agent
from langchain_community.utilities import SQLDatabase

# LOAD .env VARIABLES
load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found in .env file")



# LLM CONFIG
llm = ChatGroq(
    model_name="openai/gpt-oss-20b",
    temperature=0
)

# TOOL 1: FETCH SCHEMA
@tool
def fetch_schema_tool(db_uri: str) -> str:
    """Fetch schema from the database."""
    try:
        db = SQLDatabase.from_uri(db_uri)
        return db.get_table_info()
    except Exception as e:
        return f"Schema fetch error: {str(e)}"


# TOOL 2: GENERATE SQL
@tool
def generate_sql_tool(question: str, schema: str) -> str:
    """Generate SQL query using question and schema."""
    prompt = f"""
Generate one valid SQL query.

Schema:
{schema}

Question:
{question}

Rules:
- Use ONLY tables and columns from schema
- Do NOT invent tables or columns
- Output SQL only
"""
    response = llm.invoke([
        SystemMessage(content="You are an expert SQL generator."),
        HumanMessage(content=prompt)
    ])
    return response.content.strip()


# SQL SAFETY CHECK
def is_safe_query(sql: str) -> bool:
    forbidden = ["DROP", "DELETE", "ALTER", "TRUNCATE"]

    if ";" in sql.strip().rstrip(";"):
        return False

    if "--" in sql or "/*" in sql:
        return False

    for word in forbidden:
        if re.search(rf"\b{word}\b", sql.upper()):
            return False

    return True


# TOOL 3: EXECUTE SQL
@tool
def execute_sql_tool(sql: str, db_uri: str) -> str:
    """Execute SQL query and return executed SQL + results."""

    if not is_safe_query(sql):
        return "Blocked: Unsafe SQL detected."

    engine = create_engine(db_uri)

    try:
        with engine.begin() as conn:
            result = conn.execute(text(sql))

            if result.returns_rows:
                rows = result.fetchall()
                columns = result.keys()
                formatted = [dict(zip(columns, row)) for row in rows]
                output = {
                    "executed_sql": sql,
                    "result": formatted
                }
            else:
                output = {
                    "executed_sql": sql,
                    "result": f"{result.rowcount} row(s) affected"
                }

        return str(output)

    except Exception as e:
        return f"Execution failed: {str(e)}"


# AGENT SETUP
tools = [
    fetch_schema_tool,
    generate_sql_tool,
    execute_sql_tool
]

SYSTEM_PROMPT_EXECUTION = """
You are a SQL execution agent.

If db_uri is provided:
- Fetch schema using fetch_schema_tool.
- Generate SQL.
- Execute SQL.
- Return structured output from execute_sql_tool.
- No explanations.
"""

SYSTEM_PROMPT_GENERATION = """
You are a SQL query generator.

If db_uri is NOT provided:
- Use provided schema text.
- Generate SQL only.
- Do NOT execute.
- Return only SQL.
- No explanations.
"""

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT_EXECUTION
)


st.markdown("## 🧠 Intelligent SQL Assistant")
st.caption("Execution Mode (DB) or Generation Mode (Schema Only)")

st.divider()


# INPUT SECTION
db_uri = st.text_input(
    "Database URI (Optional for execution mode)",
    placeholder="mysql+pymysql://root:password@localhost:3306/student_db"
)

schema_text = None

if not db_uri:
    schema_text = st.text_area(
        "Provide Schema (Required if DB URI not provided)",
        placeholder="students(id, name, subject_id)\nsubjects(id, name, department)"
    )

question = st.text_area("Ask your question")


# RUN BUTTON
if st.button("Run"):

    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    if db_uri:
        # EXECUTION MODE
        with st.spinner("Executing..."):
            user_input = f"""
Database URI:
{db_uri}

Question:
{question}
"""
            result = agent.invoke({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_EXECUTION},
                    {"role": "user", "content": user_input}
                ]
            })

            output = result.get("output") or result["messages"][-1].content

            try:
                parsed = ast.literal_eval(output)

                st.markdown("### Executed SQL")
                st.code(parsed.get("executed_sql"), language="sql")

                st.markdown("### Result")

                result_data = parsed.get("result")

                if isinstance(result_data, list):
                    if result_data:
                        st.dataframe(result_data, use_container_width=True)
                    else:
                        st.info("Query executed. No rows returned.")
                else:
                    st.success(result_data)

            except:
                st.error(output)

    else:
        # GENERATION MODE
        if not schema_text:
            st.warning("Please provide schema when DB URI is not given.")
            st.stop()

        with st.spinner("Generating SQL..."):
            response = llm.invoke([
                SystemMessage(content=SYSTEM_PROMPT_GENERATION),
                HumanMessage(content=f"""
Schema:
{schema_text}

Question:
{question}
""")
            ])

            st.markdown("### Generated SQL")
            st.code(response.content.strip(), language="sql")