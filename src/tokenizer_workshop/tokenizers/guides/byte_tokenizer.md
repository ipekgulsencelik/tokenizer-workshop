# ByteTokenizer

## 1. Purpose

`ByteTokenizer` is a tokenizer type that tokenizes text at the **UTF-8 byte level**.

The purpose of this tokenizer in the project is to ensure that the learner clearly understands the following critical distinction:

* A text can be tokenized not only through characters,
* but also through a lower-level representation: **byte sequences**.

Example:

```text
"abc" -> [97, 98, 99]
```

This approach is particularly important because byte-level thinking provides a strong foundation in modern tokenizer systems.

---

## 2. Why This Tokenizer Exists

`ByteTokenizer` fills two major pedagogical gaps in the project:

### a) Makes the limitations of CharTokenizer visible

`CharTokenizer` is easy to understand, but it breaks on characters not seen in the training data.

`ByteTokenizer`, on the other hand, is much more inclusive because it converts text into UTF-8 bytes.

### b) Breaks the assumption that “token = character”

Many learners naturally equate tokens with characters or words.
`ByteTokenizer` expands this perspective and shows:

> The fundamental unit of a tokenizer does not have to be what humans intuitively call a “character”.

This is very valuable for understanding tokenization at a deeper level.

---

## 3. Core Idea

The logic of this tokenizer is as follows:

1. Encode the text using UTF-8
2. Convert the resulting byte sequence into an integer list
3. Use each byte value as a token id
4. During decoding, convert the byte sequence back to text

Example:

```text
"text" -> b"text" -> [116, 101, 120, 116]
```

There is a very important point here:

For `ByteTokenizer`, we do not need to build a learned character-to-id mapping.
Because byte values already naturally provide integer representations in the range `0..255`.

---

## 4. Why UTF-8 Matters

This tokenizer is based on UTF-8.

Why is UTF-8 important?

* it is a widely used standard in modern text systems
* it can represent non-English characters
* it supports special characters in languages like Turkish
* it is compatible with the Unicode ecosystem

For example, a character like `"ğ"` may appear as a single letter to humans, but at the UTF-8 level it is represented by multiple bytes.

This leads to an important insight:

> A structure that is a single character for humans can correspond to multiple tokens for a byte-level tokenizer.

This difference is critical for understanding byte-level tokenization.

---

## 5. Vocabulary Behavior

For `ByteTokenizer`, the vocabulary is fixed:

```text
0, 1, 2, ..., 255
```

So the total vocabulary size is always:

```text
256
```

This behavior is very different from `CharTokenizer`.

### CharTokenizer

* vocabulary is data-dependent
* changes based on training data

### ByteTokenizer

* vocabulary is fixed
* independent of data

This distinction is important for learning, because it leads learners to ask:

> Is the vocabulary something learned later, or something predefined from the start?

`ByteTokenizer` demonstrates the second case.

---

## 6. Training Logic

For this tokenizer, the concept of “training” is slightly different.

No new vocabulary is actually learned, because the vocabulary is already fixed.

So why does a `train()` method still exist?

The reason is architectural consistency.

In this project, all tokenizers implement a common `BaseTokenizer` interface.
Therefore, each tokenizer must include:

* `train`
* `encode`
* `decode`
* `vocab_size`

In `ByteTokenizer`, `train()` essentially communicates:

> This tokenizer is now ready to use.

So here, training is not about learning, but about maintaining lifecycle consistency.

---

## 7. Encode Logic

The `encode()` method performs:

```python
list(text.encode("utf-8"))
```

This line is very important.

Because here the learner should recognize:

* `CharTokenizer` looks up characters in a dictionary
* `ByteTokenizer` directly uses Python’s UTF-8 encoding mechanism

So tokenization is based on a lower-level data representation.

Example:

```text
"merhaba" -> [109, 101, 114, 104, 97, 98, 97]
```

This is intuitive for ASCII.

But for Turkish or other Unicode characters:

```text
"ğ" -> multiple bytes
```

This highlights a key concept:

> Byte-level tokenization is not the same as character-level tokenization.

---

## 8. Decode Logic

The `decode()` method converts byte token lists back to text.

The logic is:

1. create `bytes(...)` from the integer list
2. decode it using UTF-8

Example:

```text
[97, 98, 99] -> b"abc" -> "abc"
```

There is an important risk here:

Not every integer list forms a valid UTF-8 byte sequence.

Therefore, two types of validation are required:

### a) Byte range validation

Is each token within `0..255`?

### b) UTF-8 validity

Can this byte sequence actually be decoded?

This controlled error approach is valuable for learning, because it reveals:

> Having a token sequence does not always guarantee a valid text output.

---

## 9. Strengths

The strengths of `ByteTokenizer`:

### a) Highly inclusive

Can tokenize any text representable in UTF-8.

### b) Reduces unknown character issues

Not limited to characters seen during training.

### c) Fixed vocabulary

Provides a simple and predictable structure.

### d) Closer to modern tokenizer logic

Many real-world tokenizers rely on byte-level thinking.

---

## 10. Limitations

### a) Sequence length can increase

Multi-byte characters may produce multiple tokens.

### b) Does not learn semantic structure

Does not model words, roots, or repeating meaningful parts.

### c) Harder to interpret for humans

Outputs like `[109, 101, 114]` are less intuitive.

### d) Not a compression solution

Inclusive, but not always efficient.

---

## 11. Comparison with Other Tokenizers

### ByteTokenizer vs CharTokenizer

* character-based vs byte-based
* CharTokenizer is intuitive
* ByteTokenizer is more inclusive

### ByteTokenizer vs SimpleBPETokenizer

* raw bytes vs learned merges
* BPE can produce shorter sequences

### ByteTokenizer vs real byte-level BPE systems

* ByteTokenizer teaches the base idea
* does not include merge learning

---

## 12. Design Decisions in This Project

Key decisions:

* UTF-8 base
* fixed vocabulary (256 tokens)
* shared tokenizer interface
* controlled errors for invalid bytes / UTF-8
* educational clarity prioritized

---

## 13. Testing Perspective

Tests validate:

* vocab size is always 256
* errors before training
* correct roundtrip for ASCII
* correct roundtrip for Turkish characters
* multi-byte behavior
* invalid byte handling
* invalid UTF-8 handling

---

## 14. When to Use

Useful when:

* explaining Unicode and multilingual representation
* showing tokenization below character level
* discussing unknown token issues
* transitioning to byte-level BPE

Not sufficient when:

* shorter token sequences are needed
* subword efficiency is required

---

## 15. Final Takeaway

`ByteTokenizer` is a critical threshold tokenizer in this project.

Because it teaches:

> Text can be represented at a more fundamental level than characters.

Once this is understood, the design of modern tokenizer systems becomes much clearer.

