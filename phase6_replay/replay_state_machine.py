#!/usr/bin/env python3
"""
replay_state_machine.py
Application-protocol receiver state machine for replay protection.

Replay rejection is NOT a property of the cipher. It is enforced by receiver
state maintained above the AEAD layer: a monotonic packet-number check with a
sliding window that tolerates in-order, out-of-order, and lost frames while
rejecting duplicates and stale frames. The same state machine is used for every
AEAD configuration (AES-CCM, AES-GCM, ChaCha20-Poly1305); the cipher only
determines whether a frame's tag verifies, after which this logic decides
accept or reject.

States:  START -> ACTIVE (per session).  RESET returns ACTIVE to a cleared window.
Decision for a frame whose tag has ALREADY verified, carrying sequence number s:
  - s == highest_seen and already recorded      -> REJECT (immediate replay)
  - s >  highest_seen                            -> ACCEPT (advance window)
  - highest_seen - W < s <= highest_seen:
        already recorded (bit set)               -> REJECT (duplicate / delayed replay)
        not yet recorded                         -> ACCEPT (in-window out-of-order)
  - s <= highest_seen - W                        -> REJECT (stale / outside window)
A frame whose tag FAILS verification is rejected by the AEAD layer and never
reaches this state machine.

Assumptions (stated, not implied):
  * The sequence number is a per-session monotonic packet counter carried in the
    authenticated header (associated data), so it cannot be altered undetected.
  * Window size W is fixed for the session (default 64).
  * The counter is C-bit (default 32). Wraparound is handled by requiring a
    session reset / rekey before the counter would wrap; within a session no
    wrap occurs. This is stated as a protocol assumption.
  * Clock: delayed-replay classification uses arrival order, not wall-clock time;
    no synchronized clock is assumed. A timestamp field, if present, is advisory.
"""
from dataclasses import dataclass, field

@dataclass
class ReplayWindow:
    window_size: int = 64
    counter_bits: int = 32
    highest_seen: int = -1
    seen: set = field(default_factory=set)   # sequence numbers recorded within the window
    accepted: int = 0
    rejected: int = 0
    reject_reasons: dict = field(default_factory=lambda: {
        "immediate_replay":0,"delayed_replay":0,"stale_outside_window":0,"duplicate":0})

    def reset(self):
        """Session reset / rekey: clear replay state (START -> ACTIVE cleared)."""
        self.highest_seen = -1
        self.seen.clear()

    def _mask(self, s):  # wraparound guard within the counter space
        return s % (1 << self.counter_bits)

    def check(self, seq):
        """Decide accept/reject for a tag-verified frame with sequence number seq.
        Returns (accepted: bool, reason: str)."""
        s = self._mask(seq)
        if s > self.highest_seen:
            # advance: drop anything that falls out of the new window
            self.highest_seen = s
            self.seen = {x for x in self.seen if x > s - self.window_size}
            self.seen.add(s)
            self.accepted += 1
            return True, "accepted_new"
        if s <= self.highest_seen - self.window_size:
            self.rejected += 1; self.reject_reasons["stale_outside_window"] += 1
            return False, "stale_outside_window"
        # within window
        if s in self.seen:
            self.rejected += 1
            reason = "immediate_replay" if s == self.highest_seen else "delayed_replay"
            self.reject_reasons[reason] += 1
            return False, reason
        self.seen.add(s)
        self.accepted += 1
        return True, "accepted_in_window"
