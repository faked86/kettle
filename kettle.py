import time
from dataclasses import dataclass
from enum import Enum

from settings import config


class KettleStatus(Enum):
    ON = "on"
    OFF = "off"
    READY = "ready"
    STOPPED = "stopped"


@dataclass
class KettleCondition:
    status: KettleStatus
    temperature: float


class KettleFillingError(Exception):
    """Water filling related error."""


class KettleSwitchError(Exception):
    """Switch related error."""


class KettlePouringError(Exception):
    """Water pouring out related error."""


class Kettle:
    """Class representing real world kettle."""

    def __init__(self) -> None:
        self.volume = .0
        self.min_volume = float(config["DEFAULT"]["MIN_VOLUME"])
        self.max_volume = float(config["DEFAULT"]["MAX_VOLUME"])

        self.start_temperature = float(config["DEFAULT"]["START_TEMPERATURE"])
        self.max_temperature = float(config["DEFAULT"]["MAX_TEMPERATURE"])
        self.temperature = self.start_temperature

        self.boiling_time = float(config["DEFAULT"]["BOILING_TIME_SECONDS"])

        self.status = KettleStatus.OFF

    def fill_in(self, volume: float) -> None:
        """Fill kettle with `volume` of water."""
        if volume < 0:
            raise KettleFillingError("Water volume can't be negative.")
        if volume > self.max_volume:
            raise KettleFillingError("Max volume exeeded.")
        self.volume = volume

    def pour_out(self) -> float:
        """Pour out all water from kettle."""
        if self.status == KettleStatus.ON:
            raise KettlePouringError(
                "You can't pour out from working kettle. Stop it first.")
        volume = self.volume
        self.volume = .0
        self.status = KettleStatus.OFF
        return volume

    def switch(self) -> None:
        """Switch kettle on/off."""
        if self.status == KettleStatus.OFF:
            self._start()
            return
        if self.status == KettleStatus.ON:
            self._stop()
            return
        raise KettleSwitchError("Pour out old water and fill in new.")

    def _start(self) -> None:
        """
        Switch kettle on.

        If volume is under minimum level shuts off.
        """
        if self.volume < self.min_volume:
            raise KettleSwitchError("Can't start kettle: water level too low.")
        self.start_time = time.time()
        self.status = KettleStatus.ON

    def _stop(self) -> None:
        self.status = KettleStatus.STOPPED

    def _update_temperature(self) -> None:
        if self.status != KettleStatus.ON:
            return
        time_since_start = time.time() - self.start_time
        if time_since_start >= self.boiling_time:
            self.temperature = self.max_temperature
            self.status = KettleStatus.READY
            return
        self.temperature = (self.max_temperature - self.start_temperature) * (
            time_since_start / self.boiling_time)

    def check_condition(self) -> KettleCondition:
        self._update_temperature()
        condition = KettleCondition(status=self.status,
                                    temperature=self.temperature)
        return condition


def main() -> None:
    kettle = Kettle()

    while True:
        try:
            volume = float(
                input(
                    f"How much water to fill (from 0 to {kettle.max_volume}): "
                ))
            kettle.fill_in(volume)
            kettle.switch()
        except Exception as err:
            print(err)
            continue
        break

    current_status = kettle.check_condition().status
    while current_status == KettleStatus.ON:
        condition = kettle.check_condition()
        print("Current temperature: ", condition.temperature)
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            kettle.switch()
        finally:
            if condition.status != current_status:
                print("Status changed: ", condition.status)
                current_status = condition.status
            if condition.status != KettleStatus.ON:
                break


if __name__ == "__main__":
    main()
