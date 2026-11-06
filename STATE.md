# Current state

The owner canceled the astronomy project. Current work is exploring with the actual Alien Space of Science tool. Do not resume the needle/catalog plan or the keyword heuristic.

The authors' unchanged sampler ran locally on CPU using their released coherence model, availability model and author bank: 32 distinct combinations in 10.25s, then 254 distinct combinations from 256 draws in 82.94s. No LLM API calls or GPU. Code pinned at a55d660de75c99afe9e0948781cdb828fe3798eb; model release at 533937876344f11a10f5171cfea809255c9d952b. Weights were verified against the authors' SHA256 manifest. Actual rankings/provenance: experiments/alien-demo.json. Runtime and weights: ~/.cache/alien-space-of-science.

Use `python tools/run_alien.py sample --count 256` for fresh official CPU sampling, or `python tools/run_alien.py search memory` / `proposal 0a2130670db42afd` to explore through the authors' official hosted Lacuna MCP. Hosted retrieval relevance is not the Alien model score. Three hosted proposals, two source directions and a source paper were opened; raw responses stay in local .cache. No global app settings changed. The final launcher was verified with a fresh 16-candidate CPU run (all four ranking outputs checked) and a live hosted memory search.

Caveat: some released clusters_80.json sample texts have different IDs in atom_assignments. Examples are retained in alien-demo.json; this does not prove training was wrong, but decoded/source interpretations remain provisional. Do not claim novelty or a paper reproduction. Next: explore the source-linked Locally Repairable Agent Memory proposal, starting with its own cheap failure-attribution test; investigate release mapping before asserting fresh atom combinations' meanings.
