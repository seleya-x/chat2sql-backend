import os
import sys
import json
import re
import pandas as pd
from openai import OpenAI

# Set up OpenRouter environment
api_key = "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"
api_base = "https://openrouter.ai/api/v1"
model = "o3-mini-high"  # OpenRouter model

# Check if API key is set
if not api_key:
    print("Error: OPENROUTER_API_KEY environment variable is not set.")
    print(
        "Please set your OpenRouter API key using: export OPENROUTER_API_KEY=your_api_key"
    )

# Initialize the OpenAI client with OpenRouter configuration
client = OpenAI(api_key=api_key, base_url=api_base)


def load_schema():
    """Load the database schema from the JSON file and process it into a structured format."""
    try:
        # Construct the schema file path relative to this script's directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(
            current_dir, "database_schema_relationships_llm.json"
        )

        with open(schema_path, "r") as f:
            schema_data = json.load(f)

        # Process the schema into a structured format for the prompt
        schema_text = "DATABASE SCHEMA:\n\n"

        # Track relationships for later use
        all_relationships = {}

        # Process each table
        for table_name, fields in schema_data.items():
            schema_text += f"TABLE: {table_name}\n"

            # Process each field in the table
            for field_name, field_info in fields.items():
                schema_text += f"  - {field_name}"

                # Add description if available
                if "description" in field_info:
                    schema_text += f": {field_info['description']}"

                # Add possible values if available
                if "values" in field_info:
                    schema_text += f"\n    Possible values: {field_info['values']}"

                # Add relationships if available
                if "relationships" in field_info:
                    schema_text += (
                        f"\n    Relationships: {', '.join(field_info['relationships'])}"
                    )

                    # Store relationship for the relationship map
                    relationship_key = f"{table_name}.{field_name}"
                    all_relationships[relationship_key] = field_info["relationships"]

                schema_text += "\n"

            schema_text += "\n"

        # Add a relationship map section
        schema_text += "KEY TABLE RELATIONSHIPS:\n\n"

        # Process relationships to create a more readable format
        processed_relationships = set()
        for source, targets in all_relationships.items():
            for target in targets:
                # Create a unique identifier for this relationship to avoid duplicates
                rel_id = f"{source} <-> {target}"
                rev_rel_id = f"{target} <-> {source}"

                if (
                    rel_id not in processed_relationships
                    and rev_rel_id not in processed_relationships
                ):
                    schema_text += f"- {source} connects to {target}\n"
                    processed_relationships.add(rel_id)

        # Add common query patterns section
        schema_text += "\nCOMMON QUERY PATTERNS:\n\n"
        schema_text += "1. To find deals with specific acquirors or targets:\n"
        schema_text += "   - Use deals_summary table with filters on acquiror_name or target_name\n\n"
        schema_text += "2. To find fees associated with deals:\n"
        schema_text += (
            "   - Join fees_verification_consolidated with deals_summary on deal_id\n\n"
        )
        schema_text += "3. To find advisor information:\n"
        schema_text += "   - Use the advisor table and join with fees_verification_consolidated using advisor_name\n\n"
        schema_text += "4. To distinguish between sellside (target) and buyside (acquiror) advisors:\n"
        schema_text += (
            "   - Filter fees_verification_consolidated on the 'type' field\n"
        )

        return schema_text
    except Exception as e:
        print(f"Error loading schema: {e}")
        return ""


