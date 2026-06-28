---
name: decomposeaggregate
description: Use this skill for complex queries that require breaking down a problem into multiple subqueries, delegating them to subagents, and combining the results into a final report.
---

# decompose-and-aggregate

## Overview

This skill enables multi-step reasoning by:
- Decomposing a complex user query into smaller subqueries
- Delegating each subquery to the appropriate subagent
- Aggregating all retrieved results into a structured, high-quality report

---

## Instructions

### 1. Decompose the Query

Break the user query into **2–5 focused subqueries**.

Guidelines:
- Each subquery should cover a single aspect of the problem
- Avoid redundancy or overlap
- Keep subqueries concise and actionable

---

### 2. Select the Appropriate Subagents

For each subquery, choose one or more subagents:

- **rag-agent**
  - default agent
  - use to search data from the internal database

- **web-agent**
    - Use when information is missing
    - Requires factual extraction from web sources


If **rag-agent** failes -> then you MUST use the **web-agent** for that subquery
---

### 3. Delegate Subqueries

For each subquery:

1. Call the selected subagents
2. Retrieve relevant factual information
3. Do NOT summarize prematurely
4. Preserve the raw retrieved content

---
### 3. Delegate Subqueries

At the end synthesize information into structured insights using the **analasis-agent** to write a full report

### Important

You MUST answer in the same language as the user query
