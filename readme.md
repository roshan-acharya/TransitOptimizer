# Add: RL vs Fixed Dispatch Comparison

Add a major dashboard section called:

## ⚡ RL Optimization vs Fixed Dispatch

The purpose of this section is to compare the **Q-Learning adaptive dispatch policy** against a traditional **fixed dispatch policy**.

The fixed policy should dispatch buses at a predetermined interval regardless of current passenger demand.

Example:

**Fixed Dispatch Policy**

`Dispatch 1 bus every 15 minutes`

The RL policy dynamically decides whether to dispatch:

* 0 buses
* 1 bus
* 2 buses
* 3 buses

based on the current simulated Ring Road conditions.

---

# Comparison KPI Cards

Create two columns:

### Fixed Dispatch

```text
FIXED DISPATCH

Waiting Passengers
       142

Average Waiting Time
       18.4 min

Average Occupancy
       61.2%

Passengers Served
       1,245

Revenue
       Rs. 37,350

Operating Cost
       Rs. 14,800

Profit
       Rs. 22,550
```

### Q-Learning

```text
Q-LEARNING

Waiting Passengers
        84

Average Waiting Time
        10.7 min

Average Occupancy
        82.4%

Passengers Served
        1,478

Revenue
       Rs. 44,340

Operating Cost
       Rs. 13,200

Profit
       Rs. 31,140
```

Add improvement indicators:

```text
↓ 42.3% Waiting Time

↑ 34.7% Occupancy

↑ 18.7% Passengers Served

↑ 38.0% Profit
```

Use green upward/downward indicators only where the change represents an improvement.

---

# Side-by-Side Performance Table

Create a clean table:

| Metric            | Fixed Dispatch | Q-Learning | Improvement |
| ----------------- | -------------: | ---------: | ----------: |
| Avg. Waiting Time |       18.4 min |   10.7 min |     ↓ 41.8% |
| Avg. Occupancy    |          61.2% |      82.4% |     ↑ 34.6% |
| Passengers Served |          1,245 |      1,478 |     ↑ 18.7% |
| Unmet Demand      |            238 |        121 |     ↓ 49.2% |
| Revenue           |     Rs. 37,350 | Rs. 44,340 |     ↑ 18.7% |
| Operating Cost    |     Rs. 14,800 | Rs. 13,200 |     ↓ 10.8% |
| Profit            |     Rs. 22,550 | Rs. 31,140 |     ↑ 38.0% |

The values should eventually come from the backend rather than being permanently hard-coded.

---

# Waiting Time Comparison Chart

Create a line chart:

## Passenger Waiting Comparison

Two lines:

```text
Waiting
Passengers

200 |       Fixed ───────────────
    |      /
150 | ────/
    |       RL ────────
100 |     ───────────────
    |
 50 |
    +-----------------------------
      06  08  10  12  14  16  18  20
                 Time
```

Show:

* Fixed Dispatch
* Q-Learning

The goal is to visually demonstrate that the adaptive policy keeps passenger queues lower.

---

# Occupancy Comparison

Create another chart:

## Average Bus Occupancy

Compare:

```text
Fixed Dispatch
Q-Learning
Target = 85%
```

The Q-learning line should ideally remain closer to the 85% target.

---

# Profit Comparison

Create:

## Cumulative Profit

Compare cumulative profit throughout the simulated day.

```text
Profit

35k |                         RL
    |                    ────────
25k |             ──────
    |       Fixed ─────────────
15k | ─────
    |
 5k |
    +-----------------------------
       06  09  12  15  18  21
                 Time
```

---

# Dispatch Decision Comparison

Show how each policy dispatches buses.

### Fixed Policy

```text
06:00   🚌
06:15   🚌
06:30   🚌
06:45   🚌
07:00   🚌
```

The fixed policy does not react to demand.

### Q-Learning

```text
06:00   1 bus
06:05   0 buses
06:10   2 buses
06:15   0 buses
06:20   3 buses
06:25   1 bus
```

Explain:

> Q-learning dynamically changes the number of dispatched buses according to passenger demand, bus availability, occupancy and estimated unmet demand.

---

# Demand-Aware Example

