# QDigitalMeter

A simple digital peak meter for PyQt

---

Create a meter with default parameters, designed for audio dB values.

```python
from qdigitalmeter import QDigitalMeter

meter = QDigitalMeter()
meter.setStyleSheet("* { background: rgb(30, 30, 30); color: rgb(90, 90, 90); }")
meter.resize(150, 400)
meter.show()
```

Update displayed values:

```python
meter.plot([-42, -42])
```

Optionally display decay indicators:

```python
meter.plot([-42, -42], [-21, -21])
```

See `examples/example_01.py` for a working example