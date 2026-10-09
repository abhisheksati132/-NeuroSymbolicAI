"""
Symbolic Rule and Constraint Engine for Cloud Resource Allocation.
Implements hard safety constraints, SLA guarantees, anti-affinity policies,
and explainable decision logging.
"""
from typing import List, Dict, Any, Tuple, Optional
from src.simulator.host import Host
from src.simulator.task import Task


class RuleEvaluation:
    def __init__(self, rule_id: str, rule_name: str, passed: bool, reason: str, is_hard: bool = True):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.passed = passed
        self.reason = reason
        self.is_hard = is_hard

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "VIOLATED"
        kind = "HARD" if self.is_hard else "SOFT"
        return f"[{self.rule_id}:{kind}] {status} - {self.reason}"


class SymbolicRuleEngine:
    """
    Symbolic engine enforcing datacenter operational policies and emitting
    auditable explanation traces for each allocation evaluation.
    """
    def __init__(
        self,
        max_capacity_threshold: float = 0.85,
        high_priority_headroom_threshold: float = 0.75,
    ):
        self.max_capacity_threshold = max_capacity_threshold
        self.high_priority_headroom_threshold = high_priority_headroom_threshold

    def evaluate_host_candidate(
        self,
        task: Task,
        host: Host,
        forecasted_saturation: bool = False,
    ) -> Tuple[bool, float, List[RuleEvaluation]]:
        """
        Evaluates placing a task on a specific host.
        
        Returns:
            admissible: True if all hard constraints pass.
            preference_score: Scalar score combining soft constraints (higher is better).
            evaluations: List of individual rule evaluation logs.
        """
        evaluations: List[RuleEvaluation] = []
        is_admissible = True
        preference_score = 0.0

        target_cpu = host.cpu_used + task.cpu_req
        target_ram = host.ram_used + task.ram_req
        target_cpu_util = target_cpu / host.cpu_capacity
        target_ram_util = target_ram / host.ram_capacity

        # =========================================================================
        # RULE 1 [HARD]: Capacity Safety Bound (Never exceed 85% CPU / RAM)
        # =========================================================================
        rule_1_pass = (
            target_cpu_util <= self.max_capacity_threshold
            and target_ram_util <= self.max_capacity_threshold
        )
        if rule_1_pass:
            evaluations.append(RuleEvaluation(
                "R1_CAPACITY_BOUND",
                "Host Capacity Safety Threshold",
                True,
                f"Projected util CPU {target_cpu_util*100:.1f}%, RAM {target_ram_util*100:.1f}% <= {self.max_capacity_threshold*100:.0f}%",
                is_hard=True,
            ))
        else:
            evaluations.append(RuleEvaluation(
                "R1_CAPACITY_BOUND",
                "Host Capacity Safety Threshold",
                False,
                f"Exceeds safe bound: projected CPU {target_cpu_util*100:.1f}%, RAM {target_ram_util*100:.1f}% > {self.max_capacity_threshold*100:.0f}%",
                is_hard=True,
            ))
            is_admissible = False

        # =========================================================================
        # RULE 2 [HARD]: High Priority SLA Headroom
        # Priority 3 tasks must be placed on hosts with at least 25% remaining headroom (util <= 75%)
        # =========================================================================
        if task.priority == 3:
            rule_2_pass = (
                target_cpu_util <= self.high_priority_headroom_threshold
                and target_ram_util <= self.high_priority_headroom_threshold
            )
            if rule_2_pass:
                evaluations.append(RuleEvaluation(
                    "R2_SLA_HEADROOM",
                    "High-Priority Headroom Guarantee",
                    True,
                    f"P3 task accommodated with safe headroom: util <= {self.high_priority_headroom_threshold*100:.0f}%",
                    is_hard=True,
                ))
            else:
                evaluations.append(RuleEvaluation(
                    "R2_SLA_HEADROOM",
                    "High-Priority Headroom Guarantee",
                    False,
                    f"P3 task rejected: projected util ({max(target_cpu_util, target_ram_util)*100:.1f}%) violates 25% safety headroom",
                    is_hard=True,
                ))
                is_admissible = False
        else:
            evaluations.append(RuleEvaluation(
                "R2_SLA_HEADROOM",
                "High-Priority Headroom Guarantee",
                True,
                f"Task priority {task.priority} < 3; headroom rule bypassed",
                is_hard=False,
            ))

        # =========================================================================
        # RULE 3 [HARD]: Anti-Affinity Policy
        # Tasks of identical tenant with priority 3 cannot be co-located on the same host
        # =========================================================================
        colocated_same_tenant_p3 = any(
            t.tenant_id == task.tenant_id and t.priority == 3
            for t in host.allocated_tasks.values()
        )
        if task.priority == 3 and colocated_same_tenant_p3:
            evaluations.append(RuleEvaluation(
                "R3_ANTI_AFFINITY",
                "Tenant Failure Domain Isolation",
                False,
                f"Co-location conflict: tenant {task.tenant_id} already has active P3 task on {host.host_id}",
                is_hard=True,
            ))
            is_admissible = False
        else:
            evaluations.append(RuleEvaluation(
                "R3_ANTI_AFFINITY",
                "Tenant Failure Domain Isolation",
                True,
                f"No anti-affinity conflict on {host.host_id} for tenant {task.tenant_id}",
                is_hard=True,
            ))

        # If hard constraints fail, soft evaluation is skipped
        if not is_admissible:
            return False, -1e6, evaluations

        # =========================================================================
        # RULE 4 [SOFT]: Energy Consolidation Preference
        # Prefer packing already active hosts over powering on standby hosts
        # =========================================================================
        if host.is_active:
            # Active host: bonus for packing (utilization fitness)
            fill_ratio = (target_cpu_util + target_ram_util) / 2.0
            consolidation_bonus = 50.0 + fill_ratio * 30.0
            preference_score += consolidation_bonus
            evaluations.append(RuleEvaluation(
                "R4_ENERGY_CONSOLIDATION",
                "Server Consolidation & Standby Avoidance",
                True,
                f"Host is active; packing bonus +{consolidation_bonus:.1f}",
                is_hard=False,
            ))
        else:
            # Host in standby: penalty for powering on
            standby_penalty = -40.0
            preference_score += standby_penalty
            evaluations.append(RuleEvaluation(
                "R4_ENERGY_CONSOLIDATION",
                "Server Consolidation & Standby Avoidance",
                True,
                f"Host currently standby; power-on penalty {standby_penalty:.1f}",
                is_hard=False,
            ))

        # =========================================================================
        # RULE 5 [SOFT]: Flavor Affinity Alignment
        # Match task profile to host specialization
        # =========================================================================
        flavor_bonus = 0.0
        if task.cpu_req >= 8.0 and host.host_type == "CO-4":
            flavor_bonus = 25.0
        elif task.ram_req >= 16.0 and host.host_type == "MO-4":
            flavor_bonus = 25.0
        elif task.cpu_req <= 4.0 and host.host_type == "GP-4":
            flavor_bonus = 15.0
        preference_score += flavor_bonus
        evaluations.append(RuleEvaluation(
            "R5_FLAVOR_AFFINITY",
            "Hardware Flavor Alignment",
            True,
            f"Hardware specialization alignment bonus: +{flavor_bonus:.1f}",
            is_hard=False,
        ))

        # =========================================================================
        # RULE 6 [SOFT/FORECAST]: Proactive Saturation Guard
        # If neural forecaster signals aggregate cluster saturation, reserve high-capacity hosts for P3
        # =========================================================================
        if forecasted_saturation:
            if task.priority < 3 and host.host_type in ["CO-4", "MO-4"]:
                reservation_penalty = -35.0
                preference_score += reservation_penalty
                evaluations.append(RuleEvaluation(
                    "R6_PROACTIVE_GUARD",
                    "Predictive Saturation Headroom Reservation",
                    True,
                    f"Forecast alert: reserving specialized host for P3; penalized lower priority task by {reservation_penalty:.1f}",
                    is_hard=False,
                ))
            elif task.priority == 3 and host.host_type in ["CO-4", "MO-4"]:
                p3_bonus = 30.0
                preference_score += p3_bonus
                evaluations.append(RuleEvaluation(
                    "R6_PROACTIVE_GUARD",
                    "Predictive Saturation Headroom Reservation",
                    True,
                    f"Forecast alert: directing critical P3 task to specialized host bonus +{p3_bonus:.1f}",
                    is_hard=False,
                ))
            else:
                evaluations.append(RuleEvaluation(
                    "R6_PROACTIVE_GUARD",
                    "Predictive Saturation Headroom Reservation",
                    True,
                    "Neutral impact under predictive alert",
                    is_hard=False,
                ))
        else:
            evaluations.append(RuleEvaluation(
                "R6_PROACTIVE_GUARD",
                "Predictive Saturation Headroom Reservation",
                True,
                "Cluster forecast normal; no reservation triggered",
                is_hard=False,
            ))

        return True, preference_score, evaluations