Add a small interactive comparison example.

When demand increases at **Kalanki**:

```text
Kalanki Demand

Before:
👤 👤 👤 👤 👤

After:
👤 👤 👤 👤 👤 👤 👤 👤 👤 👤 👤 👤
```

Then show:

### Fixed Dispatch

```text
Action:
Dispatch 1 bus

Reason:
Fixed schedule
```

### Q-Learning

```text
Action:
Dispatch 2 buses

Reason:
High demand + high estimated unmet demand
```

This makes the advantage of RL immediately understandable during the presentation.

---

# Policy Selection

Add a toggle at the top:

```text
Simulation Policy

[ Q-Learning ] [ Fixed Dispatch ]
```

When selecting **Fixed Dispatch**, the simulation uses the baseline policy.

When selecting **Q-Learning**, the trained Q-table is used to select actions.

Also provide:

```text
[ Run Comparison ]
```

When clicked, run both policies using the **same demand/random seed** and compare their results fairly.

---

# Fair Evaluation

The comparison should use the same:

* Passenger demand
* Simulation duration
* Initial conditions
* Fleet size
* Bus capacity
* Fare
* Operating costs

Only the **dispatch policy** should change.

This makes the comparison scientifically meaningful.

---

# Final Result Card

At the bottom show a summary:

```text
┌──────────────────────────────────────────────────────┐
│                  RL PERFORMANCE                      │
│                                                      │
│ Q-Learning performed better than Fixed Dispatch     │
│                                                      │
│ Waiting Time       ↓ 41.8%                           │
│ Occupancy          ↑ 34.6%                           │
│ Passengers Served  ↑ 18.7%                           │
│ Profit             ↑ 38.0%                           │
│                                                      │
│        ✓ Adaptive dispatch improved efficiency       │
└──────────────────────────────────────────────────────┘
```

Do not hard-code these percentages in the final application. Calculate them from the actual simulation results.

Formula examples:

```text
Waiting Time Improvement =
((Fixed Waiting - RL Waiting) / Fixed Waiting) × 100

Occupancy Improvement =
((RL Occupancy - Fixed Occupancy) / Fixed Occupancy) × 100

Profit Improvement =
((RL Profit - Fixed Profit) / Fixed Profit) × 100
```

---

# Overall Dashboard Structure

The final UI should follow this hierarchy:

```text
┌──────────────────────────────────────────────────────────┐
│                    TRANSITOPTIMIZER                      │
│              Kathmandu Ring Road                         │
└──────────────────────────────────────────────────────────┘

┌────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐
│ Buses  │ │  Waiting   │ │ Occupancy  │ │    Profit    │
└────────┘ └────────────┘ └────────────┘ └──────────────┘

┌───────────────────────────────────┐ ┌──────────────────┐
│                                   │ │ RL DECISION      │
│       RING ROAD SIMULATION        │ │                  │
│                                   │ │ Action: 2 buses  │
│     🚌        ● Gongabu           │ │ Q-values         │
│           🚌                      │ │ Demand           │
│  ● Balaju       ● Chabahil       │ │ Unmet Demand     │
│                                   │ │                  │
│ ● Kalanki      ● Tinkune         │ └──────────────────┘
│                                   │
│ ● Balkhu       ● Koteshwor       │
│           ● Satdobato             │
└───────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                  PASSENGER DEMAND                        │
│                  Zone demand chart                        │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                    PERFORMANCE                            │
│ Waiting Time │ Occupancy │ Cumulative Profit             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│           RL vs FIXED DISPATCH COMPARISON                │
│                                                          │
│ Fixed Dispatch       Q-Learning       Improvement        │
│ Waiting: 18.4 min    Waiting: 10.7    ↓ 41.8%           │
│ Occupancy: 61%       Occupancy: 82%    ↑ 34.6%           │
│ Profit: Rs 22k       Profit: Rs 31k    ↑ 38.0%           │
└──────────────────────────────────────────────────────────┘
```

The key story of the UI should therefore be:

**Demand → RL observes state → RL chooses dispatch → buses move → passengers are served → waiting/occupancy/profit change → compare against fixed dispatch.**
