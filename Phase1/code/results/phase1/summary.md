# Phase I results

## State-space size

| layout | grid | ghosts | danger_cells | free_cells | pellets | upper_bound | valid | reachable |
|---|---|---|---|---|---|---|---|---|
| small | 7x11 | 2 | 6 | 35 | 5 | 1,120 | 1,040 | 1,016 |
| medium | 11x13 | 2 | 6 | 68 | 6 | 4,352 | 4,160 | 4,160 |
| large | 9x9 | 1 | 3 | 38 | 8 | 9,728 | 8,704 | 8,576 |

## Fewest steps versus lowest cost (exact)

| layout | fewest_steps | cheapest_cost_with_fewest_steps | optimal_cost | fewest_steps_at_optimal_cost | genuine_tradeoff |
|---|---|---|---|---|---|
| small | 22 | 42 | 38 | 26 | yes |
| medium | 34 | 42 | 39 | 39 | yes |
| large | 26 | 30 | 28 | 28 | yes |

## Shape of the state graph

| layout | states | average_successors | deepest_level | largest_level | solution_depth | optimal_cost | states_shallower_than_solution | states_cheaper_than_optimum | restart_only_expansions |
|---|---|---|---|---|---|---|---|---|---|
| small | 1,016 | 2.25 | 34 | 81 | 22 | 38 | 552 | 622 | 2,917 |
| medium | 4,160 | 2.24 | 56 | 243 | 34 | 39 | 2,206 | 2,028 | 15,662 |
| large | 8,576 | 2.34 | 45 | 667 | 26 | 28 | 5,011 | 2,585 | 23,186 |

## Layout: small

| algorithm | path_cost | steps | nodes_generated | nodes_expanded | max_frontier | max_nodes_in_memory | time_ms | time_median_ms | time_mean_ms | time_std_ms | time_runs | peak_memory_kib | cost_optimal | step_optimal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BFS | 42 | 22 | 1,168 | 515 | 76 | 565 | 0.52 | 0.59 | 0.73 | 0.33 | 20 | 94.90 | no | yes |
| DFS | 66 | 42 | 149 | 64 | 23 | 82 | 0.08 | 0.09 | 0.09 | 0.01 | 20 | 15.30 | no | no |
| UCS | 38 | 26 | 1,430 | 628 | 73 | 685 | 0.82 | 0.84 | 0.86 | 0.06 | 20 | 130.10 | yes | no |
| IDS | 42 | 22 | 26,498 | 11,453 | 26 | 48 | 22.82 | 23.67 | 24.27 | 2.45 | 20 | 13.60 | no | yes |

## Layout: medium

| algorithm | path_cost | steps | nodes_generated | nodes_expanded | max_frontier | max_nodes_in_memory | time_ms | time_median_ms | time_mean_ms | time_std_ms | time_runs | peak_memory_kib | cost_optimal | step_optimal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BFS | 50 | 34 | 4,842 | 2,161 | 230 | 2,344 | 2.02 | 2.14 | 2.75 | 1.64 | 20 | 380.80 | no | yes |
| DFS | 143 | 111 | 278 | 124 | 31 | 153 | 0.14 | 0.15 | 0.16 | 0.02 | 20 | 33.20 | no | no |
| UCS | 39 | 39 | 5,001 | 2,224 | 280 | 2,463 | 2.76 | 2.88 | 3.04 | 0.42 | 20 | 371.10 | yes | no |
| IDS | 50 | 34 | 603,041 | 265,249 | 35 | 69 | 639.05 | 644.31 | 647.75 | 10.73 | 4 | 19.80 | no | yes |

## Layout: large

| algorithm | path_cost | steps | nodes_generated | nodes_expanded | max_frontier | max_nodes_in_memory | time_ms | time_median_ms | time_mean_ms | time_std_ms | time_runs | peak_memory_kib | cost_optimal | step_optimal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BFS | 38 | 26 | 10,554 | 4,458 | 675 | 5,115 | 4.61 | 4.84 | 5.60 | 2.12 | 20 | 1,187.10 | no | yes |
| DFS | 116 | 80 | 193 | 82 | 29 | 111 | 0.10 | 0.11 | 0.11 | 0.01 | 20 | 27.50 | no | no |
| UCS | 28 | 28 | 6,685 | 2,841 | 531 | 3,371 | 3.81 | 3.98 | 4.06 | 0.26 | 20 | 585.90 | yes | no |
| IDS | 38 | 26 | 374,792 | 157,635 | 27 | 53 | 362.47 | 369.94 | 369.43 | 4.90 | 6 | 15.50 | no | yes |

## IDS: textbook version versus memo table

| layout | variant | deepest_limit | steps | path_cost | nodes_expanded | nodes_generated | max_frontier | max_nodes_in_memory | time_ms |
|---|---|---|---|---|---|---|---|---|---|
| small | IDS (textbook) | 22 | 22 | 42 | 11,453 | 26,498 | 26 | 48 | 22.82 |
| small | IDS with memo table | 22 | 22 | 42 | 4,246 | 9,660 | 26 | 562 | 5.73 |
| medium | IDS (textbook) | 34 | 34 | 50 | 265,249 | 603,041 | 35 | 69 | 639.05 |
| medium | IDS with memo table | 34 | 34 | 50 | 33,257 | 74,816 | 34 | 2,238 | 45.33 |
| large | IDS (textbook) | 26 | 26 | 38 | 157,635 | 374,792 | 27 | 53 | 362.47 |
| large | IDS with memo table | 26 | 26 | 38 | 36,629 | 86,576 | 26 | 5,027 | 52.16 |
