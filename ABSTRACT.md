# Abstract

**CostQual-Router: Adaptive Semantic Caching and Complexity-Based Model Routing for
Cost-Efficient LLM Serving**

Large Language Models (LLMs) are increasingly deployed as the default interface for
question-answering and conversational systems, but naive deployment strategies typically route
every user query to a single, uniformly capable — and expensive — model regardless of the
query's actual complexity. This results in significant unnecessary computational cost and
latency, particularly for simple or repeated queries that do not require full model capacity.
This project proposes and prototypes CostQual-Router, an adaptive LLM-serving architecture that
combines semantic caching with complexity-aware model routing to reduce cost and latency without
compromising answer quality.

The system maintains an embedding-based semantic cache that identifies not only exact repeat
queries but also semantically equivalent paraphrases, returning a cached response instantly when
a sufficiently similar prior query exists. For cache misses, a lightweight rule-based classifier
estimates query complexity and routes the request to the smallest capable model tier from a set
of locally hosted, open-source models, reserving the most capable tier for genuinely complex
queries.

A controlled benchmark comparing this adaptive system against a naive single-model baseline was
conducted using a curated 60-query test set spanning exact duplicates, paraphrases, simple
factual questions, complex reasoning questions, and unique one-off queries. Results demonstrate a
35% reduction in estimated serving cost and a 23% semantic cache hit rate — driven by both exact
and paraphrased repeats — with answer quality preserved in the majority of cases where routing
selected a smaller model, as verified through an automated LLM-based quality assessment.

This prototype validates the core hypothesis and forms the foundation for a seven-month project
extending the system with a genuine three-tier model hierarchy, persistent vector-based caching,
rigorous quality evaluation (BERTScore), a learned machine-learning-based routing classifier, and
production-oriented infrastructure — authentication, monitoring, and CI/CD — implemented entirely
using free and open-source, self-hosted tooling to ensure full reproducibility without reliance
on any paid third-party service.

**Keywords:** Large Language Models, Semantic Caching, Model Routing, Cost Optimization, Local
Inference, Efficient AI Serving
