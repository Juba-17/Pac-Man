# Phase II results

## Heuristics (checked on every reachable state)

| layout | heuristic | states_checked | transitions_checked | admissible | consistent | worst_overestimate | mean_ratio | h_start | true_cost_start | setup_ms | distinct_values | states_below_start_value | goal_below_start_value | h2_dominates_h1 | states_where_h2_is_larger |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| small | h1 | 1,016 | 2,288 | yes | yes | 0 | 0.46 | 12 | 38 | 0.00 | 13 | 237 | no | yes | 768 |
| small | h2 | 1,016 | 2,288 | yes | yes | 0 | 0.71 | 22 | 38 | 0.04 | 26 | 520 | yes | yes | 768 |
| medium | h1 | 4,160 | 9,312 | yes | yes | 0 | 0.51 | 18 | 39 | 0.00 | 19 | 1,017 | no | yes | 3,599 |
| medium | h2 | 4,160 | 9,312 | yes | yes | 0 | 0.88 | 34 | 39 | 0.08 | 38 | 2,097 | yes | yes | 3,599 |
| large | h1 | 8,576 | 20,096 | yes | yes | 0 | 0.46 | 12 | 28 | 0.00 | 13 | 2,018 | no | yes | 8,061 |
| large | h2 | 8,576 | 20,096 | yes | yes | 0 | 0.86 | 24 | 28 | 0.06 | 26 | 4,341 | yes | yes | 8,061 |

## Layout: small

### Search algorithms

| algorithm | path_cost | steps | nodes_generated | nodes_expanded | max_frontier | max_nodes_in_memory | time_ms | time_median_ms | time_mean_ms | time_std_ms | time_runs | peak_memory_kib | cost_optimal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BFS | 42 | 22 | 1,168 | 515 | 76 | 565 | 0.53 | 0.56 | 0.67 | 0.24 | 20 | 94.90 | no |
| DFS | 66 | 42 | 149 | 64 | 23 | 82 | 0.09 | 0.10 | 0.10 | 0.02 | 20 | 15.30 | no |
| UCS | 38 | 26 | 1,430 | 628 | 73 | 685 | 0.79 | 0.83 | 0.90 | 0.24 | 20 | 130.10 | yes |
| IDS | 42 | 22 | 26,498 | 11,453 | 26 | 48 | 22.27 | 23.07 | 23.31 | 0.89 | 20 | 13.60 | no |
| Greedy (h1) | 67 | 39 | 841 | 368 | 44 | 412 | 0.72 | 0.74 | 0.75 | 0.03 | 20 | 102.00 | no |
| Greedy (h2) | 42 | 22 | 59 | 25 | 14 | 39 | 0.12 | 0.13 | 0.14 | 0.01 | 20 | 19.60 | no |
| A* (h1) | 38 | 26 | 977 | 423 | 79 | 498 | 0.85 | 0.87 | 0.91 | 0.09 | 20 | 117.20 | yes |
| A* (h2) | 38 | 26 | 211 | 90 | 32 | 122 | 0.28 | 0.29 | 0.30 | 0.02 | 20 | 40.90 | yes |

### Local search (30 seeds)

| algorithm | runs | best | mean | worst | std | optimal_runs | mean_evaluations | mean_iterations | run_time_ms | setup_ms | time_ms | time_std_ms | peak_memory_kib | orders_in_memory |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Hill Climbing | 30 | 38 | 39.43 | 43 | 2.08 | 20 | 28.70 | 1.80 | 0.02 | 0.11 | 0.14 | 0.01 | 17.50 | 12 |
| Simulated Annealing | 30 | 38 | 38 | 38 | 0.00 | 30 | 920 | 919 | 1.16 | 0.11 | 1.27 | 0.02 | 19.00 | 3 |
| Genetic Algorithm | 30 | 38 | 38 | 38 | 0.00 | 30 | 930 | 30 | 3.85 | 0.11 | 3.96 | 0.04 | 25.30 | 61 |
| Hill Climbing (9 restarts) | 30 | 38 | 38 | 38 | 0.00 | 30 | 285.70 | 17.60 | 0.14 | 0.11 | 0.26 | 0.01 | 20.70 | 12 |
| Random sampling (920 orders) | 30 | 38 | 38 | 38 | 0.00 | 30 | 920 | 920 | 0.89 | 0.11 | 1.00 | 0.01 | 18.60 | 2 |

