# QDigitalMeter

A simple digital peak meter for use with PyQt5, PyQt6, PySide2, and PySide6.

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

See `examples/example_01.py` for a working example:

```shell
python3 examples/example_01.py

# or
QT_API=<api> python3 examples/example_01.py
# where <api> = pyqt5 || pyqt6 || pyside2 || pyside6
```

![capture](https://github.com/FrancescoCeruti/QDigitalMeter/assets/5596673/e841f7e4-4f63-42bd-81eb-eda2fc86445f)
