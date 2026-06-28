---

name: websearch
description: Use this skill when external or up-to-date information is required. Retrieves and extracts relevant facts from web sources.
----------------------------------------------------------------------------------------------------------------------------------------

# Web Research Skill

## Purpose

Retrieve external knowledge from the web and extract relevant factual information.

---

## When to use

Use this skill when:

* Information is not available internally
* The topic is general knowledge
* Up-to-date or external data is needed

---

## Instructions

### 1. Perform search

* Call the web search tool with a precise query
* Prefer high-quality sources

---

### 2. Extract content

* Identify relevant parts of the page
* Remove noise (ads, navigation, etc.)
* Extract only meaningful facts

---

### 3. Output format

[SOURCE: <url>]

* fact 1
* fact 2
* fact 3

---

## Rules

* DO NOT write full reports
* DO NOT include prior knowledge
* ONLY use retrieved web content
* DO NOT fabricate sources

---

## Failure handling

If no useful content is found:

Return:
"No relevant web information found."
