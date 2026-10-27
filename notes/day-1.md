### 1. Set up and explore
>>> 0.1 + 0.2 
predicted: 0.3 
actual: 0.30000000000000004 
> Why: 0.1 and 0.2 can’t be stored exactly in binary, so float keeps the nearest value. Adding two approximations makes the error visible.

>>> Decimal("0.1") + Decimal("0.2")
predicted: 0.30000000016
actual: Decimal('0.3')
> Why: String is interpreted as decimal digits inside the Decimal class. It is recommended to use decimal with string input as a decimal form


>>> Decimal(0.1)
predicted: 0.10000000000000001
actual: Decimal('0.1000000000000000055511151231257827021181583404541015625')
> Why: The value inside is a float, is treated like a float data type and the error is copied

### 2. The maths by hand

>>> from decimal import Decimal
>>> 0.1 + 0.2, Decimal("0.1") + Decimal("0.2"), Decimal(0.1)
>>> from loanlab import schedule
>>> s = schedule.calculate(Decimal("20000"), Decimal("0.099"), 24)
>>> s.monthly_payment, s.instalments[0], s.instalments[-1]

- monthly rate: 0.099 / 12 = 0.00825
- interest: 20,000 × 0.00825 = 165.00
- principal: 921.98 − 165.00 = 756.98
- balance: 20,000 − 756.98 = 19,243.02 ✓ matches the schedule

predicted returned value for:
> s.monthly_payment:
Predicted = Decimal('921.98')
Actual = Decimal('921.98')

> s.instalments[0]:
Predicted = (month=1, payment=Decimal('921.98'), interest=Decimal('165.00'), principal=Decimal('756.98'), balance=Decimal('19243.02')
Actual= (month=1, payment=Decimal('921.98'), interest=Decimal('165.00'), principal=Decimal('756.98'), balance=Decimal('19243.02')

> s.instalments[-1]:
Predicted = (month=24, payment=Decimal('921.98'), interest=Decimal('165.00'), principal=Decimal('756.98'), balance=Decimal('0.00')
Actual = (month=24, payment=Decimal('921.88'), interest=Decimal('7.54'), principal=Decimal('914.34'), balance=Decimal('0.00')