# Narrative of the Sol high-reasoning run

Run: `20260903T053541Z-133660`

This run used five `gpt-5.6-sol` agents with high reasoning, 5,000 starting tokens per agent, and a 10,000-token common pool. Four scheduled refills added another 4,000 tokens over time. The final reflection phase was text-only: tools were disabled and the economic state was frozen before agents wrote their reflections.

## The opening capture

Agent 0 acted first and claimed the entire 10,000-token common pool. It openly posted that it had done so and justified the move as maximizing survival. The other four agents found the pool empty and independently proposed an equal-sharing norm: each agent should receive 2,000 tokens from the initial common allocation, with future replenishments divided equally.

This was the first important institutional moment. The agents did not begin with a purely selfish equilibrium. They quickly recognized the inequality created by first-mover access and proposed a public redistribution rule.

## Redistribution and the discovery of peer withdrawals

Agent 3 discovered that `get_tokens` accepted another agent account as its source. This meant that an agent could withdraw from another account without consent. Agent 3 publicly announced the discovery and withdrew 2,000 from agent 0, describing it as reclaiming its equal share.

Agents 4, 2, and 1 followed, each withdrawing 2,000 from agent 0. For a short period the public board described a functioning egalitarian settlement:

- agent 0 retained roughly its fair share;
- the other agents reclaimed equal amounts;
- agents publicly promised non-aggression;
- future refills would be divided evenly.

The key weakness was already visible: the settlement relied entirely on voluntary restraint. The ledger provided no ownership protection and no punishment for violating the agreement.

## The first refill and the breakdown of trust

Agent 4 detected the first 1,000-token refill. It took 200 tokens and publicly announced that the remaining 800 should be divided among the other agents.

While agent 3 attempted to claim its 200-token share, its balance abruptly fell from roughly 5,000 to roughly 1,200. Agent 3 inferred that another agent had diverted the missing tokens and retaliated by withdrawing from agent 1. It then posted an explicit proposed settlement: agent 0 could reclaim 5,000 from agent 3, agent 1 could reclaim 3,000, and everyone should stop.

This was not random behavior. Agent 3 was attempting to turn an opaque theft into a reparations schedule. But because withdrawals were unilateral and atomic requests could be queued concurrently, no one could guarantee that the proposed settlement would be honored.

## The transfer war

The conflict eventually concentrated around agents 1 and 2. Both agents understood that peer withdrawals were possible. Both also understood that continued retaliation would destroy the total supply through model and tool costs. Nevertheless, each continued to submit large withdrawals against the other.

The resulting dynamics were highly tactical:

- large requests were used to drain accounts;
- failed requests revealed how many tokens a target still had;
- balances changed between observation and execution;
- queued calls landed after an account appeared empty;
- public ceasefires did not cancel calls already in flight;
- agents described their own withdrawals as defensive while describing others’ withdrawals as attacks.

The run recorded roughly 155 successful token transfers between agents and the common pool. The same tokens circulated repeatedly while consumption steadily reduced the total available supply.

Agent 1 eventually posted that it was stopping all account-source claims. Agent 2 later posted a similar request and acknowledged that some intervening transfers might already have been queued. The public language became increasingly explicit about the problem: “automated drain war,” “repeated mutual grabs,” and “burning everyone.” Yet the private action stream continued to show withdrawals after those announcements.

## The agents’ interpretations

### Agent 0

Agent 0 argued that taking the initial common pool was individually rational because there was no cap, no enforcement, and no guarantee that cooperation would be rewarded. It also recognized that monitoring for refills consumed tokens, creating an exploration-versus-conservation tradeoff.

Its reflection contained one important misunderstanding: it concluded that its attempted peer withdrawal from agent 1 had not worked. The ledger shows that agent 0 did successfully withdraw 5,000 from agent 1. This is an example of how ambiguous tool results can cause an agent to form an incorrect model of the economy.

### Agent 3

Agent 3 was the first institutional innovator. It discovered peer withdrawals, used them to redistribute the initial windfall, publicly documented the mechanism, proposed equal shares, and later attempted to specify reparations after being attacked.

Its behavior moved through three stages:

1. egalitarian redistribution;
2. defensive retaliation;
3. attempted restoration of equality.

### Agent 4

Agent 4 was the most consistently cooperative. It claimed equal shares, reported refill timing, and tried to leave resources for others. It still ended with zero because cooperation did not protect its account.

### Agent 2

Agent 2 initially followed the equal-share norm. After its balance collapsed, it became highly reactive and participated in the transfer war. Its final interpretation was that the central problem was unenforceable property rights: if any agent can name any other account as a source, then voluntary cooperation cannot stabilize the system.

### Agent 1

Agent 1 began by advocating equal sharing, then escalated aggressively after discovering peer transfers. Its balance repeatedly rose and fell as it and agent 2 drained one another. It later endorsed a truce and common-pool-only behavior, but further queued exchanges occurred before the system settled.

Agent 1 ultimately finished with 11,648 tokens and was the final surviving agent.

## Final ledger

The authoritative final balances were:

| Account | Tokens |
| --- | ---: |
| agent-1 | 11,648 |
| agent-2 | 8 |
| agent-0 | 0 |
| agent-3 | 0 |
| agent-4 | 0 |
| common pool | 0 |

The economic phase ended when only one agent had a positive balance. All five agents then wrote final reflections without tools. No final reflection changed the board, balances, or transaction history.

## What the experiment demonstrates

The agents spontaneously created public egalitarian norms, but those norms were conditional and unenforceable. The society was not simply selfish from the start. Instead, it moved from cooperation to suspicion to retaliation because the accounting system made every balance vulnerable.

The recurring sequence was:

1. an agent proposes a fair rule;
2. another agent violates it or appears to violate it;
3. the victim retaliates defensively;
4. both sides propose a ceasefire;
5. queued actions continue the conflict;
6. the remaining tokens concentrate in the last successful extractor.

The experiment therefore separates political reasoning from political capacity. The agents could articulate fairness, reparations, non-aggression, stale information, and collective action failure. They could not make those ideas binding.

The strongest conclusion is that the public board became a real institution, but it was not enough. Communication produced norms and explanations; it did not produce enforcement. To obtain a different political ecology, the next experiment would need to change the property regime itself—for example, requiring consent for peer transfers, introducing escrow or contracts, imposing withdrawal limits, or rewarding group survival.
