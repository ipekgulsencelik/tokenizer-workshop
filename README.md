# tokenizer-workshop

## Project Overview

`tokenizer-workshop` is a Python project developed to teach the concept of tokenization in a practical and education-focused manner.

The main goal of this project is to provide a strong answer to the following fundamental question by building different tokenizer approaches step by step:

**How is a piece of text split into meaningful parts by a machine, and why is this split important?**

This repository aims not only to use existing tokenizer libraries, but also to understand the logic underlying them.

## Problem Definition

### Problem

Tokenization is one of the most fundamental layers of NLP and LLM systems; however, in most trainings it is either explained superficially or passed over in a black-box manner through ready-made libraries.

As a result, learners generally:

* give incomplete answers to the question of what a token is,
* have difficulty distinguishing between character-level, byte-level, and subword approaches,
* cannot fully understand why methods like BPE emerged,
* cannot explain why the same text produces different token counts across different tokenizers.

### Why this problem matters

Many critical topics such as LLMs, fine-tuning, embeddings, context window, cost, and latency are directly related to tokenization. Without understanding tokenization logic, it is difficult to develop a deep understanding of LLM system design.

### Target user / use case

This project is suitable for the following users:

* developers learning AI / NLP
* engineers who want to understand LLM systems more deeply
* instructors who provide technical training
* students who want to learn tokenization by writing code

## Solution Approach

This project teaches the concept of tokenization not through a single class, but in a comparative and incremental manner.

The following approaches are mainly covered in the project:

* `CharTokenizer`
* `ByteTokenizer`
* `SimpleBPETokenizer`

In this way, the learner can clearly see the following progression:

* character-level representation
* byte-level representation
* subword / merge-based representation

### Architecture summary

The project consists of a Python package developed under a clean `src/` structure. Application settings are stored in `config.yaml`, while project metadata and dependency information are stored in `pyproject.toml`. The development workflow is managed with `uv`. Secret values are not written into the repository; when necessary, they are read via environment variables. The goal is not to chase production-grade performance, but to create a tokenizer laboratory that is readable, testable, and suitable for teaching.

## Tech Stack

| Component                | Choice                | Notes                                     |
| ------------------------ | --------------------- | ----------------------------------------- |
| Language                 | Python                | Python 3.10+                              |
| Environment & workflow   | uv                    | Dependency and environment management     |
| Project metadata         | pyproject.toml        | Central package and dependency management |
| App config               | YAML                  | Application settings via `config.yaml`    |
| Tokenizer implementation | Custom                | Education-focused custom implementation   |
| UI / Interface           | CLI / script          | Simple usage                              |
| Evaluation               | Simple custom metrics | token count, vocab size, comparison       |

## Project Structure

```text
src/
└── tokenizer_workshop/
    ├── tokenizers/
    ├── trainers/
    ├── evaluators/
    └── utils/

tests/
data/
README.md
config.yaml
pyproject.toml
```

### Folder descriptions

* `src/tokenizer_workshop/`: Main application code
* `tests/`: Test files
* `data/`: Sample texts and small demo inputs

## Setup

### Requirements

* Python version: **3.10+**
* Required tool: **uv**
* Optional secret: **GROQ_API_KEY**

### Installation

```bash
uv sync
```

### Environment Variables

If needed, the following value can be defined via system environment variables:

```env
GROQ_API_KEY=
```

Note: API key values must not be written into the repository.

## Run Instructions

To run the project entry point:

```bash
uv run tokenizer-workshop
```

To run the tests:

```bash
uv run pytest -v
```

## Example Input / Output

### Example input

```text
Merhaba dünya!
```

### Example output

```text
CharTokenizer -> character-level tokens  
ByteTokenizer -> UTF-8 byte ids  
SimpleBPETokenizer -> learned subword tokens  
```

## Key Features

* Education-focused tokenizer design
* Comparative learning approach
* Showing character, byte, and BPE levels together
* Test-driven development workflow
* Simple but instructive metrics

## Limitations

This project has the following limitations:

* does not aim for production-grade tokenizer performance
* does not solve large-scale data and optimization problems
* does not aim to perfectly replicate all real-world tokenizer behaviors

## Future Improvements

The following improvements can be made in the future:

* adding `WordTokenizer`
* adding `RegexTokenizer`
* adding `RegexBPETokenizer`
* adding `ByteBPETokenizer`
* merge trace / visualization module
* notebook-based training materials

## Project Status

**Status:** in progress

## Repository Workflow

* Development progresses in a controlled and step-by-step manner.
* Large bulk changes are avoided.

## Author

* Name: Burak
* Project Topic: Educational tokenizer workshop for learning tokenization step by step

