# P04 · Hotel booking after the refactoring (Python)

Extract the ZIP and open a terminal in the extracted folder. The project is the finished
P04 app: the booking rules sit behind two interfaces, and Python runs its 8 tests.

```text
python -m unittest -v
python main.py
python main.py --race
```

Step2/ holds the Step 2 tests, written against the P03 program, for anyone who missed that
step. They describe what P03 did, and they still pass after the refactoring.

The demo prints exactly the same lines as P03:

```text
Free rooms 12-14 Nov: R7, R8
Maya books R7 12-14 Nov: Accepted R101
Omar books R7 13-15 Nov: Unavailable
Nora books R7 14-16 Nov: Accepted R102
Omar books R8 15-15 Nov: InvalidDates
Free rooms 12-14 Nov: R8
Maya cancels R101: True
Free rooms 12-14 Nov: R7, R8
Confirmation emails sent: 2
```

The race demo still double-books R7, because refactoring changes the structure, not the behaviour:

```text
Maya and Omar both book R7 for 12-14 Nov at the same moment...
Maya: Accepted R101
Omar: Accepted R102
Confirmed reservations for R7 on 12-14 Nov: 2
Double booking! Both requests checked before either one saved.
```

All 8 tests pass.
