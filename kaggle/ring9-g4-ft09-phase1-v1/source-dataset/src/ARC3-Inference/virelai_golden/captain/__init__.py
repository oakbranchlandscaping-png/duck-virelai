"""CAPTAIN — ladder step 7a, build-plan rung 4. Canon: 03 §4, §7, §8. The rung no prior plan owned.

open_questions : Model -> [Question]   per-role subtrees; closed_by_data | closed_by_probe | deferred
select         : [Question] -> Question by yield and rewind cost
press          : Question x Model -> Action  one question, one legal action
probe = press . select . open_questions . integrate
The descent floor: return when presses repeat instead of reveal. No threshold.
"""
