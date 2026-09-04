# English–Japanese Parallel Corpus Cleaning Pipeline

## 1. Project Overview

This project implements a scalable, deterministic, rule-based data cleaning pipeline for a large English–Japanese parallel corpus.

The raw corpus contains **40,883,733 aligned English–Japanese sentence pairs**. Since the dataset is significantly larger than available memory, the pipeline processes the corpus using streaming, chunk-based processing, multiprocessing, compressed Parquet sharding, and disk-based global deduplication.

The primary goal is to remove structural and formatting noise while preserving as much useful bilingual information as possible.

The pipeline does not use machine learning models for cleaning. Cleaning decisions are based on deterministic Python and regular-expression rules.

---

## 2. Dataset

The corpus consists of two aligned text files:

```text
NLLB.en-ja.en    -> English source sentences
NLLB.en-ja.ja    -> Japanese target sentences
```

The files are processed line-by-line while preserving record alignment.

```text
English line 1 <-> Japanese line 1
English line 2 <-> Japanese line 2
English line 3 <-> Japanese line 3
...
```

### Dataset Size

| Stage | Records |
|---|---:|
| Original aligned corpus | 40,883,733 |
| Records removed during cleaning | 905,102 |
| Records after cleaning | 39,978,631 |
| Duplicate pairs removed | 506,293 |
| Final unique EN-JA pairs | **39,472,338** |

Approximately **97.79%** of the original records were preserved during the cleaning stage.

---

## 3. Project Structure

```text
en_ja_corpus_cleaning_pipeline/
│
├── config/
│   └── config.py
│
├── data/
│   ├── full/
│   │   ├── raw/
│   │   │   ├── NLLB.en-ja.en
│   │   │   └── NLLB.en-ja.ja
│   │   │
│   │   ├── shards/
│   │   │   ├── shard_00000.parquet
│   │   │   ├── shard_00001.parquet
│   │   │   └── ...
│   │   │
│   │   └── final/
│   │       └── deduplicated_en_ja.parquet
│   │
│   ├── samples/
│   │   ├── raw/
│   │   │   └── en_ja_30k_sample.csv
│   │   └── processed/
│   │       └── cleaned_en_ja_30k.csv
│   │
│   └── test/
│       ├── raw/
│       ├── shards/
│       ├── final/
│       └── temp/
│
├── reports/
│   ├── cleaning/
│   ├── full_run/
│   ├── inspection/
│   ├── test_run/
│   └── validation/
│
├── scripts/
│   ├── cleaning_run.py
│   ├── create_test_subset.py
│   ├── full_cleaning_pipeline.py
│   ├── global_dedup_run.py
│   ├── inspection_run.py
│   ├── inspect_remaining_foreign.py
│   ├── post_clean_validation.py
│   ├── read_parquet.py
│   └── validation_run.py
│
├── src/
│   ├── cleaner.py
│   ├── data_loader.py
│   ├── deduplicator.py
│   ├── inspection.py
│   ├── shard_writer.py
│   ├── stats.py
│   └── validator.py
│
├── tests/
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

## 4. Pipeline Architecture

The complete processing flow is:

```text
Raw English File + Raw Japanese File
                 |
                 v
        Aligned Data Streaming
                 |
                 v
       Inspection & Validation
                 |
                 v
        Chunk-based Processing
                 |
                 v
       Multiprocessing Cleaning
                 |
                 v
       KEEP / CLEAN / REMOVE
                 |
                 v
      Parquet + ZSTD Sharding
                 |
                 v
       39,978,631 Records
                 |
                 v
      Global Pair Deduplication
             (DuckDB)
                 |
                 v
       506,293 Duplicates Removed
                 |
                 v
       39,472,338 Unique Pairs
                 |
                 v
       Post-clean Validation
                 |
                 v
            Final Dataset
