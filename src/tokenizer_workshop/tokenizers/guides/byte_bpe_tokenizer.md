# ByteBPETokenizer

## 1. Purpose

`ByteBPETokenizer` is a tokenizer type included in this project to teach the idea of **byte-level subword tokenization**.

The main purpose of this class is to enable the learner to clearly answer the following question:

> While representing any text (including language, emojis, or unknown characters) without loss, is it possible to obtain a more efficient representation by merging repeating byte sequences?

`ByteBPETokenizer` directly demonstrates the answer to this question.
Here, the text is first reduced to a UTF-8 byte sequence, and then BPE merge rules are learned on this byte sequence.

Example idea:

```text
"merhaba" -> UTF-8 bytes -> BPE merges -> token ids
```

This approach combines the strengths of the `ByteTokenizer` and `SimpleBPETokenizer` classes into a single architecture.

* Like `ByteTokenizer`, it provides a **universal representation covering all UTF-8 bytes**
* Like `SimpleBPETokenizer`, it **learns repeating patterns and performs compression**

In this way, it is no longer just about splitting text, but:

**representing any kind of input without loss while simultaneously learning repeating structures**

---

## 2. Why This Tokenizer Exists

This tokenizer fills a very critical point in the project.

### a) Inclusiveness and efficiency meet in the same place

`ByteTokenizer` can represent any input (different languages, emojis, unknown characters) without loss; however, the resulting token sequences are usually long.
`SimpleBPETokenizer`, on the other hand, produces shorter and more efficient sequences by merging repeating parts; however, since it starts at the character level, it is limited for unseen characters during training.

`ByteBPETokenizer` combines the strengths of these two approaches:

* **Byte-level coverage** → ability to encode any input
* **BPE-based compression** → learning repeating byte sequences to produce shorter representations

### b) Demonstrates the core logic of modern LLM tokenizers

Many large tokenizers used in the real world (especially in the GPT family) operate largely based on this logic:

* byte-level initialization
* merge learning with BPE

`ByteBPETokenizer` is a simplified but **conceptually correct and educational** version of this real-world approach.

### c) A natural continuation of previous tokenizers

Throughout the project, the learner is introduced to:

* `CharTokenizer` → character-level splitting
* `ByteTokenizer` → universal byte representation
* `SimpleBPETokenizer` → learning repeating structures

`ByteBPETokenizer` is the natural result of this journey:

> A structure that combines the most inclusive base with the most powerful compression logic.

---

## 3. What “BPE” Means in This Project

BPE in this class is handled as a merge approach inspired by the idea of **Byte Pair Encoding**.

However, unlike `SimpleBPETokenizer` in the project, `ByteBPETokenizer` moves closer to a more realistic model.

The use of BPE in this project has the following characteristics:

* **uses a byte-level starting point** (operates on UTF-8 bytes instead of characters)
* **merge learning is done with BPE logic** (the most frequent neighboring byte pairs are merged)
* **deterministic merge order is preserved** (the learned order is applied exactly during encoding)
* **contains a fixed base vocabulary covering all 256 bytes**
* **can encode unseen characters** (falls back to base bytes)

However, this implementation is still intentionally simplified:

* does not include regex pre-tokenization
* does not include special token management (PAD, BOS, EOS, etc.)
* does not apply unicode normalization
* does not aim for production-level optimizations

Therefore, `ByteBPETokenizer` is:

> Not an exact copy of production tokenizers,
> but a teaching tool that **conceptually reflects their approach correctly**.

The goal of BPE usage here is not only to merge characters, but to create a compression mechanism that learns repeating structures and produces a more efficient representation.

---

## 4. Core Idea

The working logic of this tokenizer is based on the following steps:

1. Encode the text using UTF-8
2. Take the resulting byte sequence as the initial token sequence
3. Map each byte to a single-character symbol (so BPE can operate on strings)
4. Count consecutive token pairs
5. Find the most frequent pair and merge it into a new token
6. Repeat this process `num_merges` times
7. Apply learned merge rules in the same order during encoding
8. During decoding, convert the token sequence back to bytes and then to text

Example:

```text
"abababa"
```

First, the text is converted into bytes (unchanged since ASCII):

```text
[97, 98, 97, 98, 97, 98, 97]
```

These bytes are mapped to symbols:

```text
["a", "b", "a", "b", "a", "b", "a"]
```

Consecutive pairs:

```text
("a", "b") -> 3
("b", "a") -> 3
```

According to tie-break rules, the first selected pair:

```text
("a", "b") -> "ab"
```

After merging:

```text
["ab", "ab", "ab", "a"]
```

This process repeats `num_merges` times, producing larger and more meaningful tokens at each step.

This example shows the learner:

> Byte-level BPE learns repeating byte sequences and transforms them into larger and more efficient tokens.

Example:

```text
"abab"

-> UTF-8: [97, 98, 97, 98]
-> pair count: (97, 98) -> 2
-> merge: (97, 98) -> 256
-> new sequence: [256, 256]
```

A critical observation here:

