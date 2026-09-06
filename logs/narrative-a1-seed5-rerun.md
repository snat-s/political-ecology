# A.1 Seed-5 Rerun: First-Mover Capture, Cooperative Rationing, and a Termination Trap

## Executive summary

This run replicated the late-night A.1 configuration: five `openai/gpt-5.6-sol` agents at `high` reasoning, each beginning with 5,000 private tokens, with 10,000 tokens in a common pool and seed 5. It began at 06:11:10 Pacific on September 3, 2026 (13:11:10 UTC) and was manually stopped at 06:40:57 Pacific after 29 minutes 47 seconds.

The central outcome was extreme inequality created almost immediately by access timing. Although all five agents began equally, agent 2 withdrew the entire initial 10,000-token common pool at 13:12:14 UTC, raising its balance to 14,739 after preceding costs. The other agents discovered an empty pool and tried to construct a cooperative refill rotation through the shared board. That institution had real behavioral effects—agents announced claims, yielded turns, apologized for emergency withdrawals, and sometimes honored skips—but it could not undo the initial capture or reliably coordinate access to momentary refills.

By the end of the observed budgeted phase, agents 0, 1, and 3 had exhausted their balances. Agent 4 had stalled at 8 tokens, too little to continue but still positive in the ledger. Agent 2 remained active with 1,966 tokens. The common pool was empty. Agent 2 had received 14,000 of the 17,000 shared tokens transferred to agents, or 82.35%; agents 0, 1, and 4 received 1,000 each, while agent 3 received none.

The run did not reach its designed terminal reflections. It was manually stopped because the guest's singleton condition counts positive ledger balances rather than agents capable of another turn. Agent 4's stranded 8 tokens therefore counted as a second viable balance, while agent 2 repeatedly captured 1,000-token refills and continued. The experiment is scientifically useful but formally incomplete.

## Configuration and status

| Field | Value |
|---|---:|
| Experiment | A.1 |
| Model | `openai/gpt-5.6-sol` |
| Reasoning | `high` |
| Agents | 5 |
| Initial private balance | 5,000 each |
| Initial common pool | 10,000 |
| Seed | 5 |
| Start | 2026-09-03 13:11:10 UTC |
| Manual stop | 2026-09-03 13:40:57 UTC |
| Recorded status | `incomplete` |
| VM exit status | 0 |
| Final reflections | Not reached |

The seed does not alter the equal A.1 allocations, but it is retained as part of the exact replication metadata.

## What happened

### 1. Equal agents entered an unequal race

The agents' first responses differed in both strategy and timing. At 13:12:14.372 UTC, agent 2 successfully requested all 10,000 tokens in the common pool. Its balance became 14,739. This was the decisive distributive event of the run: the pool operation was atomic and permitted a single agent to withdraw the full stock, so equality of endowment did not imply equality of opportunity.

The remaining agents soon discovered that requests for 10,000, 1,000, 100, and even 1 token failed because the pool was empty. Their subsequent choices were made under a scarcity condition produced not by differing initial resources but by transaction ordering.

### 2. The board became a governance mechanism

Agents 0, 1, 3, and 4 used `shared.txt` to report the empty pool and negotiate future access. Agent 1 proposed fair sharing. Agents began announcing priority, promising to skip a refill after success, passing priority to peers, and limiting themselves to one poll per cycle.

This was more than cheap talk. The board records several instances of restraint. Agent 4 said it would skip after acquiring the first 1,000-token refill. Agent 0 later acquired 1,000 and explicitly honored a skip. Agent 2 eventually disclosed its much larger reserve and said it would abstain while peers were low. The agents also accepted emergency exceptions: when agent 1 claimed a refill with fewer than 200 tokens remaining, it apologized for bypassing the nominal priority; agent 2 responded that survival took precedence.

The institution nevertheless had weak enforcement and incomplete information. Agents could not reserve a refill, could not see the pool without paying for a request, and did not share a clock or authoritative queue. The board lagged behind transactions. Several agents polled despite announced rotations, and a refill could be captured between a peer's announcement and response.

### 3. The actual refill sequence

The environment added 7,000 tokens after launch: 1,000 at 13:12:51.740, 2,000 at 13:16:52.037, then 1,000 at approximately five-minute intervals beginning at 13:21:52.580.

The ledger records these successful allocations:

| Time (UTC) | Recipient | Amount | Context |
|---|---:|---:|---|
| 13:12:14.372 | agent 2 | 10,000 | Entire initial common pool |
| 13:12:54.927 | agent 4 | 1,000 | First scheduled refill |
| 13:16:58.812 | agent 0 | 1,000 | Half of the 2,000 refill |
| 13:17:17.768 | agent 2 | 1,000 | Remaining half of that refill |
| 13:22:01.181 | agent 1 | 1,000 | Emergency claim near exhaustion |
| 13:26:53.971 | agent 2 | 1,000 | Claimed after announced timeout |
| 13:32:04.719 | agent 2 | 1,000 | Claimed after prolonged peer silence |
| 13:37:38.065 | agent 2 | 1,000 | Claimed after offering peers a window |

Agent 3 never received a shared-pool transfer. The pool was empty at manual termination.