```

---

## 5. Data Inspection

Before applying cleaning rules to the complete corpus, a sample dataset was analyzed to understand the major types of contamination.

A combination of random records and targeted suspicious records was used during development.

The inspection stage helped identify issues such as:

1. Empty or malformed records
2. Japanese targets containing no Japanese script
3. Excessive Latin text in Japanese targets
4. Copied English/Latin content around Japanese text
5. Unexpected foreign scripts
6. Excessive numeric noise
7. Repeated-character noise
8. Repeated-token noise
9. Symbol and ASCII-art noise
10. Unmatched emoji/decorative symbols
11. Duplicate EN-JA pairs

The cleaning rules were designed conservatively to avoid unnecessarily modifying valid multilingual text.

---

## 6. Cleaning Strategy

The cleaning system classifies records into three main actions:

```text
KEEP    -> No modification required
CLEAN   -> Record is useful after safe modification
REMOVE  -> Record is considered structurally unusable/noisy
```

### 6.1 Unicode and Whitespace Normalization

Text is normalized before further processing.

The pipeline performs safe operations such as:

- Unicode normalization
- Removal of zero-width characters
- Removal of unnecessary whitespace
- Collapsing repeated spaces

The objective is to normalize formatting without changing the actual meaning of the sentence.

---

### 6.2 Empty Record Detection

Pairs containing an empty English or Japanese side are rejected.

```text
English: ""
Japanese: "こんにちは"
```

Such a pair cannot be used as a valid parallel training record.

---

### 6.3 Japanese Script Validation

The Japanese target is expected to contain actual Japanese characters.

Records containing no Japanese script are removed.

Example:

```text
English:
How are you?

Japanese:
This is not Japanese.
```

This prevents completely English or unrelated target-side records from entering the final corpus.

---

### 6.4 Insufficient Japanese Content

Records containing extremely little Japanese content are treated as suspicious.

A minimum Japanese-character requirement is used to reject records where the target contains insufficient Japanese information.

---

### 6.5 Copied Latin Edge Removal

Some Japanese records contain long English or Latin blocks before or after valid Japanese text.

Example:

```text
English:
This is an example English sentence.

Japanese:
This is an example English sentence ... very long copied text ... これは日本語の文章です。
```

The pipeline detects suspicious Latin prefixes and suffixes and compares them with the English source.

Long source-like Latin blocks can be removed while preserving valid Japanese content.

The rule is intentionally conservative so that short English titles, proper nouns, product names, and technical terms are not unnecessarily deleted.

---

### 6.6 Foreign Script Detection

Unexpected scripts inside the Japanese target are detected using Unicode ranges.

Examples include:

- Arabic
- Cyrillic
- Korean
- Hebrew
- Other unexpected script ranges

Foreign-script detection is used as a structural quality signal.

However, multilingual references, proper names, quoted foreign-language terms, and kaomoji may legitimately contain characters outside normal Japanese ranges. Therefore these cases require conservative handling.

---

### 6.7 Excessive Repeated Characters

Extremely long repeated-character sequences are treated as noise.

Example:

```text
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

A regex-based rule detects excessive continuous repetition.

This helps remove corrupted or spam-like records while preserving normal character repetition.

---

### 6.8 Excessive Repeated Tokens

The pipeline also detects cases where the same alphanumeric token is repeated many times consecutively.

Example:

```text
test test test test test test test test test
```

This rule detects a different type of repetition from character-level flooding.

---

### 6.9 Excessive Numeric Noise

Numeric information is not automatically removed because numbers may carry important meaning.

For example:

```text
2026
$500
Version 3.2
10 km
```

are potentially valid.

The pipeline only removes records when numeric content becomes excessively dominant or resembles corrupted/serialized data.

---

### 6.10 Symbol Noise

Normal Japanese and English punctuation is preserved.

The cleaner targets excessive symbol sequences and ASCII-art-like contamination instead of deleting punctuation blindly.

Valid punctuation such as the following is protected:

```text
。、！？「」『』（）【】・
```

---

### 6.11 Emoji and Decorative Symbols

Emoji can contain useful information and are therefore not removed globally.

The pipeline uses conservative matching logic to clean suspicious unmatched emoji or decorative symbols while attempting to preserve meaningful corresponding symbols.

---

## 7. Pair-Level Deduplication

Deduplication is performed on the complete cleaned dataset using the pair:

```text
(english, japanese)
```

This means that only exact duplicate translation pairs are removed.

A repeated English sentence with a different Japanese translation is not automatically considered a duplicate.

