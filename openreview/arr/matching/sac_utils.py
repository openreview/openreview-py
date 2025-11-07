from collections import defaultdict, Counter
from dataclasses import dataclass
import logging
import math
from heapq import heappush, heappop
from typing import Dict, List, Tuple, Set, Mapping, Optional

logger = logging.getLogger(__name__)

class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

def multiple_sac_tracks_to_single_track(
    sac_candidates: dict[str, list[str]],
    track_counts: dict[str, int],
) -> dict[str, str]:
    """
    Greedy scarcity‑first assignment of ONE primary track per SAC.
    Returns: primary_track[SAC] = track
    """

    # ------------------------------------------------------------------
    # helper maps
    track_to_sacs = defaultdict(set)
    for s, cand in sac_candidates.items():
        for t in cand:
            track_to_sacs[t].add(s)

    assigned_track  : dict[str, str] = {}     # final answer
    assigned_sacs   = set()                   # fast lookup
    sac_options     = {s: set(cand) for s, cand in sac_candidates.items()}
    sac_degree      = {s: len(cand) for s, cand in sac_candidates.items()}
    sacs_left       = set(sac_candidates)

    # ------------------------------------------------------------------
    # 0. forced assignments (degree‑1 SACs)
    forced = [s for s, d in sac_degree.items() if d == 1]
    for s in forced:
        t = next(iter(sac_options[s]))
        assigned_track[s] = t
        assigned_sacs.add(s)
        sacs_left.remove(s)

    # keep counts of how many SACs already on each track
    sac_count = Counter(assigned_track.values())

    # ------------------------------------------------------------------
    # 1. build scarcity heap  (max‑heap ⇒ negate key for heapq)
    def scarcity_key(t):
        elig = len(track_to_sacs[t])
        # protect division‑by‑zero if ever no candidates (shouldn't happen)
        return -(track_counts[t] / max(elig, 1))

    heap = []
    for t in track_counts:
        heappush(heap, (scarcity_key(t), t))

    # ------------------------------------------------------------------
    # 2. main loop
    while sacs_left:
        _, t = heappop(heap)

        # pick the "best" SAC for this track ---------------------------
        candidates = [
            s for s in track_to_sacs[t] if s in sacs_left  # still free
        ]
        if not candidates:
            continue  # no free SAC can take this track -> try next

        # heuristic choice: fewest remaining options *after* taking t
        s_best = min(
            candidates,
            key=lambda s: (sac_degree[s], len(sac_options[s] - {t}))
        )

        # assign -------------------------------------------------------
        assigned_track[s_best] = t
        assigned_sacs.add(s_best)
        sacs_left.remove(s_best)
        sac_count[t] += 1

        # update scarcity of all tracks that still need SACs ----------
        for t2 in sac_options[s_best]:
            if t2 in track_counts:
                heappush(heap, (scarcity_key(t2), t2))

    # ------------------------------------------------------------------
    # 3. optional single‑swap improvement pass
    loads = {
        s: track_counts[assigned_track[s]] / sac_count[assigned_track[s]]
        for s in assigned_track
    }
    improved = True
    while improved:
        improved = False
        s_list = list(assigned_track.keys())
        for i in range(len(s_list)):
            for j in range(i + 1, len(s_list)):
                si, sj = s_list[i], s_list[j]
                ti, tj = assigned_track[si], assigned_track[sj]
                if tj not in sac_candidates[si] or ti not in sac_candidates[sj]:
                    continue  # swap not legal
                if ti == tj:
                    continue
                # loads after swap
                li_new = track_counts[tj] / sac_count[tj]
                lj_new = track_counts[ti] / sac_count[ti]
                l_old  = [loads[si], loads[sj]]
                l_new  = [li_new, lj_new]
                rng_old = max(l_old) - min(l_old)
                rng_new = max(l_new) - min(l_new)
                if rng_new < rng_old:
                    # do swap
                    assigned_track[si], assigned_track[sj] = tj, ti
                    loads[si], loads[sj] = li_new, lj_new
                    improved = True
        # if any swap happened, recompute sac_count & loads globally
        if improved:
            sac_count = Counter(assigned_track.values())
            loads = {
                s: track_counts[assigned_track[s]] / sac_count[assigned_track[s]]
                for s in assigned_track
            }

    return assigned_track