def generate_sql_query(human_query, schema_text):
    prompt = f"""
    You are an agent designed to interact with an MySQL database.
    Given an input question, create a syntactically correct MySQL query to run, then look at the results of the query and return the answer.
    Limit your query to at most 10 results using the LIMIT clause.
    You can order the results by a relevant column to return the most interesting examples in the database.
    Never query for all the columns from a specific table, only ask for a the few relevant columns given the question.
    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

    If the question does not seem related to the database, just return "I don't know" as the answer.
    
    Given the following database schema:

    {schema_text}

    And the human query:
    {human_query}

    ** Important instructions: **
    1. Only use tables and fields that exist in the schema provided
    2. Use the relationships between tables to create proper JOIN conditions
    3. For queries about fees:
    - Use the fees_verification_consolidated table for fee information
    - The 'type' field indicates whether the advisor represented the target ('target') or acquiror ('acquiror')
    - 'Sellside' refers to advisors representing the target company (type = 'target')
    - 'Buyside' refers to advisors representing the acquiring company (type = 'acquiror')
    4. For queries about deals:
    - Use the deals_summary table for transaction details
    - Join with other tables using the deal_id field
    5. Select specific relevant columns rather than using SELECT *
    6. Include descriptive column aliases to make the results more readable (e.g., ds.acquiror_name AS acquiror)
    7. Use appropriate WHERE conditions to filter the data as requested
    8. If needed, use the advisor table to get additional information about advisors
    9. Use table aliases for readability (e.g., deals_summary AS ds)
    10. For date-based queries, ensure proper date formatting
    11. If aggregating data, use appropriate GROUP BY clauses
    12. For large result sets, consider adding ORDER BY clauses for better organization
    13. Include target_name and date information when relevant to provide context

    ** Specific Guidelines for Common Queries: **
    1. For transaction size filters:
        - The rank_value field in deals_summary is in millions of dollars
        - For ranges like "$1bn-$5bn", use rank_value BETWEEN 1000 AND 5000

    2. For queries involving company names:
        - Always look into deals_summary table first when looking for target names or acquiror names
        - ** IMPORTANT ** Always search the entire hierarchal relationship of the company which includes the 'parent company' and 'ultimate parent company'. 
        - When searching for an acquiror always include: acquiror_name, acquiror_parent_name and acquiror_ultimate_parent_name in the WHERE conditions of the query    
        - Convert strings to lower case and use "LIKE '%string%'
        - Example: "SELECT ... FROM ... WHERE LOWER(ds.target_name) LIKE '%blackstone%' OR LOWER(ds.target_parent_name) LIKE '%blackstone%' OR LOWER(ds.target_ultimateparent_name) LIKE '%blackstone%'"

    3. For country-specific transactions:
        - Use company.country_headquarters to filter by country
        - For "U.S. transactions", check if either acquiror or target is in the United States
        - Join deals_summary with company table using appropriate permid fields

    4. Queries involving sector or industry:
        - Filter using company.gics_sector or company.gics_industry
        - For queries on 'healthcare', use company.gics_sector = 'Health Care'
        - Use your knowledge to select the most similar SECTOR from this sector list: ["Consumer Discretionary", "Materials", "Consumer Staples", "Information Technology", "Utilities", "Industrials", "Energy", "Health Care", "Financials", "Communication Services", "Real Estate"]
        - Use your knowledge to select the most similar INDUSTRY from this industry list: ["Aerospace & Defense, Air Freight & Logistics, Automobile Components, Automobiles, Banks, Beverages, Biotechnology, Broadline Retail, Building Products, Capital Markets, Chemicals, Commercial Services & Supplies, Communications Equipment, Construction & Engineering, Construction Materials, Consumer Finance, Consumer Staples Distribution & Retail, Containers & Packaging, Distributors, Diversified Consumer Services, Diversified REITs, Diversified Telecommunication Services, Electric Utilities, Electrical Equipment, Electronic Equipment, Instruments & Components, Energy Equipment & Services, Entertainment, Financial Services, Food Products, Gas Utilities, Ground Transportation, Health Care Equipment & Supplies, Health Care Providers & Services, Health Care REITs, Health Care Technology, Hotel & Resort REITs, Hotels, Restaurants & Leisure, Household Durables, Household Products, IT Services, Independent Power and Renewable Electricity Producers, Industrial Conglomerates, Industrial REITs, Insurance, Interactive Media & Services, Leisure Products, Life Sciences Tools & Services, Machinery, Marine Transportation, Media, Metals & Mining, Mortgage Real Estate Investment Trusts (REITs), Multi-Utilities, Office REITs, Oil, Gas & Consumable Fuels, Paper & Forest Products, Passenger Airlines, Personal Care Products, Pharmaceuticals, Professional Services, Real Estate Management & Development, Residential REITs, Retail REITs, Semiconductors & Semiconductor Equipment, Software, Specialized REITs, Specialty Retail, Technology Hardware, Storage & Peripherals, Textiles, Apparel & Luxury Goods, Tobacco, Trading Companies & Distributors, Transportation Infrastructure, Water Utilities, Wireless Telecommunication Services"]
        - For excluding REITs(e.g., "excl. REITs"): exclude where gics_sector = 'Real Estate' AND gics_industry LIKE '%REIT%'
        - Example: [query="Select deals in the electric vehicles", answer="SELECT ... FROM ... WHERE LOWER(company.gics_sector) LIKE '%consumer discretionary%' OR LOWER(company.gics_industry LIKE '%automobiles%' OR LOWER(company.gics_industry LIKE '%automobile components%'"]

    5. Time-based queries (e.g., "past 10 years"):
        - Use deals_summary.date_announced or deals_summary.date_effective
        - Filter with date_announced >= DATE_SUB(CURDATE(), INTERVAL 10 YEAR)

    6. Queries involving deal details and deal characteristics:
        - Always look into deal_sheet table first before go to deal_summary table.
        - The schema includes three new tables: deal_sheet, refinitiv_fields, and deals_details
        - These tables are related: deal_sheet.code, deals_details.name, and refinitiv_fields.trcode all refer to the same field codes
        - Use these relationships to join these tables when needed
        - deal_sheet contains field names and their codes
        - refinitiv_fields contains additional information about fields
        - deals_details contains detailed transaction information

    7. Queries involving people:
        - Always look into the person and person_history tables before going to deals_summary. 
        - Join person and person_history with person_permid
        - Join person_history and company with person_history.company_id and company.permid
        - Use the first_name and last_name to look up people in the person table. Adjust names to lowercase in the query. Do not use the full_name.
        - Ensure that a person is actively affiliated with the company at the time of announcement using position_start and position end_date
        - If position_end_date is null, assume they are currently affiliated with the company
        - When looking up positions like 'CEO' in position_name, use LIKE %CEO%

    8. Queries involving advisors:
        - Always look into the advisor_fees table before going to deal_history_consolidated and fees_verification_consolidated tables
        - When querying for strings in fee_context, fee_relative, selection_process, engagement_context, engagement_role, convert string to lower case and use "LIKE '%string%'"



    

    Query Structure Best Practices:
    - Start with the main table that contains the core information needed
    - Join only the necessary tables to fulfill the query requirements
    - Use LEFT JOINs when you want to include records even if there's no match in the joined table
    - Use INNER JOINs when you only want records that have matches in both tables
    - Use clear and consistent indentation for readability
    - When querying for strings, convert to lower case and use the LIKE '%string%' operator

    Generate an MySQL query that answers the human query. Only provide the MySQL statement as your answer. If the question does not seem related to the database, just return "I don't know" as the answer"""

    try:
        response = client.chat.completions.create(
            model=model,  # Use the OpenRouter model variable
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10000,  # OpenRouter uses max_tokens instead of max_completion_tokens
        )

        # Debug response is now disabled for cleaner output
        # print("OpenRouter API Response:")
        # print(response)

        # Check if the response has the expected structure
        if (
            hasattr(response, "choices")
            and len(response.choices) > 0
            and hasattr(response.choices[0], "message")
        ):
            sql_query = response.choices[0].message.content.strip()
        else:
            print("Unexpected response structure from OpenRouter API")
            raise ValueError("Invalid response structure from OpenRouter API")

        # Clean the SQL query for direct execution
        # Remove markdown code blocks if present
        if sql_query.startswith("```") and "```" in sql_query[3:]:
            sql_query = sql_query.split("```", 2)[1]
            # Remove SQL language identifier if present
            if sql_query.lower().startswith("sql"):
                sql_query = sql_query[3:].lstrip()

        # Ensure the query ends with a semicolon
        if not sql_query.rstrip().endswith(";"):
            sql_query = sql_query.rstrip() + ";"

        # Remove any explanatory text before or after the SQL query
        lines = sql_query.split("\n")
        clean_lines = []
        in_query = False

        for line in lines:
            line = line.rstrip()
            # Skip empty lines
            if not line.strip():
                continue
            # Check if this line looks like SQL
            if any(
                keyword in line.upper()
                for keyword in [
                    "SELECT",
                    "FROM",
                    "WHERE",
                    "JOIN",
                    "GROUP BY",
                    "ORDER BY",
                    "HAVING",
                    "LIMIT",
                    "INSERT",
                    "UPDATE",
                    "DELETE",
                ]
            ):
                in_query = True
            if in_query:
                clean_lines.append(line)

        # If we found SQL lines, use them; otherwise use the original (might be a simple query)
        if clean_lines:
            sql_query = "\n".join(clean_lines)

        return sql_query
    except Exception as e:
        error_message = str(e)
        if not api_key:
            print(
                f"Error generating SQL query: API key not set. Please set the OPENROUTER_API_KEY environment variable."
            )
        else:
            print(f"Error generating SQL query: {error_message}")
        return None


