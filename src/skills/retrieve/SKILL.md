---

name: retrieve
description: Use this skill when internal or private knowledge is required. Retrieves relevant document chunks from a vector database and returns grounded facts.
-----------------------------------------------------------------------------------------------------------------------------------------------------------------

# RAG Retrieval Skill

## Purpose

Retrieve relevant internal knowledge and provide grounded factual information.

---

## When to use

Use this skill when:

* The query relates to internal/company knowledge
* The topic may exist in a vector database
* High accuracy and grounding is required

---

## Instructions

### 1. Retrieve data

* Call the retrieval tool with a focused query
* Use semantic search (not keyword guessing)

---

### 2. Extract information

* Return only relevant facts from retrieved chunks
* Keep output concise and factual
* Do NOT generate explanations beyond retrieved content

---

### 3. Output format

Return structured chunks:

[doc-1] <relevant fact>
[doc-2] <relevant fact>

---

## Rules

* DO NOT write full reports
* DO NOT summarize broadly
* DO NOT hallucinate missing data
* ONLY use retrieved content

---

## Failure handling

If no relevant documents are found:

Return:
"No relevant internal documents found."
