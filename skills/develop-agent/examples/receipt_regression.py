"""Offline regression example. Run with --version faulty or --version fixed."""

import argparse
import unittest
from dataclasses import dataclass, field


@dataclass
class Outbox:
    deliveries: list = field(default_factory=list)

    def send(self, status, receipt_id=None):
        self.deliveries.append((status, receipt_id))


def decide_fixed(receipt, calls_left):
    if receipt is not None:
        return "delivered", receipt
    if calls_left == 0:
        return "unconfirmed", None
    raise ValueError("The example expects the last lookup to have been used")


def decide_faulty(receipt, calls_left):
    if calls_left == 0:
        return "unconfirmed", None
    return decide_fixed(receipt, calls_left)


class TicketQuery:
    def __init__(self, decision, outbox):
        self.decision = decision
        self.outbox = outbox
        self.calls_left = 1
        self.visible_receipt = None
        self.closed = False

    def start(self, lookup):
        self.calls_left -= 1
        lookup("T-4", self.receive)

    def receive(self, receipt):
        if not self.closed:
            self.visible_receipt = receipt

    def deadline(self):
        self.outbox.send(*self.decision(self.visible_receipt, self.calls_left))
        self.closed = True


class ReceiptRegression(unittest.TestCase):
    decision = staticmethod(decide_fixed)

    def exercise(self, arrival_ms, receipt):
        outbox = Outbox()
        query = TicketQuery(self.decision, outbox)
        lookups = []
        results_returned = []
        agenda = [(10, query.deadline)]

        def lookup(ticket, on_result):
            lookups.append(ticket)

            def return_result():
                results_returned.append(receipt)
                on_result(receipt)

            agenda.append((arrival_ms, return_result))

        query.start(lookup)
        delivered_at_deadline = None
        for tick, action in sorted(agenda, key=lambda entry: entry[0]):
            action()
            if tick == 10:
                delivered_at_deadline = list(outbox.deliveries)
        self.assertEqual(lookups, ["T-4"])
        self.assertEqual(results_returned, [receipt])
        self.assertEqual(outbox.deliveries, delivered_at_deadline)
        return delivered_at_deadline

    def test_visible_receipt_is_delivered(self):
        self.assertEqual(self.exercise(3, "R-17"), [("delivered", "R-17")])

    def test_delivery_uses_the_current_receipt(self):
        self.assertEqual(self.exercise(3, "R-83"), [("delivered", "R-83")])

    def test_late_receipt_does_not_reopen_task(self):
        self.assertEqual(self.exercise(12, "R-17"), [("unconfirmed", None)])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=("faulty", "fixed"), default="fixed")
    args = parser.parse_args()
    if args.version == "faulty":
        ReceiptRegression.decision = staticmethod(decide_faulty)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReceiptRegression)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
