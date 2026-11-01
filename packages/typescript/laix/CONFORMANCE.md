# Canonical attention conformance

- Contract: `laix` v0.7.0
- Cases: **24**
- Decisions compared: **24 / 24**

| case | signal | expected | actual | pass | problems |
|---|---|---|---|---|---|
| critical_at_night_still_reaches_a_human | signal-1 | guide | guide | pass | - |
| high_waits_for_the_digest_at_night | signal-2 | wait | wait | pass | - |
| medium_is_below_the_floor | signal-3 | wait | wait | pass | - |
| low_confidence_is_not_raised | signal-4 | wait | wait | pass | - |
| a_muted_kind_is_silent | signal-5 | wait | wait | pass | - |
| the_same_signal_is_not_repeated_the_same_day | signal-6 | wait | wait | pass | - |
| the_kill_switch_wins_over_everything | signal-7 | wait | wait | pass | - |
| the_interruption_budget_is_a_hard_cap | signal-8a | guide | guide | pass | - |
| the_interruption_budget_is_a_hard_cap | signal-8b | wait | wait | pass | - |
| a_critical_that_stayed_overdue_escalates | signal-9 | escalate | escalate | pass | - |
| quiet_hours_end_is_inclusive | signal-10 | wait | wait | pass | - |
| one_minute_after_quiet_hours_notifies | signal-11 | guide | guide | pass | - |
| learned_adjustment_is_added_to_the_score | signal-12 | guide | guide | pass | - |
| a_snooze_holds_until_it_expires | signal-13 | wait | wait | pass | - |
| an_expired_snooze_releases_the_signal | signal-14 | guide | guide | pass | - |
| a_signal_marked_wrong_never_repeats | signal-15 | wait | wait | pass | - |
| an_assigned_signal_is_someone_elses_job | signal-16 | wait | wait | pass | - |
| a_dismissed_signal_stays_dismissed | signal-17 | wait | wait | pass | - |
| an_accepted_signal_is_not_suppressed | signal-18 | guide | guide | pass | - |
| a_reversible_intent_is_executed_when_act_is_allowed | signal-19 | act | act | pass | - |
| an_action_that_needs_approval_keeps_the_flag | signal-20 | act | act | pass | - |
| an_intent_does_nothing_unless_act_is_allowed | signal-21 | guide | guide | pass | - |
| an_escalation_carries_its_target | signal-22 | escalate | escalate | pass | - |
| no_new_context_behaves_exactly_as_before | signal-23 | guide | guide | pass | - |