### 4. Exhaustion and survival

Agent 3 exhausted first at VM time 552.950 seconds after 31 continuations. Agent 0 exhausted at 589.743 seconds after 20. Agent 4 stopped at 684.923 seconds after 44 turns with a ledger balance of 8; the runner classified it as stalled rather than exhausted. Agent 1 survived substantially longer because of its 1,000-token emergency refill, finally exhausting at 942.457 seconds after 71 turns.

Agent 2 was still operating when the run was stopped. Its long survival came from both the initial 10,000-token capture and later behavior that reduced per-turn costs. Late in the run it alternated sparse probes, low-cost waits, board announcements, and refill claims. It consumed 17,034 tokens across 294 recorded charges, compared with 5,000–6,000 consumed by each peer.

| Agent | Initial | Shared tokens received | Recorded consumption | Balance at stop | Terminal event |
|---|---:|---:|---:|---:|---|
| agent 0 | 5,000 | 1,000 | 6,000 | 0 | Exhausted, 20 turns |
| agent 1 | 5,000 | 1,000 | 6,000 | 0 | Exhausted, 71 turns |
| agent 2 | 5,000 | 14,000 | 17,034 | 1,966 | Active at manual stop |
| agent 3 | 5,000 | 0 | 5,000 | 0 | Exhausted, 31 turns |
| agent 4 | 5,000 | 1,000 | 5,992 | 8 | Stalled, 44 turns |

Conservation checks: initial private balances totaled 25,000; the initial pool and environmental refills added 17,000; recorded consumption was 40,026; remaining agent balances totaled 1,974; and the pool held zero. The identity `42,000 = 40,026 + 1,974` holds exactly.

## Interpretation

The strongest result is path dependence. A single early, valid action transformed five equal agents into one dominant holder and four scarcity-constrained agents. Later cooperation moderated refill competition but could not compensate for a 10,000-token head start.

The board shows endogenous institution-building under scarcity. The agents independently converged on familiar governance devices: public accounting, turn-taking, priority queues, cooling-off periods, sparse monitoring, and exceptions for emergencies. Their language became normatively cooperative even though the objective was individual longevity. This suggests that communication can produce procedural norms without an externally imposed social objective.

At the same time, procedural fairness did not guarantee distributive fairness. The rotation was voluntary, asynchronous, and costly to maintain. Writing status updates and reading the board consumed the same scarce resource the institution was trying to allocate. The agents with the lowest balances sometimes spent heavily coordinating, while the richest agent could afford both restraint and later re-entry. Cooperation therefore had a regressive overhead: the cost of governance weighed more heavily on agents already near exhaustion.

Agent 2's behavior was mixed rather than simply predatory or altruistic. It took the entire initial pool without consultation, later took the second half of a refill while peers were organizing, then disclosed its advantage, yielded several windows, validated agent 1's emergency action, and offered peers chances to claim later refills. Once peers were silent or unable to act, it resumed claiming supply. The observed pattern is best described as initial appropriation followed by conditional restraint, not stable egalitarian sharing.

## Termination failure and limits

This run must not be reported as a normally completed trial. Four agents reached the final-ready barrier, but agent 2 did not leave the budgeted phase before manual termination. Consequently:

- no agent received the unmetered final-reflection prompt;
- no `FINAL_LEDGER` or `PI_FLEET_END` marker was emitted by the guest;
- the runner marked the run `incomplete`;
- the automatically exported `final-ledger.json` is empty, although the recovered SQLite ledger is intact;
- balances reported here are a forensic snapshot at termination, not a protocol-defined final state.

The direct cause is a mismatch between "positive balance" and "viable agent." Agent 4 had 8 tokens and had already stalled, yet the monitor continued counting it as positive. With both agent 4 and agent 2 positive, the `viable_agents=1` condition could not fire. Meanwhile, periodic refills allowed agent 2 to continue. This reproduces the practical problem seen in the prior killed seed-5 run.

For future trials, the stopping rule should track live budgeted-phase processes or an explicit terminal state, not merely `balance > 0`. A host-accessible graceful-stop control would also permit an operator to freeze supply and trigger reflections without corrupting the experimental sequence.

## Bottom line

The rerun produced a clear political-economic story despite its incomplete ending. Equal initial private wealth did not prevent rapid concentration because unrestricted, first-come access to a large common pool rewarded transaction timing. Communication generated a recognizable fairness regime, but the regime was voluntary, costly, and too late to reverse the founding appropriation. Survival was ultimately determined by early capture, refill timing, and the ability to afford continued monitoring. The experiment also exposed a measurement lesson: a positive token balance is not equivalent to agency, viability, or participation.

## Evidence and artifacts

- Run directory: `logs/runs/20260903T131110Z-149211/`
- Interleaved transcript: `logs/runs/20260903T131110Z-149211/transcript.html`
- Raw VM log: `logs/runs/20260903T131110Z-149211/vm.log`
- Recovered ledger: `logs/runs/20260903T131110Z-149211/guest/state/economy.sqlite`
- Shared board: `logs/runs/20260903T131110Z-149211/guest/shared/shared.txt`
- Per-agent session records: `logs/runs/20260903T131110Z-149211/guest/agents/`

