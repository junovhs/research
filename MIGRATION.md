# Migration provenance record

This is a workflow record, not a research result. It changes no scientific conclusion.

## Source and destination

| | |
|---|---|
| Source repository | [junovhs/fractodactyl](https://github.com/junovhs/fractodactyl) (public) |
| Source branch | `research/dynamics-transfer-lab` |
| Source commit | [`314abc8afd5b89915a215f30c07692f77d6b3dec`](https://github.com/junovhs/fractodactyl/commit/314abc8afd5b89915a215f30c07692f77d6b3dec) (tree `d01f25f330625e078361ee2727cf45b2bea6e707`) |
| Destination | `junovhs/research`, default branch `main` (public, at the owner's direction) |
| Import date | 2026-10-13 |
| Method | Clean snapshot (`git archive` of the source commit) committed as a new root commit. **No Fractodactyl history or Git objects were imported.** |
| Prior contents of junovhs/research | An unrelated, stale application prototype (Rust/HTML). The owner directed that it be wiped; it was replaced, not merged, and is not part of this lab. |

The source branch is left intact in Fractodactyl as a read-only historical backup. Its full commit history (for example the pretest commits cited by R-006 to R-009 and PA-P-083) remains reachable there; those links in historical records are deliberately unchanged.

## Commit boundary

1. **Import commit** (root of `main`): all 54 tracked source files, byte-for-byte. Its Git tree hash equals the source commit's tree hash `d01f25f330625e078361ee2727cf45b2bea6e707`, which proves the snapshot is exact.
2. **Adaptation commit**: the new-repository operating changes listed below. Historical records are untouched.

## Exclusions

None were needed. The source tree contained only lab material: 54 text files of Markdown plus three standard-library Python helper files, with no renderer/application source, binaries, build outputs, dependencies, caches or secrets. A pattern scan for common credential formats found nothing. No `EVIDENCE/` directory existed at the source commit.

## Transformations (adaptation commit)

- `AGENTS.md` = `CLAUDE.md`: scope moved to junovhs/research, PR-based delivery, Fractodactyl out of scope.
- `AGENTS-READ-THIS/00`, `01`, `03`: repository/branch scope, PR + CI workflow, CI-versus-judgment limits, distinct review step. The research method itself is unchanged.
- `AGENTS-READ-THIS/02-LIVE-STATE.md`: operational lines only (location, update rule, migration note in the workflow handoff entry, a NOT_RECOVERED note on the R-014 companion). **Scientific state still R-014; no conclusion changed.**
- `README.md`: a new-location banner prepended; the historical text is otherwise unchanged.
- `scripts/research_run.py`: hardened (schema 2). It adds experiment identity, relative paths, an environment-bound fingerprint, fail-closed resume (`--resume-from/--checkpoint`), a refusal to declare compiled artifacts, a fresh per-run build directory, and stricter `verify`. It also fixes a bug: run IDs previously ended in `+00-00` instead of `Z`. No schema-1 manifests ever existed in the lab, so nothing is invalidated.
- `scripts/test_research_run.py`: extended regression tests. `scripts/README.md`: rewritten for the new tooling.
- New: `scripts/validate_lab.py` and `scripts/test_validate_lab.py` (static validator), `.github/workflows/lab-checks.yml` (CI), `EVIDENCE/LEGACY.json` (frozen-record hashes and the archive registry), `.gitignore`, this file, and `next-agent-please-do.md` (owner/agent follow-ups that could not be completed during migration).

## Legacy evidence status

1. **Present in the GitHub research branch, now imported:** all 54 files listed below. The 33 files in RESULTS/, PROMPTS/ and PRIOR_ART/ are hash-frozen in `EVIDENCE/LEGACY.json`.
2. **Accessible through verified durable external locations:** none found. No historical R-card names a durable URI.
3. **Mentioned historically but not recoverable from here:** the downloadable companion bundles of **R-013** (original; its timing samples were already lost before the archive correction), **R-013 archive reconstruction**, and **R-014**. These were delivered with ChatGPT sessions and never committed to Git. They are registered as `NOT_RECOVERED` together with their SHA-256 anchors, copied verbatim from the R-cards. No replacement files were created. If the owner still has them, place the files under the registered `recovered_path`, set `status` to `RECOVERED` and open a PR; CI will then check each file against its historical anchor. R-001 to R-012 never had in-repository archives; R-007 notes that its frozen scripts/logs were kept outside Git.

These records predate the CI. **None of R-001 to R-014 is claimed to have passed the new evidence validation**; CI only checks that the records remain byte-identical.

## Source inventory (commit 314abc8)

| Path | Bytes | SHA-256 at source | In destination |
|---|---|---|---|
| `AGENTS-READ-THIS/00-START-HERE.md` | 4675 | `f12fea9ef88c5cdb325dd6d4ffc738d1539f72d9c6472fe31d9cb335b882723b` | adapted in commit 2 |
| `AGENTS-READ-THIS/01-RULES-AND-METHOD.md` | 10230 | `cf041478cb125ac10b55455709709d976223676b3ed00178b34fd2b156fb2d35` | adapted in commit 2 |
| `AGENTS-READ-THIS/02-LIVE-STATE.md` | 6990 | `023350266560aff1a615baec74f68161e3dbed69cb66e4a0647d589a4ec98f11` | adapted in commit 2 |
| `AGENTS-READ-THIS/03-WRITEBACK-CHECKLIST.md` | 11073 | `bdd058882ecfebbb329b781099081aa5e6899093dfe7f7ef560b15643c40d360` | adapted in commit 2 |
| `AGENTS.md` | 2147 | `0bca3e4f02ff970cc3659c39b27b8956c93fb141b67d273a071779e2bef61180` | adapted in commit 2 |
| `CLAUDE.md` | 2147 | `0bca3e4f02ff970cc3659c39b27b8956c93fb141b67d273a071779e2bef61180` | adapted in commit 2 |
| `FRONTIER.md` | 14029 | `4ced27887d3f025943b0fd83fef8576d0a15363e530b0c041d6a881e521ff564` | unchanged |
| `GOAL.md` | 4204 | `c24f3199a676eb59e1664df9fcb74bf271bb652b570d32d417032f65f56d447d` | unchanged |
| `INDEX.md` | 8041 | `b579d44b01c55dfd819f5e80ea56b4068eebc8fd8e1df391277581128b4592ef` | unchanged |
| `LEAN.md` | 3288 | `eb6a7726b34c8905c2ab0ecdc28aeddc817ad735e94b623f99163bdf8a960383` | unchanged |
| `MAP.md` | 5259 | `3f53e37a05fd26cd620f5c59b99da4b7911f3c213c134ef8b81da6b50b77a6c7` | unchanged |
| `METHOD.md` | 5481 | `34221c4f7acb5ee1a34e3e41c4b7ed6e46c64d5e13aea010047e5a0b2e59e032` | unchanged |
| `PRIOR_ART.md` | 6218 | `b20375350ddcd3f28143621aa303eaf0033418fdffbcddcf58cfaf7946d5c278` | unchanged |
| `PRIOR_ART/PA-P-083.md` | 6770 | `c1b97cd6961e26865d0cd64e41bfae36d6020bd4d5adb7786cf2f6f921c0eba6` | unchanged |
| `PRIOR_ART/PA-PWM-RETRO.md` | 6956 | `9a3abbd303ebe31acb922af4874bb0ba684ef3a71eb6562cb0cf672ef2ac6bdd` | unchanged |
| `PRIOR_ART/TEMPLATE.md` | 2659 | `7422969839d1fd6f93b4cb9b3ca09b85dd221e2d5371ec5484366f5359e0ef7c` | unchanged |
| `PROMPTS/P-000.md` | 1042 | `10bbcb66acc22b12d3169a80f79862d7ec1ef851099f8a47aca7f0de59650a76` | unchanged |
| `PROMPTS/P-010.md` | 837 | `2856113a33b7d15ecf1bf814161953b281593febf6981657292a072bb7791ea2` | unchanged |
| `PROMPTS/P-020.md` | 855 | `ae307ba64e4cded3f69b07d7787069a901c92d2188665e5a80d7da77dc270468` | unchanged |
| `PROMPTS/P-021.md` | 973 | `9a88828a5b6464c0726c522c9217d9e98efd7c5206acde806467fcd3af7c24c6` | unchanged |
| `PROMPTS/P-022.md` | 835 | `d87c1163657960f058ac27b4e457ccf3a5ed1ebd6a9e0e027e34256437599793` | unchanged |
| `PROMPTS/P-030.md` | 1089 | `0d8ec2b6567eb728643feb743831ce1e15595d38f453118c8d18776d68cbcae2` | unchanged |
| `PROMPTS/P-040.md` | 2668 | `05fbfb29c687614517876b9f71a5d5371fc5e7cb7a5417417c34885674e3d2a7` | unchanged |
| `PROMPTS/P-050.md` | 894 | `f83bfb579656aff59fe32b0faf342460f910f9cadf7e04552573a96c780a4a37` | unchanged |
| `PROMPTS/P-051.md` | 3431 | `cca476d64bedb6407d6fdb44386c343f524b14fc2bb580e178c2dba44b7c44df` | unchanged |
| `PROMPTS/P-060.md` | 2708 | `2b8ae5f6f9902db9b5053a0befa3300b56561bc3b3e69b53e4d3d8dbf0e3d3a4` | unchanged |
| `PROMPTS/P-070.md` | 981 | `bb88bb2e2e0be11d4e5eca5cd4a097c1d9759d6743e7dc84738518d68ea28dfd` | unchanged |
| `PROMPTS/P-080.md` | 1273 | `12fa88fe7502256a28123777aaeb88897fd199e5006931a0f528b12886e7b429` | unchanged |
| `PROMPTS/P-081.md` | 1231 | `ba369e853170a8b4da364ce78377f3bd7e891d43415c84c9315622de1b9e8232` | unchanged |
| `PROMPTS/P-082.md` | 1209 | `0ceab02bd95a3b65f57ef8593a487602aaee2420a7f9a1bd15574d17c514cf74` | unchanged |
| `PROMPTS/P-083.md` | 1253 | `d4b5b50e1d61e00c606494ef4b25655f7d6fe93e9001d625eb19f315f5d5eb9f` | unchanged |
| `PROOF_OF_DONE.md` | 4865 | `cc8dff74e594a991d46fa9aaae33d54f33723b95ab5f694c1ad998b709779d07` | unchanged |
| `README.md` | 10906 | `2ba926c08439c79860c1cd5c85d302c7faaa8396a4565c809ff9c610dd98ee5b` | adapted in commit 2 |
| `RESULTS/R-001.md` | 1366 | `2b89afca31adfe36f1d88f88f282083d6da03767bdbf3e44af557e5d4d8a76c1` | unchanged |
| `RESULTS/R-002.md` | 1103 | `b18614abec0a4442f871c86b1024327a7ee5b7c8a4b58b6481d0d3145dd6d215` | unchanged |
| `RESULTS/R-003.md` | 1144 | `a25b81cde7236c89b79aae01f3dcac38e5ef7cc09104440737970bad1e9d98e9` | unchanged |
| `RESULTS/R-004.md` | 1254 | `2de66d4f62e3785f045f4c055590d991553914e127314895a154ac47095afda1` | unchanged |
| `RESULTS/R-005.md` | 1323 | `acf1a5a87ba688b66d5862722fb431037227c6df1c202a74a2889458d72fcad5` | unchanged |
| `RESULTS/R-006.md` | 6716 | `349a0a7548f6e1487cd099bad2b48ea33d05f6f79fdd47d1b09fc8da50d72bfc` | unchanged |
| `RESULTS/R-007.md` | 8673 | `fbc83c49ab8c3361f1f54391a76387060b9cea234746187443bb54d06386064b` | unchanged |
| `RESULTS/R-008.md` | 9328 | `1b694262cd5575e67e1c19a6e7abc554612cf43e69d345c4d981d2787a72a896` | unchanged |
| `RESULTS/R-009.md` | 10400 | `117c5e19448118be2af26b4e6d654c3de37669ad336d70393624ab4bc7bd5a4d` | unchanged |
| `RESULTS/R-010.md` | 8194 | `0dbdbc9cb8bb77c301f682fcf778445f60389978a973c506bf367685344e6d39` | unchanged |
| `RESULTS/R-011.md` | 13700 | `3670b32d5dd44f51dfe7dad41b3013bfac5805e91b21aa656162404888226a89` | unchanged |
| `RESULTS/R-012.md` | 4710 | `39433d1055d23ee07a484c1648b4225625bb0062dda06162f4293eb316a6c923` | unchanged |
| `RESULTS/R-013-archive-rerun.md` | 12186 | `029de5c314a621c4c3e3587da5b996ddd4080869bb38e9016b9a77d1306b6078` | unchanged |
| `RESULTS/R-013.md` | 21613 | `b427ff04376835663198ba78f4809a5f268fa31e5ad520a7c34950dfef3be13c` | unchanged |
| `RESULTS/R-014.md` | 16814 | `d56948f8ee2d19778c0dda41fe84e734ce14d19d03ace8cb9dd08e352fbf0b94` | unchanged |
| `SOURCES.md` | 10049 | `c57018bb3628dffc93f7a7a3f6380ea87d6a6f22705eb2f6fa8ad4811c968f4d` | unchanged |
| `TEMPLATES/QUESTION.md` | 1488 | `0ff933b9c8aed6b86f2db961acf095d76de9730e9a97567aac5eb902562e1740` | unchanged |
| `TEMPLATES/RESULT.md` | 4153 | `7267113fe01be86ae59411e5241266760c94b55989bd2cdcda898e2bc2bc666b` | unchanged |
| `scripts/README.md` | 1696 | `4befd10df9cc8c11406f70d7407bc1584976c9c1670ebe1531b7f90761cae48e` | adapted in commit 2 |
| `scripts/research_run.py` | 7443 | `d7017fd29b3f13994c746fccd78793d7a34886d1a16bc52f5a185ae86262fc38` | adapted in commit 2 |
| `scripts/test_research_run.py` | 2866 | `a3ae8a504bc8a36ed536a6aa7b780808f25b6c74140ee18996bab3b8d4a06cc4` | adapted in commit 2 |