### All algorithms

| algorithm | family | cost | cost_range | steps | time_ms | peak_memory_kib | memory_items | effort | found_optimum | complete | optimal_guaranteed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BFS | uninformed | 42 | - | 22 | 0.53 | 94.90 | 565 | 515 | no | yes | no (fewest steps only) |
| DFS | uninformed | 66 | - | 42 | 0.09 | 15.30 | 82 | 64 | no | yes (finite space, explored set) | no |
| UCS | uninformed | 38 | - | 26 | 0.79 | 130.10 | 685 | 628 | yes | yes | yes |
| IDS | uninformed | 42 | - | 22 | 22.27 | 13.60 | 48 | 11,453 | no | yes | no (fewest steps only) |
| Greedy (h1) | informed | 67 | - | 39 | 0.72 | 102.00 | 412 | 368 | no | yes (finite space) | no |
| Greedy (h2) | informed | 42 | - | 22 | 0.12 | 19.60 | 39 | 25 | no | yes (finite space) | no |
| A* (h1) | informed | 38 | - | 26 | 0.85 | 117.20 | 498 | 423 | yes | yes | yes (admissible heuristic) |
| A* (h2) | informed | 38 | - | 26 | 0.28 | 40.90 | 122 | 90 | yes | yes | yes (admissible heuristic) |
| Hill Climbing | local search | 39.43 | [38, 43] | - | 0.14 | 17.50 | 12 | 28.70 | 20/30 runs | yes (every order is a valid plan) | no |
| Simulated Annealing | local search | 38 | [38, 38] | - | 1.27 | 19.00 | 3 | 920 | 30/30 runs | yes (every order is a valid plan) | no |
| Genetic Algorithm | local search | 38 | [38, 38] | - | 3.96 | 25.30 | 61 | 930 | 30/30 runs | yes (every order is a valid plan) | no |
| Hill Climbing (9 restarts) | local search | 38 | [38, 38] | - | 0.26 | 20.70 | 12 | 285.70 | 30/30 runs | yes (every order is a valid plan) | no |
| Random sampling (920 orders) | baseline | 38 | [38, 38] | - | 1.00 | 18.60 | 2 | 920 | 30/30 runs | yes (every order is a valid plan) | no |

## Layout: medium

### Search algorithms

| algorithm | path_cost | steps | nodes_generated | nodes_expanded | max_frontier | max_nodes_in_memory | time_ms | time_median_ms | time_mean_ms | time_std_ms | time_runs | peak_memory_kib | cost_optimal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BFS | 50 | 34 | 4,842 | 2,161 | 230 | 2,344 | 2.11 | 2.16 | 2.46 | 0.79 | 20 | 380.80 | no |
| DFS | 143 | 111 | 278 | 124 | 31 | 153 | 0.14 | 0.15 | 0.16 | 0.02 | 20 | 33.20 | no |
| UCS | 39 | 39 | 5,001 | 2,224 | 280 | 2,463 | 2.77 | 2.82 | 2.87 | 0.17 | 20 | 371.10 | yes |
| IDS | 50 | 34 | 603,041 | 265,249 | 35 | 69 | 633.30 | 642.27 | 643.89 | 10.63 | 4 | 19.80 | no |
| Greedy (h1) | 82 | 54 | 2,909 | 1,294 | 90 | 1,380 | 2.51 | 2.54 | 2.59 | 0.10 | 20 | 380.30 | no |
| Greedy (h2) | 50 | 34 | 79 | 34 | 17 | 51 | 0.19 | 0.20 | 0.20 | 0.01 | 20 | 30.60 | no |
| A* (h1) | 39 | 39 | 1,293 | 569 | 111 | 680 | 1.19 | 1.24 | 1.25 | 0.04 | 20 | 146.80 | yes |
| A* (h2) | 39 | 39 | 199 | 86 | 27 | 113 | 0.30 | 0.32 | 0.32 | 0.01 | 20 | 47.50 | yes |

### Local search (30 seeds)

