from random import uniform

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from qdigitalmeter import QDigitalMeter


class Updater(QTimer):
    samples = [-70, -70]
    decaySamples = [-70, -70]
    decayPeakTTL = 8

    def __init__(self, meter: QDigitalMeter, **kwargs):
        super().__init__(**kwargs)
        self.meter = meter

    def newSamples(self):
        self.samples = [
            uniform(-70, 0),
            uniform(-70, 0),
        ]

        for n, sample in enumerate(self.samples):
            if sample >= self.decaySamples[n]:
                self.decayPeakTTL = 8
                self.decaySamples[n] = sample
            elif self.decayPeakTTL <= 0:
                self.decaySamples[n] -= 0.4
            else:
                self.decayPeakTTL -= 1

    def timerEvent(self, event):
        self.newSamples()

        self.meter.plot(self.samples, self.decaySamples)


if __name__ == "__main__":
    app = QApplication([])

    meter = QDigitalMeter()
    meter.setStyleSheet("* { background: rgb(30, 30, 30); color: rgb(90, 90, 90); }")
    meter.resize(150, 400)
    meter.show()

    updater = Updater(meter)
    updater.startTimer(33)

    app.exec()