# ----------------------------------------------------------------------------
# Priority Track SAC Load Planner
# ----------------------------------------------------------------------------

@dataclass
class SACLoadPlan:
    per_sac_track_paper_targets: Dict[str, Dict[str, int]]
    per_sac_total_papers: Dict[str, int]
    volunteered_tracks: Dict[str, Set[str]]
    iterations: int
    stopped: str


def compute_priority_track_load_plan(
    sac_ids: List[str],
    papers_by_track: Dict[str, int],
    sac_priority_tracks: Dict[str, List[str]],
    sac_allowed_tracks: Dict[str, List[str]],
    *,
    small_track_min_papers: int = 10,
    small_track_percent_of_median: float = 0.2,
) -> SACLoadPlan:
    """
    Compute per-SAC paper targets using priority tracks only, then iteratively
    rebalance by re-splitting whole tracks across their current participants
    plus the smallest-load SAC (as a volunteer), skipping small tracks.

    - Range objective: minimize (max_total - min_total)
    - Small tracks: papers < max(min_papers, ceil(alpha * median(track_papers)))
    - Deterministic equal splits and tie-breaking
    - Only the chosen track's shares are changed on each iteration

    Returns a SACLoadPlan with per-track targets and volunteered track state.
    """

    print(
        "Starting compute_priority_track_load_plan: "
        f"sacs={len(sac_ids)} tracks={len(papers_by_track)} "
        f"small_track_min={small_track_min_papers} "
        f"small_track_percent={small_track_percent_of_median:.3f}"
    )

    # Eligibility by priority (seed only)
    eligible: Dict[str, List[str]] = {
        t: [s for s in sac_ids if t in sac_priority_tracks.get(s, [])]
        for t in papers_by_track
    }
    track_paper_totals = dict(papers_by_track)

    # Baseline equal allocation per track (priority-only participants)
    paper_shares: Dict[str, Dict[str, int]] = {s: {} for s in sac_ids}
    for t, sacs in eligible.items():
        if not sacs:
            print(f"Track {t} skipped during seeding: no priority SACs")
            continue  # by assumption there is at least one, but guard anyway
        n = len(sacs)
        total = track_paper_totals[t]
        base, rem = divmod(total, n)
        for s in sacs:
            paper_shares[s][t] = base
        for s in sorted(sacs)[:rem]:  # deterministic remainder
            paper_shares[s][t] += 1

    totals: Dict[str, int] = {s: sum(paper_shares[s].values()) for s in sac_ids}
    print(f"Initial per-SAC totals (priority-only): {totals}")

    # Percent-of-median small-track threshold with absolute floor
    vals = sorted(track_paper_totals.values())
    if vals:
        mid = len(vals) // 2
        median_p = vals[mid] if len(vals) % 2 == 1 else (vals[mid - 1] + vals[mid]) / 2
    else:
        median_p = 0
    threshold = max(small_track_min_papers, int(math.ceil(small_track_percent_of_median * median_p)))
    print(
        f"Computed small-track threshold={threshold} "
        f"(median={median_p:.2f}, min_papers={small_track_min_papers})"
    )

    def objective(totals_dict: Dict[str, int]) -> int:
        loads = list(totals_dict.values())
        return (max(loads) - min(loads)) if loads else 0

    iterations = 0
    current_range = objective(totals)
    print(f"Initial load range={current_range}")
    max_iter = 10_000
    stop_reason = 'max_iterations'
    volunteered_tracks: Dict[str, Set[str]] = {s: set() for s in sac_ids}

    # Main loop: each iteration runs through all eligible SACs once
    while iterations < max_iter:
        iterations += 1
        # Consider SACs that have multiple allowed tracks (eligible to volunteer)
        candidates = [s for s in sac_ids if len(sac_allowed_tracks.get(s, [])) >= 2]
        if not candidates:
            print(
                f"Iteration {iterations}: stopping - no SACs with multiple allowed tracks available to volunteer"
            )
            stop_reason = 'no_candidates'
            break

        print(f"Iteration {iterations}: evaluating {len(candidates)} candidate(s)")
        improved_in_iteration = False

        # Iterate over SACs in ascending load order, recomputing loads per pass
        ordered_candidates = sorted(candidates, key=lambda s: totals.get(s, 0))
        for u in ordered_candidates:
            current_range = objective(totals)
            print(
                f"Iteration {iterations}: evaluating volunteer candidate {u} "
                f"(current total={totals.get(u, 0)}, range={current_range})"
            )
            best_action = None
            best_delta = 0

            for t in track_paper_totals.keys():
                # volunteer only into SAC's normal (allowed) tracks
                if t not in set(sac_allowed_tracks.get(u, [])):
                    continue
                if track_paper_totals[t] < threshold:
                    print(
                        f"Iteration {iterations}: track {t} skipped - "
                        f"papers={track_paper_totals[t]} below threshold={threshold}"
                    )
                    continue  # small track

                donors = [d for d in sac_ids if paper_shares.get(d, {}).get(t, 0) > 0]
                if not donors or u in donors:
                    if not donors:
                        print(f"Iteration {iterations}: track {t} skipped - no existing donors")
                    else:
                        print(
                            f"Iteration {iterations}: track {t} skipped - {u} already participates"
                        )
                    continue

                # Rebalance t equally across donors + u
                new_participants = sorted(set(donors) | {u})
                total = track_paper_totals[t]
                base, rem = divmod(total, len(new_participants))

                sim_totals = totals.copy()
                sim_shares: Dict[str, Dict[str, int]] = {s: dict(paper_shares.get(s, {})) for s in sac_ids}

                # reset track t shares for all participants
                for s in new_participants:
                    sim_shares.setdefault(s, {})[t] = base
                for s in new_participants[:rem]:  # deterministic: already sorted
                    sim_shares[s][t] += 1

                affected = set(donors) | {u}
                for s in affected:
                    old = paper_shares.get(s, {}).get(t, 0)
                    new = sim_shares.get(s, {}).get(t, 0)
                    if new != old:
                        sim_totals[s] = totals.get(s, 0) - old + new

                score = objective(sim_totals)
                delta = current_range - score
                if delta > best_delta:
                    best_delta = delta
                    best_action = (t, sim_totals, sim_shares, True)  # True => u volunteered
                    print(
                        f"Iteration {iterations}: volunteering {u} into track {t} improves range "
                        f"{current_range} -> {score}"
                    )

            if best_action is None:
                print(f"Iteration {iterations}: no improving track found for volunteer {u}")
                continue

            t, totals, paper_shares, is_volunteer = best_action
            new_range = objective(totals)
            print(
                f"Iteration {iterations}: applying volunteer move {u} -> track {t}; "
                f"range {current_range} -> {new_range}"
            )
            current_range = new_range
            improved_in_iteration = True
            if is_volunteer:
                volunteered_tracks[u].add(t)
                print(
                    f"Iteration {iterations}: {u} now volunteering on track {t} "
                    f"(total volunteered tracks={len(volunteered_tracks[u])})"
                )

        if not improved_in_iteration:
            print(f"Iteration {iterations}: stopping - no improving moves found")
            stop_reason = 'no_improvement'
            break
    else:
        stop_reason = 'max_iterations'

    print(
        "Finished compute_priority_track_load_plan after "
        f"{iterations} iteration(s); stop_reason={stop_reason}; final range={objective(totals)}"
    )

    return SACLoadPlan(
        per_sac_track_paper_targets=paper_shares,
        per_sac_total_papers=totals,
        volunteered_tracks=volunteered_tracks,
        iterations=iterations,
        stopped=stop_reason,
    )