| algorithm | runs | best | mean | worst | std | optimal_runs | mean_evaluations | mean_iterations | run_time_ms | setup_ms | time_ms | time_std_ms | peak_memory_kib | orders_in_memory |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Hill Climbing | 30 | 39 | 39.10 | 40 | 0.31 | 27 | 42.50 | 1.80 | 0.03 | 0.23 | 0.26 | 0.01 | 26.70 | 17 |
| Simulated Annealing | 30 | 39 | 39 | 39 | 0.00 | 30 | 920 | 919 | 1.18 | 0.23 | 1.41 | 0.02 | 26.70 | 3 |
| Genetic Algorithm | 30 | 39 | 39 | 39 | 0.00 | 30 | 930 | 30 | 3.96 | 0.23 | 4.19 | 0.07 | 32.40 | 61 |
| Hill Climbing (9 restarts) | 30 | 39 | 39 | 39 | 0.00 | 30 | 429.50 | 18.00 | 0.21 | 0.23 | 0.44 | 0.02 | 28.30 | 17 |
| Random sampling (920 orders) | 30 | 39 | 39 | 39 | 0.00 | 30 | 920 | 920 | 1.01 | 0.23 | 1.25 | 0.01 | 26.70 | 2 |

### All algorithms

| algorithm | family | cost | cost_range | steps | time_ms | peak_memory_kib | memory_items | effort | found_optimum | complete | optimal_guaranteed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BFS | uninformed | 50 | - | 34 | 2.11 | 380.80 | 2,344 | 2,161 | no | yes | no (fewest steps only) |
| DFS | uninformed | 143 | - | 111 | 0.14 | 33.20 | 153 | 124 | no | yes (finite space, explored set) | no |
| UCS | uninformed | 39 | - | 39 | 2.77 | 371.10 | 2,463 | 2,224 | yes | yes | yes |
| IDS | uninformed | 50 | - | 34 | 633.30 | 19.80 | 69 | 265,249 | no | yes | no (fewest steps only) |
| Greedy (h1) | informed | 82 | - | 54 | 2.51 | 380.30 | 1,380 | 1,294 | no | yes (finite space) | no |
| Greedy (h2) | informed | 50 | - | 34 | 0.19 | 30.60 | 51 | 34 | no | yes (finite space) | no |
| A* (h1) | informed | 39 | - | 39 | 1.19 | 146.80 | 680 | 569 | yes | yes | yes (admissible heuristic) |
| A* (h2) | informed | 39 | - | 39 | 0.30 | 47.50 | 113 | 86 | yes | yes | yes (admissible heuristic) |
| Hill Climbing | local search | 39.10 | [39, 40] | - | 0.26 | 26.70 | 17 | 42.50 | 27/30 runs | yes (every order is a valid plan) | no |
| Simulated Annealing | local search | 39 | [39, 39] | - | 1.41 | 26.70 | 3 | 920 | 30/30 runs | yes (every order is a valid plan) | no |
| Genetic Algorithm | local search | 39 | [39, 39] | - | 4.19 | 32.40 | 61 | 930 | 30/30 runs | yes (every order is a valid plan) | no |
| Hill Climbing (9 restarts) | local search | 39 | [39, 39] | - | 0.44 | 28.30 | 17 | 429.50 | 30/30 runs | yes (every order is a valid plan) | no |
| Random sampling (920 orders) | baseline | 39 | [39, 39] | - | 1.25 | 26.70 | 2 | 920 | 30/30 runs | yes (every order is a valid plan) | no |

## Layout: large

### Search algorithms

