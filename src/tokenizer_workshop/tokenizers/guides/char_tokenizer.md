# CharTokenizer

## 1. Purpose

`CharTokenizer` is the most basic tokenizer type that tokenizes text at the **character level**.

The purpose of this tokenizer in the project is to present the concept of tokenization in its most raw and understandable form.
Here, each unique character is treated as a token.

Example:

```text id="3x6w9v"
"merhaba" -> ["m", "e", "r", "h", "a", "b", "a"]
```

This approach is especially valuable for learning because it allows the learner to clearly answer the following fundamental questions:

* what is a token?
* how is a vocabulary formed?
* what does encode do?
* what does decode do?
* why is a mapping table needed?

---

## 2. Why This Tokenizer Exists

This tokenizer does not exist for real-world performance, but for **teaching and conceptual clarity**.

In the project, `CharTokenizer` plays the following role:

* it is the starting point of tokenization
* it provides a reference behavior to understand more advanced tokenizers
* it creates a comparison foundation with `ByteTokenizer` and `SimpleBPETokenizer`

In other words, without this class, it becomes difficult for the learner to evaluate more advanced tokenizers.
Because without seeing the “simplest form” first, it is hard to understand why more complex methods are needed.

---

## 3. Core Idea

The logic of this tokenizer is very simple:

1. collect all unique characters from the training data
2. assign an integer ID to each character
3. convert text into these IDs
4. convert back to text when needed

Example:

```text
text = "aba"

unique characters = ["a", "b"]
stoi = {"a": 0, "b": 1}
itos = {0: "a", 1: "b"}

encode("aba") -> [0, 1, 0]
decode([0, 1, 0]) -> "aba"
```

Two things are very important here:

* `stoi`: string to integer
* `itos`: integer to string

A tokenizer does not only split; it must also be able to reconstruct.

---

## 4. Training Logic

For `CharTokenizer`, “training” is not classical machine learning training.
Here, training means extracting the vocabulary from the text.

In the code, this is done with the following logic:

```python id="d8x7zb"
unique_chars = sorted(set(text))
```

This line contains two important decisions:

### a) `set(text)`

Collects unique characters in the text.

### b) `sorted(...)`

Orders characters deterministically.

Why is this important?

Because tokenizer outputs must be reproducible.
When training on the same text multiple times, the same character must receive the same ID.

Without `sorted`, the mapping order may become unpredictable in some cases, leading to unstable results.

---

## 5. Encode Logic

The `encode()` method converts each character in the text into an integer token ID.

Example:

```text id="4r8y0x"
"merhaba" -> [id_m, id_e, id_r, id_h, id_a, id_b, id_a]
```

An important design decision is made here:

If the tokenizer encounters a character that it has not seen during training, it does **not silently skip it** and does **not create a fake solution**.
It directly raises an error.

This is correct for learning purposes because it makes the following problem visible:

> What should a tokenizer do when it encounters characters it does not cover?

In real-world systems, this problem is solved using methods like `unknown token`, `fallback`, or `byte fallback`.
But here, the goal is to expose the problem clearly first.

---

## 6. Decode Logic

The `decode()` method converts a list of integer tokens back into text.

This uses the `_itos` mapping:

```text id="m5o2vz"
[0, 1, 0] -> "aba"
```

The key point here is:

Decoding demonstrates that the tokenizer works bidirectionally.
Many learners understand encoding but overlook why decoding is necessary.

However, decoding is essential for:

* inspecting tokenizer behavior
* debugging
* validating correctness

---

## 7. Vocabulary Behavior

For `CharTokenizer`, the vocabulary size is:

> the number of unique characters in the training data

This means:

* vocabulary is data-dependent
* different corpora produce different vocabularies
* small text → small vocab
* new characters → require retraining

This behavior is educationally valuable because it encourages learners to ask:

> Is the vocabulary fixed or learned?

---

## 8. Strengths

The strengths of `CharTokenizer`:

* conceptually very clear
* simple implementation
* teaches encode/decode logic
* makes vocabulary creation visible
* easy to debug
* ideal for learning

This makes it a very appropriate first tokenizer in the project.

---

## 9. Limitations

This tokenizer has serious limitations:

### a) Sequence length can grow significantly

Each character becomes a token.

### b) Does not capture structural repetition

It does not learn patterns like words or common substrings.

### c) Breaks on unseen characters

Cannot encode new characters without retraining.

### d) Inefficient for real-world usage

Modern LLM systems use more advanced tokenizers.

---

## 10. Comparison with Other Tokenizers

### CharTokenizer vs ByteTokenizer

* CharTokenizer is character-based
* ByteTokenizer is UTF-8 byte-based

CharTokenizer is more intuitive.
ByteTokenizer is more inclusive.

### CharTokenizer vs SimpleBPETokenizer

* CharTokenizer does not merge anything
* SimpleBPETokenizer merges frequent patterns

So BPE can produce shorter token sequences in many cases.

---

## 11. Design Decisions in This Project

Key design decisions for `CharTokenizer`:

* vocabulary is learned from text
* character order is deterministic
* encode/decode does not work before training
* unknown characters raise errors
* educational clarity is prioritized over performance

---

## 12. Testing Perspective

Tests validate:

* vocabulary is created after training
* encode output is an integer list
* decode reconstructs original text
* using before training raises an error
* unknown characters raise errors
* same input produces same vocabulary

These tests validate both correctness and design contracts.

---

## 13. When to Use

Useful when:

* teaching tokenization
* demonstrating basic tokenizer logic
* running simple and transparent experiments
* explaining encode/decode mapping

Not sufficient for:

* large-scale NLP systems
* efficient sequence representation
* multilingual complex data
* modern LLM pipelines

---

## 14. Final Takeaway

`CharTokenizer` is the simplest tokenizer in the project, but not the least important.
On the contrary, it provides the fundamental conceptual framework needed to understand all other tokenizers.

Its main value is:

> The essence of tokenization becomes clearly visible in its simplest form here.

