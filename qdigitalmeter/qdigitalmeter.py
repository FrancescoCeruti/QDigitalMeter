# This file is part of Linux Show Player
#
# Copyright 2023 Francesco Ceruti <ceppofrancy@gmail.com>
#
# Linux Show Player is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Linux Show Player is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Linux Show Player.  If not, see <http://www.gnu.org/licenses/>.

from math import ceil
from typing import Iterable

from qtpy.QtCore import QPointF, QRectF, Qt, QPoint
from qtpy.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
    QFontDatabase,
    QFontMetrics,
    QResizeEvent,
    QPaintEvent,
)
from qtpy.QtWidgets import QWidget

from qdigitalmeter.scales import Scale, IECScale


class QDigitalMeter(QWidget):
    """DPM - Digital Peak Meter widget"""

    def __init__(
        self,
        parent=None,
        scale: Scale = IECScale(),
        steps: Iterable[int] = (5, 10, 20, 50),
        smoothing: float = 0.016,
        unit: str = "dBFS",
        **kwargs,
    ):
        """
        :param parent: Parent widget
        :param scale: The algorithm used to normalize the values in the [0-1] range
        :param steps: Incremental steps values at which indicators should be placed
        :param smoothing: Amount of smoothing to apply to decreasing values, 0 to disable
        :param unit: Unit string to draw at the bottom of the indicators
        """

        super().__init__(parent, **kwargs)
        self.valueSmoothing = smoothing
        self.scale = scale
        self.steps = steps
        self.unit = unit

        self.backgroundBrush = None
        self.borderPen = None
        self.clippingPen = None
        self.textPen = None
        self._updateColors()

        self.metersSpacing = 3
        self.minMeterWidth = 10

        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(font.pointSize() - 3)
        self.setFont(font)
        font.setPointSize(font.pointSize() - 1)
        self.unitFont = font

        self.peaks = [self.scale.min, self.scale.min]
        self.decayPeaks = [self.scale.min, self.scale.min]
        self.clipping = {}

        self._currentSmoothing = self.valueSmoothing
        self._meterPixmap = QPixmap()
        self._outerScale = []
        self._outerScaleWidth = self.outerScaleWidth()
        self._canDisplayOuterScale = True
        self._innerScalePixmap = QPixmap()

    def _updateColors(self):
        palette = self.palette()
        self.backgroundBrush = QBrush(palette.window().color())
        self.borderPen = QPen(palette.light().color())
        self.clippingPen = QPen(QColor(220, 50, 50))
        self.textPen = QPen(palette.windowText().color())

    def setStyleSheet(self, stylesheet: str):
        super().setStyleSheet(stylesheet)
        self.style().polish(self)
        self._updateColors()

    def reset(self):
        self.peaks = [self.scale.min] * len(self.peaks)
        self.decayPeaks = [self.scale.min] * len(self.decayPeaks)
        self.clipping = {}

        self.update()

    def metersHeight(self):
        return self.height() - self.borderPen.width()

    def metersCount(self):
        return len(self.peaks)

    def metersWidth(self, forceScale: bool = False):
        metersCount = self.metersCount()
        totalSpacing = self.metersSpacing * (metersCount - 1) + self.borderPen.width()
        outerScaleWidth = self._outerScaleWidth * int(self._canDisplayOuterScale or forceScale)

        return int((self.width() - totalSpacing - outerScaleWidth) / metersCount)

    def outerScaleWidth(self):
        return (
            max(
                QFontMetrics(self.font()).width(str(self.scale.min)),
                QFontMetrics(self.unitFont).boundingRect(self.unit).width(),
            )
            + 4
        )

    def plot(self, peaks: list, decayPeak: list = []):
        peaks = peaks.copy()
        decayPeak = decayPeak.copy()

        # Normalize data and check for clipping
        for n in range(len(peaks)):
            self.clipping[n] = peaks[n] > self.scale.max

            peaks[n] = self.scale.scale(peaks[n])

            if n >= len(decayPeak):
                decayPeak.append(0)
            else:
                decayPeak[n] = self.scale.scale(decayPeak[n])

        # Make transitioning from height to low peaks, smoother
        for n in range(min(len(peaks), len(self.peaks))):
            if self.valueSmoothing:
                if peaks[n] < self.peaks[n]:
                    peaks[n] = self.peaks[n] - self._currentSmoothing
                    self._currentSmoothing *= 1.10
                else:
                    self._currentSmoothing = self.valueSmoothing

        # If the number of "channels" has changed, we need to update the cached pixmaps
        updatePixmaps = len(peaks) != len(self.peaks)

        # Update the meters
        self.peaks = peaks
        self.decayPeaks = decayPeak

        # Update the pixmpas, if needed
        if updatePixmaps:
            self.updateOuterScale()
            self.updateInnerScalePixmap()
            self.updateMeterPixmap()

        # Redraw the widget (queued, and executed in the Qt main-loop)
        self.update(
            0,
            0,
            self.width() - (self._outerScaleWidth if self._canDisplayOuterScale else 0),
            self.height(),
        )

    def updateMeterPixmap(self):
        """Prepare the colored rect to be used during paintEvent(s)"""
        meterWidth = self.metersWidth()
        meterHeight = self.metersHeight()
        dbRange = abs(self.scale.min - self.scale.max)

        gradient = QLinearGradient(0, 0, 0, meterHeight)
        gradient.setColorAt(0, QColor(230, 0, 0))
        gradient.setColorAt(10 / dbRange, QColor(255, 220, 0))
        gradient.setColorAt(30 / dbRange, QColor(0, 220, 0))
        gradient.setColorAt(1, QColor(0, 180, 50))

        self._meterPixmap = QPixmap(meterWidth, meterHeight)
        QPainter(self._meterPixmap).fillRect(0, 0, meterWidth, meterHeight, gradient)

    def updateOuterScale(self):
        self._outerScale = []

        fm = QFontMetrics(self.font())
        height = self.metersHeight()
        # We assume that we're using numerals that lack descenders
        stepMixHeight = fm.ascent() * 1.25
        currLevel = self.scale.max
        currY = 0

        while currY < height - stepMixHeight:
            prevLevel = currLevel
            prevY = currY + stepMixHeight

            for step in self.steps:
                currLevel = prevLevel - step
                currY = height - self.scale.scale(currLevel) * height
                if currY > prevY:
                    break

            if currY < height - stepMixHeight:
                self._outerScale.append([ceil(currY), currLevel])

    def updateInnerScalePixmap(self):
        meterWidth = self.metersWidth()
        innerScaleX = meterWidth - max(meterWidth - meterWidth // 2, self.minMeterWidth)

        self._innerScalePixmap = QPixmap(meterWidth, self.height())
        self._innerScalePixmap.fill(Qt.GlobalColor.transparent)

        if self._innerScalePixmap.isNull():
            return

        painter = QPainter(self._innerScalePixmap)
        painter.setPen(self.borderPen)
        painter.setFont(self.font())

        for mark in self._outerScale:
            painter.drawLine(innerScaleX, mark[0], meterWidth, mark[0])

    def resizeEvent(self, event: QResizeEvent):
        self._canDisplayOuterScale = self.metersWidth(True) >= self.minMeterWidth

        self.updateOuterScale()
        self.updateInnerScalePixmap()
        self.updateMeterPixmap()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter()
        painter.begin(self)
        painter.setPen(self.borderPen)
        painter.setBrush(self.backgroundBrush)

        # Calculate the meter size (per single channel)
        meterRect = QRectF(0, 0, self.metersWidth(), self.metersHeight())
        peakAreaRect = meterRect.adjusted(1, 1, 0, 0)

        # Draw each channel
        for n, (peak, decayPeak) in enumerate(zip(self.peaks, self.decayPeaks)):
            # Scale values to widget size
            peak = peak * peakAreaRect.height()
            decayPeak = decayPeak * peakAreaRect.height()

            # Decide borders colors, depending on the "clipping" state
            if self.clipping.get(n, False):
                painter.setPen(self.clippingPen)
            else:
                painter.setPen(self.borderPen)

            # Draw background and borders
            painter.drawRect(meterRect)

            # Draw peak (audio peak in dB)
            peakRect = QRectF(0, peakAreaRect.bottom() - peak, peakAreaRect.width(), peak)
            painter.drawPixmap(
                peakRect.translated(peakAreaRect.x(), 0),
                self._meterPixmap,
                peakRect,
            )

            # Draw decay indicator
            decayRect = QRectF(
                0,
                peakAreaRect.bottom() - decayPeak,
                peakAreaRect.width(),
                1,
            )
            painter.drawPixmap(
                decayRect.translated(peakAreaRect.x(), 0),
                self._meterPixmap,
                decayRect,
            )

            # Draw inner markings
            painter.drawPixmap(peakAreaRect.topLeft(), self._innerScalePixmap)

            # Move to the next meter
            meterRect.translate(meterRect.width() + self.metersSpacing, 0)
            peakAreaRect.translate(meterRect.width() + self.metersSpacing, 0)

        # Draw the meter scale, when needed
        if self._canDisplayOuterScale and event.region().contains(QPoint(self.width() - self._outerScaleWidth, 0)):
            self.drawScale(painter)

        painter.end()

    def drawScale(self, painter: QPainter):
        # Draw the scale marking text
        x = self.width() - self._outerScaleWidth
        textHeight = QFontMetrics(self.font()).height()
        textOffset = textHeight / 2

        painter.setPen(self.textPen)

        painter.drawText(QPointF(x, 0), str(self.scale.max))
        for mark in self._outerScale:
            painter.drawText(
                QRectF(x, mark[0] - textOffset, self._outerScaleWidth, textHeight),
                Qt.AlignVCenter | Qt.AlignRight,
                str(mark[1]),
            )

        # Draw the units that the scale uses
        painter.setFont(self.unitFont)
        painter.drawText(
            QPointF(x + 2, self.metersHeight()),
            self.unit,
        )