| algorithm | path_cost | steps | nodes_generated | nodes_expanded | max_frontier | max_nodes_in_memory | time_ms | time_median_ms | time_mean_ms | time_std_ms | time_runs | peak_memory_kib | cost_optimal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BFS | 38 | 26 | 10,554 | 4,458 | 675 | 5,115 | 4.87 | 5.03 | 5.12 | 0.27 | 20 | 1,187.10 | no |
| DFS | 116 | 80 | 193 | 82 | 29 | 111 | 0.11 | 0.12 | 0.12 | 0.01 | 20 | 27.50 | no |
| UCS | 28 | 28 | 6,685 | 2,841 | 531 | 3,371 | 3.97 | 4.14 | 4.26 | 0.54 | 20 | 585.90 | yes |
| IDS | 38 | 26 | 374,792 | 157,635 | 27 | 53 | 407.45 | 460.18 | 454.48 | 43.32 | 5 | 15.50 | no |
| Greedy (h1) | 31 | 27 | 5,893 | 2,478 | 300 | 2,778 | 6.94 | 8.25 | 9.57 | 3.92 | 20 | 658.00 | no |
| Greedy (h2) | 34 | 26 | 61 | 26 | 17 | 43 | 0.18 | 0.23 | 0.23 | 0.02 | 20 | 25.30 | no |
| A* (h1) | 28 | 28 | 2,492 | 1,051 | 328 | 1,378 | 2.80 | 3.25 | 3.30 | 0.30 | 20 | 345.60 | yes |
| A* (h2) | 28 | 28 | 253 | 108 | 59 | 167 | 0.49 | 0.58 | 0.59 | 0.09 | 20 | 53.70 | yes |

### Local search (30 seeds)

| algorithm | runs | best | mean | worst | std | optimal_runs | mean_evaluations | mean_iterations | run_time_ms | setup_ms | time_ms | time_std_ms | peak_memory_kib | orders_in_memory |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Hill Climbing | 30 | 28 | 29.27 | 33 | 1.55 | 16 | 72.90 | 1.60 | 0.05 | 0.18 | 0.24 | 0.01 | 32.00 | 30 |
| Simulated Annealing | 30 | 28 | 28 | 28 | 0.00 | 30 | 920 | 919 | 1.23 | 0.18 | 1.42 | 0.02 | 26.20 | 3 |
| Genetic Algorithm | 30 | 28 | 28 | 28 | 0.00 | 30 | 930 | 30 | 4.53 | 0.18 | 4.71 | 0.20 | 34.00 | 61 |
| Hill Climbing (9 restarts) | 30 | 28 | 28.07 | 30 | 0.37 | 29 | 752.90 | 16.50 | 0.42 | 0.18 | 0.60 | 0.06 | 32.30 | 30 |
| Random sampling (920 orders) | 30 | 28 | 28 | 28 | 0.00 | 30 | 920 | 920 | 1.25 | 0.18 | 1.44 | 0.03 | 25.80 | 2 |

### All algorithms

| algorithm | family | cost | cost_range | steps | time_ms | peak_memory_kib | memory_items | effort | found_optimum | complete | optimal_guaranteed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BFS | uninformed | 38 | - | 26 | 4.87 | 1,187.10 | 5,115 | 4,458 | no | yes | no (fewest steps only) |
| DFS | uninformed | 116 | - | 80 | 0.11 | 27.50 | 111 | 82 | no | yes (finite space, explored set) | no |
| UCS | uninformed | 28 | - | 28 | 3.97 | 585.90 | 3,371 | 2,841 | yes | yes | yes |
| IDS | uninformed | 38 | - | 26 | 407.45 | 15.50 | 53 | 157,635 | no | yes | no (fewest steps only) |
| Greedy (h1) | informed | 31 | - | 27 | 6.94 | 658.00 | 2,778 | 2,478 | no | yes (finite space) | no |
| Greedy (h2) | informed | 34 | - | 26 | 0.18 | 25.30 | 43 | 26 | no | yes (finite space) | no |
| A* (h1) | informed | 28 | - | 28 | 2.80 | 345.60 | 1,378 | 1,051 | yes | yes | yes (admissible heuristic) |
| A* (h2) | informed | 28 | - | 28 | 0.49 | 53.70 | 167 | 108 | yes | yes | yes (admissible heuristic) |
| Hill Climbing | local search | 29.27 | [28, 33] | - | 0.24 | 32.00 | 30 | 72.90 | 16/30 runs | yes (every order is a valid plan) | no |
| Simulated Annealing | local search | 28 | [28, 28] | - | 1.42 | 26.20 | 3 | 920 | 30/30 runs | yes (every order is a valid plan) | no |
| Genetic Algorithm | local search | 28 | [28, 28] | - | 4.71 | 34.00 | 61 | 930 | 30/30 runs | yes (every order is a valid plan) | no |
| Hill Climbing (9 restarts) | local search | 28.07 | [28, 30] | - | 0.60 | 32.30 | 30 | 752.90 | 29/30 runs | yes (every order is a valid plan) | no |
| Random sampling (920 orders) | baseline | 28 | [28, 28] | - | 1.44 | 25.80 | 2 | 920 | 30/30 runs | yes (every order is a valid plan) | no |

