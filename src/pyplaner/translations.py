DEFAULT_LANGUAGE: str = "en"

SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "ru", "kr")

WEEKDAY_NAMES: dict[str, tuple[str, ...]] = {
    "en": (
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    ),
    "ru": (
        "Понедельник", "Вторник", "Среда", "Четверг",
        "Пятница", "Суббота", "Воскресенье",
    ),
    "kr": (
        "월요일", "화요일", "수요일", "목요일",
        "금요일", "토요일", "일요일",
    ),
}

WEEKDAY_SHORT_NAMES: dict[str, tuple[str, ...]] = {
    "en": ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
    "ru": ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"),
    "kr": ("월", "화", "수", "목", "금", "토", "일"),
}

WEEKDAY_LETTERS: dict[str, tuple[str, ...]] = {
    "en": ("M", "T", "W", "T", "F", "S", "S"),
    "ru": ("П", "В", "С", "Ч", "П", "С", "В"),
    "kr": ("월", "화", "수", "목", "금", "토", "일"),
}

MONTH_NAMES: dict[str, tuple[str, ...]] = {
    "en": (
        "January", "February", "March", "April",
        "May", "June", "July", "August",
        "September", "October", "November", "December",
    ),
    "ru": (
        "Январь", "Февраль", "Март", "Апрель",
        "Май", "Июнь", "Июль", "Август",
        "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
    ),
    "kr": (
        "1월", "2월", "3월", "4월",
        "5월", "6월", "7월", "8월",
        "9월", "10월", "11월", "12월",
    ),
}

MONTH_SHORT_NAMES: dict[str, tuple[str, ...]] = {
    "en": (
        "Jan", "Feb", "Mar", "Apr",
        "May", "Jun", "Jul", "Aug",
        "Sep", "Oct", "Nov", "Dec",
    ),
    "ru": (
        "Янв", "Фев", "Мар", "Апр",
        "Май", "Июн", "Июл", "Авг",
        "Сен", "Окт", "Ноя", "Дек",
    ),
    "kr": (
        "1월", "2월", "3월", "4월",
        "5월", "6월", "7월", "8월",
        "9월", "10월", "11월", "12월",
    ),
}