def merge_sac_tracks_with_volunteers(
    base_tracks: Dict[str, List[str]],
    volunteered_tracks: Dict[str, Set[str]] | Dict[str, List[str]],
) -> Dict[str, List[str]]:
    """
    Return a copy of `base_tracks` where each SAC's track list is extended
    with any volunteered tracks (if not already present).

    Inputs:
    - base_tracks: {sac: [track, ...]}
    - volunteered_tracks: {sac: set|list(track)}
    """
    merged: Dict[str, List[str]] = {s: list(ts) for s, ts in base_tracks.items()}
    for sac, vol in (volunteered_tracks or {}).items():
        if vol is None:
            continue
        if isinstance(vol, set):
            vol_list = sorted(vol)
        else:
            vol_list = list(vol)
        merged.setdefault(sac, [])
        for t in vol_list:
            if t not in merged[sac]:
                merged[sac].append(t)
    return merged

def calculate_disparity_after_merge(comp_a, comp_b, comp_tracks, comp_sacs, 
                                   track_counts, sac_to_track):
    """Calculate what disparity would be if we merged comp_a and comp_b"""
    # Create temporary merged state
    merged_sacs = comp_sacs[comp_a] | comp_sacs[comp_b]
    merged_tracks = comp_tracks[comp_a] | comp_tracks[comp_b]
    merged_submissions = sum(track_counts[t] for t in merged_tracks)
    merged_load = merged_submissions / max(len(merged_sacs), 1)
    
    # Calculate loads for all components in the new state
    new_loads = []
    for comp_id in comp_tracks:
        if comp_id == comp_a or comp_id == comp_b:
            new_loads.append(merged_load)
        else:
            tracks = comp_tracks[comp_id]
            sacs = comp_sacs[comp_id]
            load = sum(track_counts[t] for t in tracks) / max(len(sacs), 1)
            new_loads.append(load)
    
    # Calculate new disparity
    if not new_loads:
        return 0
    max_load = max(new_loads)
    min_load = min(new_loads)
    return (max_load - min_load) / max(max_load, 1)