## Larger mazes (10,000 evaluations per run, 20 seeds)

| pellets | free_cells | state_space_upper_bound | pellet_orders | optimal_cost | optimal_steps | astar_h2_nodes_expanded | astar_h2_max_nodes_in_memory | astar_h2_time_ms |
|---|---|---|---|---|---|---|---|---|
| 8 | 129 | 33,024 | 40,320 | 56 | 52 | 260 | 344 | 1.00 |
| 12 | 129 | 528,384 | 479,001,600 | 64 | 60 | 361 | 492 | 1.61 |
| 16 | 129 | 8,454,144 | 20,922,789,888,000 | 76 | 72 | 911 | 1,275 | 4.63 |
| 20 | 129 | 135,266,304 | 2,432,902,008,176,640,000 | 78 | 74 | 1,366 | 1,944 | 8.04 |
| 24 | 129 | 2,164,260,864 | 620,448,401,733,239,439,360,000 | 84 | 80 | 3,241 | 4,660 | 20.90 |

| pellets | method | runs | optimal_cost | best | mean | worst | optimal_runs | mean_evaluations | mean_percent_above_optimum |
|---|---|---|---|---|---|---|---|---|---|
| 8 | Random sampling | 20 | 56 | 56 | 57 | 60 | 12 | 10,000 | 1.80 |
| 8 | Hill Climbing (restarts) | 20 | 56 | 56 | 56 | 56 | 20 | 10,077 | 0.00 |
| 8 | Simulated Annealing | 20 | 56 | 56 | 56 | 56 | 20 | 10,001 | 0.00 |
| 8 | Genetic Algorithm | 20 | 56 | 56 | 56 | 56 | 20 | 10,000 | 0.00 |
| 12 | Random sampling | 20 | 64 | 66 | 72.25 | 77 | 0 | 10,000 | 12.90 |
| 12 | Hill Climbing (restarts) | 20 | 64 | 64 | 65.05 | 68 | 11 | 10,174 | 1.60 |
| 12 | Simulated Annealing | 20 | 64 | 64 | 65.35 | 68 | 7 | 10,001 | 2.10 |
| 12 | Genetic Algorithm | 20 | 64 | 68 | 69.90 | 75 | 0 | 10,000 | 9.20 |
| 16 | Random sampling | 20 | 76 | 85 | 88.65 | 93 | 0 | 10,000 | 16.60 |
| 16 | Hill Climbing (restarts) | 20 | 76 | 76 | 82.25 | 86 | 1 | 10,404 | 8.20 |
| 16 | Simulated Annealing | 20 | 76 | 76 | 81.90 | 85 | 1 | 10,001 | 7.80 |
| 16 | Genetic Algorithm | 20 | 76 | 84 | 85.65 | 87 | 0 | 10,000 | 12.70 |
| 20 | Random sampling | 20 | 78 | 88 | 93.30 | 100 | 0 | 10,000 | 19.60 |
| 20 | Hill Climbing (restarts) | 20 | 78 | 82 | 85.80 | 88 | 0 | 10,451 | 10.00 |
| 20 | Simulated Annealing | 20 | 78 | 78 | 84.70 | 88 | 3 | 10,001 | 8.60 |
| 20 | Genetic Algorithm | 20 | 78 | 85 | 87.45 | 90 | 0 | 10,000 | 12.10 |
| 24 | Random sampling | 20 | 84 | 95 | 105.65 | 115 | 0 | 10,000 | 25.80 |
| 24 | Hill Climbing (restarts) | 20 | 84 | 87 | 93.35 | 99 | 0 | 10,867 | 11.10 |
| 24 | Simulated Annealing | 20 | 84 | 84 | 88.80 | 94 | 3 | 10,001 | 5.70 |
| 24 | Genetic Algorithm | 20 | 84 | 93 | 96.35 | 102 | 0 | 10,000 | 14.70 |
