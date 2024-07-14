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

from abc import abstractmethod, ABC
from dataclasses import dataclass


class Scale(ABC):
    min: int
    max: int

    @abstractmethod
    def scale(self, value):
        pass


class IECScale(Scale):
    min: int = -70
    max: int = 0

    def scale(self, value):
        """IEC 268-18:1995 standard dB scaling.

        Adapted from: http://plugin.org.uk/meterbridge/
        """
        scale = 100

        if value < -70.0:
            scale = 0.0
        elif value < -60.0:
            scale = (value + 70.0) * 0.25
        elif value < -50.0:
            scale = (value + 60.0) * 0.50 + 5
        elif value < -40.0:
            scale = (value + 50.0) * 0.75 + 7.5
        elif value < -30.0:
            scale = (value + 40.0) * 1.5 + 15
        elif value < -20.0:
            scale = (value + 30.0) * 2.0 + 30
        elif value < 0:
            scale = (value + 20.0) * 2.5 + 50

        return scale / 100


@dataclass
class LinearScale(Scale):
    min: int = -60
    max: int = 0

    def scale(self, value):
        if value < self.min:
            return 0
        elif value < self.max:
            return (value - self.min) / (self.max - self.min)

        return 1
