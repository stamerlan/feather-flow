import importlib
import importlib.util
import types
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DayInfo:
    """Supplementary information about a calendar day.

    Every field defaults to ``None`` (no data - fall back to default
    calendar logic). New fields can be added as the framework grows.
    """

    is_off_day: bool | None = None


class DayInfoProvider(ABC):
    """Interface for day-information providers.

    Custom providers: any importable Python module that contains one or more
    classes with a ``fetch_day_info(self, year)`` method can be loaded via
    :meth:`load`. Plugin modules do not need to depend on pyplaner; classes
    are discovered at runtime by duck typing.

    Example standalone plugin (e.g. ``my_holidays.py``)::

        from dataclasses import dataclass

        @dataclass
        class DayInfo:
            is_off_day: bool | None = None

        class MyHolidayProvider:
            def __init__(self, country_code: str) -> None:
                if country_code.upper() != "US":
                    raise ValueError(f"Unsupported: {country_code!r}")

            def fetch_day_info(self, year: int):
                return {
                    f"{year}-12-25": DayInfo(is_off_day=True),
                    f"{year}-01-01": DayInfo(is_off_day=True),
                }

    Usage::

        pyplaner planner.html --provider my_holidays --country us
    """

    @staticmethod
    def load(module_name: str) -> list[type["DayInfoProvider"]]:
        """Import *module_name* and return every provider class found in it.

        Provider classes are discovered by duck typing - they do not have to
        inherit from this class. If the name cannot be imported as an
        installed package, the method falls back to loading a file from disk
        (see :meth:`_load_from_file`).

        :param module_name: Dotted module name **or** a file path (with or
            without extension).
        :returns: List of provider classes found in the module.
        :raises TypeError: If the module contains no provider classes.
        :raises ModuleNotFoundError: If *module_name* cannot be imported and
            no matching file is found on disk.
        :raises ImportError: If a matching file is found but cannot be loaded.
        """
        try:
            mod = importlib.import_module(module_name)
        except ModuleNotFoundError:
            mod = DayInfoProvider._load_from_file(module_name)

        classes = [
            getattr(mod, name) for name in dir(mod)
            if (DayInfoProvider.is_provider_class(getattr(mod, name)))
        ]

        if not classes:
            raise TypeError(
                f"No day information provider class found in {module_name!r}."
            )
        return classes

    _FILE_SUFFIXES = ("", ".py", ".pyc", ".pyd", ".so")

    @staticmethod
    def _load_from_file(module_name: str) -> types.ModuleType:
        """Try to load *module_name* as a file, cycling through known suffixes.

        When *module_name* already has a file extension, only that exact path
        is attempted. Otherwise the method tries the bare name followed by
        each suffix in :attr:`_FILE_SUFFIXES`.

        :param module_name: Bare module name or file path.
        :returns: The loaded module object.
        :raises ModuleNotFoundError: If no file matching *module_name* could
            be found or loaded.
        """
        base = Path(module_name)
        suffixes = (
            (base.suffix,) if base.suffix
            else DayInfoProvider._FILE_SUFFIXES
        )
        last_err: Exception | None = None
        for suffix in suffixes:
            path = base.with_suffix(suffix) if suffix else base
            spec = importlib.util.spec_from_file_location(path.stem, path)
            if spec is None or spec.loader is None:
                last_err = ImportError(f"Cannot load module from {path}")
                continue
            try:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod
            except Exception as exc:
                last_err = exc
        raise ModuleNotFoundError(
            f"No module named {module_name!r} and no matching file found."
        ) from last_err

    @staticmethod
    def is_provider_class(obj: object) -> bool:
        return (
            isinstance(obj, type)
            and callable(getattr(obj, "fetch_day_info", None))
        )

    @abstractmethod
    def __init__(self, country_code: str) -> None:
        """Initialize the provider.

        :param country_code: ISO 3166-1 alpha-2 country code.
        :raises ValueError: If *country_code* is not supported.
        """
        raise NotImplementedError()

    @abstractmethod
    def fetch_day_info(self, year: int) -> dict[str, DayInfo] | None:
        """Return day information keyed by date id (``YYYY-MM-DD``).

        :param year: Calendar year to fetch data for.
        :returns: Mapping of ``YYYY-MM-DD`` strings to :class:`DayInfo`
            instances, or ``None`` when the data source is unreachable or
            the response is unusable. Missing keys are treated as "no extra
            info" (equivalent to ``DayInfo()``).
        """
        raise NotImplementedError()
