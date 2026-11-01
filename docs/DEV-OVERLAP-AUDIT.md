# Public development-source overlap audit

This offline audit found substantial shared patch context among variants of the same application. It compared 30 public development cases across nine applications, then checked selected code windows against a small set of locally available public Python sources. The measurements describe lexical overlap. They do not establish training exposure, originality, benchmark cleanliness or statistical independence.

The audited public source was revision `83005d1126b9ac2ad9451101b9051d88b5d096f7`, with `defects/` tree `bd099c7e29442caf40a40bce71200f5a91b18e1f`. See the [README](../README.md) for the benchmark's broader scope and limitations.

## Inputs and sampling

The inputs were 30 public `defect.json` / `bug.patch` pairs: 60 verified Git blobs, with six cases in each of five defect classes. Only displayed post-change patch context was reconstructed; complete application files were not read to fill gaps. No private evaluation data was accessed.

Extraction produced **57 raw windows**: 28 cases had two windows, one had one, and one had none. The minimum was eight code-bearing whitespace tokens after excluding comments, strings and imports from that count. Source review rejected `tickets-secret-leakage-2-window-1`: its relevant portion supplied seven tokens, with an unrelated following definition supplying two more. The threshold-qualified subset therefore contains **56 windows across 28 cases**. `tickets-removed-validation-2` had no qualifying selected window. These gaps are not zero-match observations.

Other generic-pattern and function-boundary flags remained relevant. Windows can overlap, and passing the token minimum does not make them independent or distinctive source samples.

## Within-development comparison

All **435 unordered pairs** of the 30 cases were compared, independently of window selection. The primary metric was set Jaccard similarity of exact lexical Python 5-grams; 8-grams were a sensitivity check. Jaccard is intersection divided by union, with an empty union reported as undefined.

Added and unchanged context lines from displayed Python hunks were included. Removed lines, diff headers, comments and layout were excluded. Identifiers, operators, literal spelling and docstrings were retained. No gram crossed a hunk or file boundary.

Of **292 Python hunks**, two produced explicitly flagged token prefixes after `TokenError`: `coupons-removed-validation` in `service.py` and `tickets-race-condition-1` in `core.py`. Those retained prefixes contribute to the results. This is partial patch-context tokenization, not complete application parsing.

| Metric | Within-app pairs | Median | Maximum | Cross-app pairs | Median | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Exact lexical 5-gram Jaccard | 62 | 0.659270 | 0.903846 | 373 | 0 | 0.018898 |
| Exact lexical 8-gram Jaccard | 62 | 0.627201 | 0.885287 | 373 | 0 | 0.008278 |

The highest primary pair was the two `tickets-secret-leakage` variants. The highest cross-app pair was `uploadstore-off-by-one` versus `wallet-race-condition`: 12 shared / 635 union 5-grams and 5 / 604 8-grams. The groups are unevenly weighted: **45 of the 62 within-app pairs are ticket-app pairs**.

There were no exact raw-patch duplicate groups or exact cross-app hunk-token duplicate groups. One auxiliary alpha-renamed hunk-template group linked booking and inventory across three case pairs. That deliberately lossy measure generalizes identifiers and literals; it does not show exact copying or semantic equivalence. Identical-token, disjoint-token and empty-set controls returned 1, 0 and undefined at both gram sizes.

## Narrow public reference comparison

The reference set contained **770 local public Python source files**: 690 from bundled CPython 3.12.14's standard library, excluding site-packages, tests, caches and links, plus 80 files from installed pytest 9.1.1's `pytest/` and `_pytest/` packages. The files totalled 12,798,601 bytes. All eligible enumerated files decoded and tokenized successfully; excluded directories remain outside coverage.

Each window was checked for contiguous exact text, whitespace-collapsed text, a complete lexical token sequence and shared lexical 8-grams. The scan retained all 57 raw candidates for transparency; the qualified interpretation excludes the padding candidate. **Neither view had a complete-window match.** Ten windows across six cases shared **40 short 8-gram occurrences**, including ordinary lock, path and comprehension patterns. The rejected candidate had no short matches, so those counts are unchanged in the qualified subset. Overlapping grams and repeated windows mean these are not 40 independent matches.

Five controls exercised the actual matching routine: exact-text, whitespace and complete-lexical positives, an 8-gram-only positive and a disjoint negative. All reference files were rehashed afterward without changes, as were the inventory and pytest metadata/RECORD bytes. The selected pytest files matched their local RECORD hashes. These are local provenance and before/after checks, not authentication of an upstream release, its supply chain or an atomic filesystem snapshot.

The target sources were read as data; no benchmark application, target pytest module or model test was executed. The audit scripts used ordinary standard-library support modules.

## Search was not an external coverage test

An initial GitHub code-search approach was abandoned because the authenticated legacy API did not establish a suitable public-only global scope. Three controls were restricted to a verified public repository. All returned HTTP 200 with zero results and `incomplete_results=true`, including both expected-positive controls. They are inconclusive responses, not negative overlap evidence.

**Zero global or selected-snippet search queries ran.** Outside GitHub repositories were not searched. The reference comparison covers only the 770 local files examined and is not representative of GitHub, package ecosystems or model training data.

## Provenance and limits

The reference scan recorded 21.016 seconds and a Windows own-process peak working set of 23,429,120 bytes. The persisted matrix snapshot recorded 8.484 seconds, Python peak 26,480,640 bytes and maximum sampled Python plus direct Git working set 31,936,512 bytes. These are cooperative measurement snapshots whose duration fields precede final output serialization, without an operating-system isolation or continuous descendant guarantee. A matrix status-persistence edge can leave its final post-write budget check unrecorded; no recorded breach or numerical discrepancy showed that it affected these results. It needs correction before future reuse.

This documentation-only change does **not** ship the executable audit scripts, complete matrices, per-file manifests or raw receipts. This summary alone is insufficient for full independent reproduction. Source, arithmetic and receipt reviews were performed by AI agents working for the same person; they are **not independent human approval**.

Shared application context, benign edits and generic templates can explain high overlap. Exact spelling, limited context and partial tokenization can explain low overlap. The audit does not determine an effective sample size, establish whole-application independence or show who copied whom. Neither absent full-window matches nor positive short matches establishes model exposure, memorization, novelty or cleanliness. Results apply only to the public development cases and the stated reference set, with no claim about model performance, deployed authorization, native services or runtime safety.