def calculate_merge_score(current_disparity, new_disparity, track_a, neighbor, track_fallback):
    """Calculate weighted score for a merge based on disparity improvement and semantic distance"""
    # Disparity improvement (0-1 scale, higher is better)
    disparity_improvement = max(0, current_disparity - new_disparity) / max(current_disparity, 1)
    
    # Semantic distance (0-1 scale, lower is better based on position in track_fallback list)
    semantic_distance = 1.0  # Default to worst case
    fallback_list = track_fallback.get(track_a, [])
    if neighbor in fallback_list:
        # Position 0 gets distance 0 (best), normalize by list length
        position = fallback_list.index(neighbor)
        semantic_distance = position / max(len(fallback_list) - 1, 1)
    
    # Weighted score: 0.5 weight for each parameter
    # Higher disparity improvement is better (higher score)
    # Lower semantic distance is better (so we use 1 - semantic_distance)
    score = 0.5 * disparity_improvement + 0.5 * (1 - semantic_distance)
    
    return score

def rebalance_sacs_across_tracks(
    sac_to_track: Dict[str, str],
    track_counts: Dict[str, int],
    track_fallback: Dict[str, List[str]],
    threshold: float,
) -> Tuple[Dict[str, List[str]], Dict[str, int], Dict[str, List[str]]]:

    uf = UnionFind()
    track_graph: Dict[str, List[str]] = defaultdict(list)

    # main loop --------------------------------------------------------------
    while True:
        # 1. group all tracks into components
        comp_tracks: Dict[str, Set[str]] = defaultdict(set)
        comp_sacs:   Dict[str, Set[str]] = defaultdict(set)
        for track in track_counts:
            comp_tracks[uf.find(track)].add(track)
        for sac, track in sac_to_track.items():
            comp_sacs[uf.find(track)].add(sac)

        # 2. compute SAC loads and global disparity
        sac_load: Dict[str, float] = {}
        for comp_id, tracks in comp_tracks.items():
            load_per_sac = (
                sum(track_counts[t] for t in tracks) / max(len(comp_sacs[comp_id]), 1)
            )
            for sac in comp_sacs[comp_id]:
                sac_load[sac] = load_per_sac
        #print num of tracks per comp
        print({comp_id: len(tracks) for comp_id, tracks in comp_tracks.items()})

        if not sac_load:           # no SACs? exit early
            print("break: no SACs")
            break
        max_load = max(sac_load.values())
        min_load = min(sac_load.values())
        disparity = (max_load - min_load) / max(max_load, 1)
        print(f"max_load: {max_load} min_load: {min_load} disparity: {disparity} threshold: {threshold}")
        if disparity <= threshold:
            print(f"break: disparity({disparity}) <= threshold({threshold})")
            break  # finished!

        # 3. Evaluate all possible merges with weighted scoring
        best_merge = None
        best_score = -1  # Initialize to impossible score
        best_merge_info = None

        for comp_a in comp_tracks.keys():
            tracks_a = comp_tracks[comp_a]
            for track_a in tracks_a:
                for neighbor in track_fallback.get(track_a, []):
                    comp_b = uf.find(neighbor)
                    if comp_a == comp_b:
                        continue
                        
                    new_disparity = calculate_disparity_after_merge(
                        comp_a, comp_b, comp_tracks, comp_sacs, 
                        track_counts, sac_to_track
                    )
                    
                    # Calculate weighted score
                    score = calculate_merge_score(
                        disparity, new_disparity, track_a, neighbor, track_fallback
                    )
                    
                    if score > best_score:
                        best_score = score
                        best_merge = (track_a, neighbor)
                        best_merge_info = (comp_a, comp_b, new_disparity, score)

        # 4. Execute best merge if score indicates meaningful improvement
        if best_merge and best_score > 0.1:  # Only proceed if score indicates meaningful improvement
            track_a, neighbor = best_merge
            comp_a, comp_b, new_disp, score = best_merge_info
            
            track_graph[track_a].append(neighbor)
            uf.union(track_a, neighbor)
            
            print(f"Merged {track_a} and {neighbor} "
                  f"(disparity: {disparity:.3f} -> {new_disp:.3f}, score: {score:.3f})")
        else:
            print(f"break: no beneficial merge found (best score: {best_score:.3f})")
            break

    # final outputs ----------------------------------------------------------
    # sac_to_tracks
    sac_to_tracks: Dict[str, List[str]] = {}
    for sac, primary in sac_to_track.items():
        comp_id = uf.find(primary)
        sac_to_tracks[sac] = list(comp_tracks[comp_id])

    # sac_to_load (cast to int to match your signature)
    sac_to_load_int: Dict[str, int] = {s: int(round(l)) for s, l in sac_load.items()}

    return sac_to_tracks, sac_to_load_int, dict(track_graph)

