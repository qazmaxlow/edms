import datetime

SOURCE_TZ_HK = u'Asia/Hong_Kong'

CITY_ALL = 'all'

DEFAULT_NIGHT_TIME_START = datetime.time(22)
DEFAULT_NIGHT_TIME_END = datetime.time(7)

CORPORATE = 1
EDUCATION = 2
COMPANY_TYPES = {
    (CORPORATE, 'Corporate'),
    (EDUCATION, 'Education'),
}