Similarly, a repeated Japanese sentence with different English text is not automatically removed.

---

## 8. Large Dataset Processing

Loading more than 40 million records into a Pandas DataFrame at once would require significant memory.

Therefore the pipeline uses a streaming and chunk-based architecture.

```text
Disk
 |
 v
Read chunk
 |
 v
Process chunk
 |
 v
Write accepted records
 |
 v
Release memory
 |
 v
Read next chunk
```

Only a limited portion of the corpus is processed in memory at a time.

This allows the pipeline to process datasets much larger than available RAM.

---

## 9. Multiprocessing

Cleaning is primarily based on Python text processing and regular expressions.

These operations are CPU-bound, so multiprocessing is used to distribute cleaning work across multiple CPU cores.

The production run used:

```text
Workers: 4
Chunk size: 50,000 records
```

The main process is responsible for reading aligned records and writing output, while worker processes perform record cleaning.

This architecture also helps preserve deterministic processing and record alignment.

---

## 10. Multiprocessing Benchmark

A benchmark was performed on the same 100,000 records.

| Configuration | Time | Throughput |
|---|---:|---:|
| 1 Worker | 14.73 sec | ~6,790 records/sec |
| 4 Workers | 5.34 sec | ~18,717 records/sec |

Approximate speedup:

```text
14.73 / 5.34 ≈ 2.76x
```

Both runs produced the same output statistics and the same number of final records.

Therefore multiprocessing improved performance without changing the cleaning result.

---

## 11. Chunking vs Sharding

Chunking and sharding serve different purposes.

### Chunking

Chunking controls how many records are processed in memory at one time.

Example:

```text
Chunk size = 50,000
```

### Sharding

Sharding controls how processed records are divided into output files.

The full cleaning run produced:

```text
80 Parquet shards
```

Therefore:

```text
Chunking = processing strategy
Sharding = storage strategy
```

---

## 12. Parquet and ZSTD Compression

Intermediate cleaned records are stored using:

```text
Format      : Parquet
Compression : ZSTD
```

Parquet was selected because it provides:

- Efficient storage
- Columnar format
- Compression support
- Fast analytical reads
- Compatibility with DuckDB and other data-processing tools

ZSTD compression reduces storage size while maintaining efficient read performance.

---

## 13. Global Deduplication with DuckDB

After cleaning, records are distributed across multiple Parquet shards.

Duplicates may occur across different shards, so deduplicating each shard independently would not guarantee global uniqueness.

DuckDB is therefore used to perform global exact pair-level deduplication across all cleaned shards.

Conceptually:

```sql
SELECT DISTINCT
    english,
    japanese
FROM cleaned_shards;
```

DuckDB can directly query Parquet files and use disk-backed processing, making it suitable for large datasets that should not be loaded completely into a Pandas DataFrame.

### Deduplication Result

```text
Input records      : 39,978,631
Duplicates removed :    506,293
Unique records     : 39,472,338
```

Final dataset:

```text
data/full/final/deduplicated_en_ja.parquet
```

---

## 14. Post-clean Validation

After global deduplication, the final dataset is validated again.

The validation checks include:

- Empty English records
- Empty Japanese records
- Japanese targets without Japanese script
- Exact duplicate EN-JA pairs
- Remaining foreign-script characters

### Final Validation Result

```text
Total Records             : 39,472,338
Empty English             : 0
Empty Japanese            : 0
No Japanese Script        : 0
Duplicate EN-JA Pairs     : 0
Foreign Script Flags      : 40
```

The remaining foreign-script cases were exported separately for manual inspection.

Some foreign-script detections may represent multilingual references, names, quoted terms, or special characters rather than simple formatting noise.

---

## 15. Full Cleaning Results

The complete corpus cleaning run produced the following results:

```text
Total Records       : 40,883,733

KEEP                : 39,132,957
CLEAN               :    845,674
REMOVE              :    905,102

After Cleaning      : 39,978,631

Preserved           : 97.79%
Removed             :  2.21%

Total Shards        : 80
```

### Main Cleaning Reasons