def assign_acs_to_sac(
    ac_tracks: dict[str, list[str]],
    sac_tracks: dict[str, list[str]],
    original_sac_tracks: dict[str, list[str]],
    track_graph: dict[str, list[str]],
    track_counts: dict[str, int],
    ac_asms: dict[str, list[str]],
    sac_cois: dict[str, list[str]],
    sac_max_loads: Optional[Mapping[str, int]] = None,
) -> dict[str, list[str]]:
    """
    Return: {sac_id: [ac_id, …]}
    """

    # 1. Flatten AC → single-track mapping and invert it
    track_to_acs: dict[str, list[str]] = defaultdict(list)
    unassigned_acs: list[str] = []  # Track ACs without valid tracks
    
    # Find all ACs with assignments but no valid tracks
    acs_with_assignments = set(ac_asms.keys())
    acs_with_valid_tracks = set()
    
    for ac, tracks in ac_tracks.items():
        if ac not in ac_asms:
            print(f"AC {ac} has no asms")
            continue    # AC is not assigned any papers
        if not tracks:
            print(f"AC {ac} has no tracks")
            unassigned_acs.append(ac)  # Collect trackless ACs
            continue
        # AC has both assignments and tracks
        acs_with_valid_tracks.add(ac)
        track_to_acs[tracks[0]].append(ac)
    
    # Find ACs with assignments but missing from ac_tracks entirely
    acs_missing_from_tracks = acs_with_assignments - acs_with_valid_tracks - set(unassigned_acs)
    for ac in acs_missing_from_tracks:
        print(f"AC {ac} missing from ac_tracks entirely")
        unassigned_acs.append(ac)

    # 2. Cache SAC membership by track
    track_to_sacs: dict[str, list[str]] = defaultdict(list)
    all_sacs: set[str] = set()  # Track all SACs
    
    for sac, tracks in sac_tracks.items():
        all_sacs.add(sac)
        for t in tracks:
            track_to_sacs[t].append(sac)

    # 3. Set-up counters we update on the fly
    sac_load: defaultdict[str, int] = defaultdict(int)   # running #submissions
    sac_ac_count: defaultdict[str, int] = defaultdict(int)  # track AC count
    sac_ac:   defaultdict[str, list[str]] = defaultdict(list)
    sac_load_caps = sac_max_loads or {}

    def has_capacity(sac_id: str, load_to_add: int) -> bool:
        cap = sac_load_caps.get(sac_id)
        if cap is None:
            return True
        return sac_load[sac_id] + load_to_add <= cap

    # 4. Process tracks from smallest → largest
    for track in sorted(track_counts.keys(), key=track_counts.get):
        sacs_here = track_to_sacs.get(track, [])
        print(f"processing track {track} with {len(sacs_here)} SACs")
        if not sacs_here:
            # Collect ACs from tracks without SACs
            unassigned_acs.extend(track_to_acs.get(track, []))
            print(f"  No SACs for track {track}, {len(track_to_acs.get(track, []))} ACs moved to unassigned")
            continue

        if track in track_graph:
            print(f"{track} was merged into {track_graph[track]}, assigning to original SACs")
            local_sacs = []
            for sac in sacs_here:
                if sac in original_sac_tracks and track in original_sac_tracks[sac]:
                    local_sacs.append(sac)
            sacs_here = local_sacs
            
        print(f"track {track} has {len(track_to_acs.get(track, []))} ACs")
        for ac in track_to_acs.get(track, []):
            # Pre-compute the conflict count for this AC against every candidate SAC
            asms_set = set(ac_asms.get(ac, []))
            load_increment = len(asms_set)
            eligible_sacs = [
                sac for sac in sacs_here if has_capacity(sac, load_increment)
            ]
            if not eligible_sacs:
                print(f"  No capacity for AC {ac} on track {track}, deferring")
                unassigned_acs.append(ac)
                continue
            best_sac = min(
                eligible_sacs,
                key=lambda sac: (
                    len(asms_set & set(sac_cois.get(sac, []))),  # (a) fewest conflicts
                    sac_load[sac]                               # (b) lightest current load
                )
            )
            # Commit the assignment
            sac_ac[best_sac].append(ac)
            sac_load[best_sac] += len(asms_set)
            sac_ac_count[best_sac] += 1

            # Log loads
            #local_loads = [sac_load[sac] for sac in sacs_here]
            #print(local_loads)

    # 5. Distribute unassigned ACs across all SACs
    if unassigned_acs:
        print(f"\n=== Distributing {len(unassigned_acs)} unassigned ACs ===")
        
        # Sort unassigned ACs by their load (descending) to assign heavy ACs first
        unassigned_acs.sort(key=lambda ac: len(ac_asms.get(ac, [])), reverse=True)
        
        for ac in unassigned_acs:
            asms_set = set(ac_asms.get(ac, []))
            
            # Compute conflict count for all SACs
            sac_conflicts = {
                sac: len(asms_set & set(sac_cois.get(sac, [])))
                for sac in all_sacs
            }
            
            # Find minimum conflict count
            min_conflicts = min(sac_conflicts.values()) if sac_conflicts else 0
            
            # Get SACs with minimum conflicts
            min_conflict_sacs = [
                sac for sac, conflicts in sac_conflicts.items() 
                if conflicts == min_conflicts
            ]
            
            eligible_sacs = [
                sac for sac in min_conflict_sacs if has_capacity(sac, len(asms_set))
            ]
            if not eligible_sacs:
                print(f"  All SACs at capacity for AC {ac}; assigning ignoring cap")
                eligible_sacs = min_conflict_sacs

            # Among SACs with min conflicts, choose the one with lowest load
            best_sac = min(
                eligible_sacs,
                key=lambda sac: (sac_load[sac], sac_ac_count[sac])  # Consider both paper load and AC count
            )
            
            # Assign
            sac_ac[best_sac].append(ac)
            sac_load[best_sac] += len(asms_set)
            sac_ac_count[best_sac] += 1
            
            print(f"  Assigned AC {ac} ({len(asms_set)} papers) to SAC {best_sac} "
                  f"(conflicts={min_conflicts}, new_load={sac_load[best_sac]})")
    
    # 6. Final disparity check
    if sac_load:
        max_load = max(sac_load.values())
        min_load = min(sac_load.values())
        disparity = (max_load - min_load) / max(max_load, 1)
        print(f"\nFinal SAC loads: max={max_load}, min={min_load}, disparity={disparity:.3f}")
        print(f"SAC AC counts: {dict(sac_ac_count)}")

    return dict(sac_ac)
