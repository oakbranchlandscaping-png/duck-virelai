"""PUSH — ladder step 7b, build-plan rung 5. Canon: 03 §10, §11, R4, R-D, R-D.1.

saturated   : Model -> bool   computed every frame; relative to the library's depth
prune / step / certificate / verdict : WIN | EXHAUSTED_NO_WIN | STILL_SEARCHING
Coverage-ordered, never win-proximity-ordered. A failed predict here opens a Friction and
kills nothing. Hidden state (fork / promote / discriminate) is deferred.
"""