| Cleaning / Removal Reason | Count |
|---|---:|
| No Japanese script | 494,872 |
| Unmatched symbol | 440,644 |
| Insufficient Japanese content | 324,649 |
| Copied Latin edge | 246,387 |
| Unmatched emoji | 149,378 |
| Excessive repeated characters | 49,832 |
| Foreign script | 17,942 |
| Excessive numeric noise | 16,813 |
| Excessive symbol noise | 16,047 |
| Excessive repeated tokens | 2,782 |
| Excessive Latin in Japanese | 107 |

A record may be affected by more than one cleaning condition, so reason counts should not necessarily be interpreted as mutually exclusive record counts.

---

## 16. Full Run Performance

Production configuration:

```text
Records processed : 40,883,733
Workers           : 4
Chunk size        : 50,000
Cleaning time     : ~37 minutes 11 seconds
Throughput        : ~18,326 records/second
```

This demonstrates that the pipeline can process tens of millions of aligned records efficiently without loading the entire corpus into memory.

---

## 17. Final Output

The final cleaned and globally deduplicated dataset is:

```text
data/full/final/deduplicated_en_ja.parquet
```

Schema:

```text
english     -> English source sentence
japanese    -> Japanese target sentence
```

Final record count:

```text
39,472,338 unique English-Japanese pairs
```

---

## 18. Running the Pipeline

Run commands from the project root directory.

### Full Cleaning

```bash
python -m scripts.full_cleaning_pipeline --full --workers 4 --chunk-size 50000
```

### Global Deduplication

```bash
python -m scripts.global_dedup_run --full
```

### Post-clean Validation

```bash
python -m scripts.post_clean_validation --full
```

### Run Tests

```bash
pytest
```

---

## 19. Testing

Basic unit tests are included for important cleaning behavior such as:

- Pure-English Japanese target detection
- Preservation of valid mixed-language titles
- Copied Latin prefix cleaning
- Preservation of technical Latin content
- Excessive repeated-character detection
- Preservation of valid Japanese punctuation
- Foreign-script handling
- Excessive numeric-noise detection

Testing helps ensure that new cleaning rules do not unintentionally modify previously valid behavior.

---

## 20. Design Principles

The pipeline follows several important principles:

### Preserve useful information

Valid text should not be removed simply because it contains unusual punctuation, numbers, emoji, Latin technical terms, or proper names.

### Deterministic processing

The same input and cleaning configuration should produce the same output.

### Maintain alignment

English and Japanese records are always processed as pairs.

### Memory efficiency

The complete dataset is never required to be loaded into RAM.

### Global deduplication

Duplicate detection is performed across the complete cleaned corpus rather than independently inside each shard.

### Separation of responsibilities

Different modules handle inspection, validation, cleaning, writing, statistics, deduplication, and final validation.

---

## 21. Limitations

The pipeline is primarily designed for deterministic structural cleaning.

It can detect issues such as:

- Missing Japanese text
- Unexpected scripts
- Excessive Latin contamination
- Repeated-character noise
- Numeric/symbol noise
- Copied source-side text
- Empty records
- Exact duplicates

However, deterministic rules cannot reliably determine whether two grammatically valid English and Japanese sentences express exactly the same meaning.

For example:

```text
English:
When did you start making wine by yourself?

Japanese:
お弁当を自分でつくりはじめたのはいつ頃からですか。
```

Both sentences are structurally valid, but their meanings are different.

Reliable semantic-alignment verification would require additional bilingual human evaluation or an appropriate multilingual semantic model.

Semantic filtering was intentionally kept outside the deterministic cleaning pipeline.

---

## 22. Summary

The project successfully implements an end-to-end large-scale English–Japanese corpus cleaning pipeline using:

- Python
- Regular expressions
- Streaming file processing
- Chunk-based processing
- Multiprocessing
- Parquet
- ZSTD compression
- DuckDB
- Global pair-level deduplication
- Post-clean validation

Final processing flow:

```text
40,883,733 Original Pairs
          |
          | Cleaning
          v
39,978,631 Cleaned Pairs
          |
          | Global Deduplication
          | -506,293
          v
39,472,338 Final Unique EN-JA Pairs
```

The resulting dataset is stored as compressed Parquet and is ready for downstream review or language-model data preparation.