> Tokens created after merging are no longer single bytes.
> They are new symbolic units representing multiple bytes.

This means:

* Initially each token = 1 byte
* After merge each token = a byte sequence

Thanks to this mechanism:

* repeating byte sequences are grouped under one token
* token count decreases (compression)
* the model works with shorter and more meaningful sequences

The same merge logic as `SimpleBPETokenizer` is used, but:

the starting point is **byte-level, not character-level**

therefore:

* **unseen characters** (emoji, different languages, special characters) can be encoded safely
* inputs not seen during training can still be processed
* even if merge rules are insufficiently learned, the system always falls back to byte-level representation and never produces an “unknown token” error

---

## 5. Why Byte-Level Base Matters

The foundation of this tokenizer is UTF-8 bytes, and this choice is intentional.

A byte-level base provides the following advantages:

* no character is “unknown”
* every UTF-8 text can be represented without loss
* Turkish, Arabic, CJK characters, emojis, and other special symbols are tokenized seamlessly
* tokenizer behavior becomes less dependent on training data

`SimpleBPETokenizer` may struggle when encountering unseen characters.
`ByteBPETokenizer`, at worst, decomposes the character into bytes and continues encoding.

Therefore, `ByteBPETokenizer` is a more robust tokenizer that works reliably for real-world text.

---

## 6. Separation of Responsibilities

The key architectural principle in this project is preserved here:

* `BPETrainer` (or `ByteBPETrainer`) handles learning
* `ByteBPETokenizer` handles encode/decode behavior

This separation is highly valuable because it clearly distinguishes two responsibilities.

### Trainer

* calculates frequencies of consecutive token pairs
* selects the most frequent pair
* produces merge order
* assigns new token IDs starting from `256`
* ensures deterministic learning

### Tokenizer

* stores learned merge rules
* builds vocabulary from base bytes + merged tokens
* applies merges during encoding in learned order
* converts tokens back to byte sequences during decoding

This teaches a key principle:

> Learning logic and application logic should not be mixed in the same class.

---

## 7. Training Logic

The `train()` method is the core of this tokenizer.

During training:

### a) Convert text into bytes

```python
initial_tokens = list(text.encode("utf-8"))
```

Each token initially corresponds to a byte value in the range `0..255`.

### b) Learn merge rules

* count consecutive token pairs
* select the most frequent pair
* create a new token ID

New IDs:

```text
256, 257, 258, ...
```

### c) Store merge steps

Each step is stored as a `MergeStep` object containing:

* merged pair
* new token ID
* frequency

### d) Build vocabulary

* base vocabulary: `0..255`
* merged tokens: `256+`

Final size:

```text
256 + num_merges
```

---

## 8. Why Merge Order Matters

Merge order is critical.

Applying the same merges in different orders produces different outputs.

Therefore:

* merges are stored in order
* encoding applies them in the same order

---

## 9. Determinism and Tie-Breaking

When two pairs have equal frequency:

* choose the most frequent
* if equal, choose lexicographically smaller

This ensures:

* same input → same output
* reproducibility

---

## 10. Encode Logic

Steps:

1. Encode text to UTF-8
2. Map to symbols
3. Apply merges
4. Convert to token IDs

Important:

> No new merges are learned during encoding.
> Only learned rules are applied.

---

## 11. Decode Logic

Steps:

1. Convert token IDs to byte sequences
2. Convert bytes to text

Important:

> Decoding is not just concatenation; it reconstructs valid UTF-8.

---

## 12. Vocabulary Behavior

Two parts:

### Base vocabulary

* fixed `0..255`

### Merged vocabulary

* learned
* IDs `256+`

---

## 13. Compression Behavior

Example:

```text
"ababab"
```

ByteTokenizer → 6 tokens
ByteBPETokenizer → fewer tokens

---

## 14. Strengths

* universal coverage
* no unknown tokens
* compression
* efficient multi-byte handling
* close to real-world tokenizers
* deterministic

---

## 15. Strengths

Key strengths:

* universal coverage
* combines byte + BPE
* efficient compression
* deterministic behavior
* inspectable
* educational strength

---

## 16. Limitations

* no pre-tokenization
* no special tokens
* no save/load
* not optimized
* harder to interpret
* limited production features

---

## 17. Comparison with Other Tokenizers

### vs CharTokenizer

simpler vs more powerful

### vs ByteTokenizer

fixed vs learned

### vs SimpleBPETokenizer

data-dependent vs fixed base

---

## 18. Design Decisions

* byte-level base
* fixed vocab
* deterministic merges
* separation of trainer/tokenizer

---

## 19. Testing Perspective

Tests validate:

* errors
* vocab size
* encode/decode correctness
* determinism
* coverage

---

## 20. When to Use

Useful for:

* learning modern tokenizer logic
* showing compression + coverage

Not sufficient for:

* production systems
* advanced features

---

## 21. Final Takeaway

`ByteBPETokenizer` is the culmination of the tokenizer journey.

> A good tokenizer does not just split text;
> it builds learned structures on top of a universal base.