def main():
    if len(sys.argv) < 2:
        print('Usage: python agent.py "<human_query>"')
        sys.exit(1)

    human_query = sys.argv[1]
    schema_text = load_schema()
    if not schema_text:
        print("Failed to load the database schema.")
        sys.exit(1)

    sql = generate_sql_query(human_query, schema_text)
    if sql:
        # Format the SQL query for better readability
        formatted_sql = format_sql(sql)

        # Output only the formatted SQL query with no headers or extra text
        print(formatted_sql)

        # Write the SQL query to a text file silently
        try:
            with open("sql_query.txt", "w") as f:
                f.write(formatted_sql)
        except Exception:
            pass  # Silently fail if file writing fails
    else:
        print("SQL query generation failed.")


def format_sql(sql):
    """Format SQL query for better human readability."""
    # Replace multiple spaces with a single space
    sql = " ".join(sql.split())

    # Add newlines after specific SQL keywords for better readability
    keywords = [
        "FROM",
        "WHERE",
        "JOIN",
        "LEFT JOIN",
        "RIGHT JOIN",
        "INNER JOIN",
        "GROUP BY",
        "ORDER BY",
        "HAVING",
        "LIMIT",
        "UNION",
        "UNION ALL",
    ]

    # First, handle the SELECT statement separately to format each column on a new line
    if "SELECT" in sql.upper():
        # Split the query at the SELECT keyword
        parts = re.split(r"\bSELECT\b", sql, flags=re.IGNORECASE, maxsplit=1)

        if len(parts) > 1:
            prefix = parts[0]  # Usually empty
            rest = parts[1]  # The rest of the query

            # Find where the FROM clause starts
            from_match = re.search(r"\bFROM\b", rest, re.IGNORECASE)
            if from_match:
                select_part = rest[: from_match.start()].strip()
                post_select = rest[from_match.start() :].strip()

                # Split the SELECT columns by commas, but be careful with functions
                # that might contain commas within parentheses
                columns = []
                current_col = ""
                paren_level = 0

                for char in select_part:
                    if char == "(" and not (
                        current_col.endswith("'") and not current_col.endswith("\\'")
                    ):
                        paren_level += 1
                        current_col += char
                    elif char == ")" and not (
                        current_col.endswith("'") and not current_col.endswith("\\'")
                    ):
                        paren_level -= 1
                        current_col += char
                    elif char == "," and paren_level == 0:
                        columns.append(current_col.strip())
                        current_col = ""
                    else:
                        current_col += char

                if current_col.strip():
                    columns.append(current_col.strip())

                # Format the SELECT part with each column on a new line
                formatted_select = "SELECT\n    " + ",\n    ".join(columns)

                # Reconstruct the query
                sql = prefix + formatted_select + "\nFROM" + post_select[4:]
            else:
                # If FROM is not found, just add a newline after SELECT
                sql = prefix + "SELECT\n    " + rest

    # Process other SQL keywords
    for keyword in keywords:
        # Only replace if the keyword is a whole word (not part of another word)
        # Don't add a newline for FROM since we already handled it
        if keyword != "FROM":
            sql = re.sub(
                r"\b" + keyword + r"\b", "\n" + keyword, sql, flags=re.IGNORECASE
            )

    # Remove any leading newlines
    sql = sql.lstrip("\n")

    # Add indentation for better readability
    lines = sql.split("\n")
    formatted_lines = []

    # Process each line to ensure proper indentation
    for line in lines:
        line_stripped = line.strip()

        # Main SQL keywords should be at the leftmost position
        if any(
            line_stripped.upper().startswith(keyword)
            for keyword in [
                "SELECT",
                "FROM",
                "WHERE",
                "GROUP BY",
                "ORDER BY",
                "HAVING",
                "LIMIT",
            ]
        ):
            formatted_lines.append(line_stripped)
        # Items in the SELECT statement should be indented
        elif line_stripped.startswith(",") or (
            len(formatted_lines) > 0
            and formatted_lines[-1].strip().startswith("SELECT")
        ):
            # Remove any leading comma and whitespace
            clean_line = line_stripped.lstrip(",").strip()
            formatted_lines.append("    " + clean_line)
        # JOIN statements should be at the same level as FROM
        elif any(
            line_stripped.upper().startswith(join)
            for join in ["JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "OUTER JOIN"]
        ):
            formatted_lines.append(line_stripped)
        # Everything else gets a standard indentation
        else:
            formatted_lines.append("    " + line_stripped)

    # Return only the formatted SQL string without any additional values
    formatted_sql = "\n".join(formatted_lines)
    return formatted_sql


if __name__ == "__main__":
    main()
