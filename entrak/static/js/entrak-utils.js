function Utils (){};

Utils.RANGE_TYPE_HOUR	= 'hour';
Utils.RANGE_TYPE_DAY	= 'day';
Utils.RANGE_TYPE_NIGHT	= 'night';
Utils.RANGE_TYPE_WEEK	= 'week';
Utils.RANGE_TYPE_MONTH	= 'month';
Utils.RANGE_TYPE_YEAR	= 'year';

Utils.API_RANGE_TYPES = {
	'hour': 'hour',
	'day': 'day',
	'night': 'day',
	'week': 'week',
	'month': 'month',
	'year': 'year',
};

Utils.UNIT_KWH = -1;

Utils.getNowMoment = function (startOf) {

	// TODO: hardcode now should be change after have real data
	// result = moment();
	result = moment().year(2014).month(5).date(3);
	if (startOf !== undefined) {
		result.startOf(startOf);
	}

	return result;
}

Utils.genStartEndDt = function (targetDt, rangeType) {
	var startDt = null;
	var endDt = null;
	var dtClone = moment(targetDt).startOf('hour');

	if (rangeType === Utils.RANGE_TYPE_HOUR) {
		startDt = dtClone;
		endDt = moment(startDt).add('h', 1);
	} else if (rangeType === Utils.RANGE_TYPE_DAY) {
		startDt = dtClone.startOf('day');
		endDt = moment(startDt).add('d', 1);
	} else if (rangeType == Utils.RANGE_TYPE_NIGHT) {
		if (dtClone.hour() >= 8) {
			startDt = dtClone.subtract('d', 1).hour(20);
		} else {
			startDt = dtClone.subtract('d', 2).hour(20);
		}
		endDt = moment(startDt).add('h', 12);
	} else if (rangeType == Utils.RANGE_TYPE_WEEK) {
		startDt = dtClone.startOf('week');
		endDt = moment(startDt).add('d', 7);
	} else if (rangeType == Utils.RANGE_TYPE_MONTH) {
		startDt = dtClone.startOf('month');
		endDt = moment(startDt).add('M', 1);
	} else if (rangeType == Utils.RANGE_TYPE_YEAR) {
		startDt = dtClone.startOf('year');
		endDt = moment(startDt).add('y', 1);
	}

	return {startDt: startDt, endDt: endDt};
}

Utils.getDtDetlaUnit = function (rangeType) {
	var deltaUnit = null;
	if (rangeType === Utils.RANGE_TYPE_HOUR) {
		deltaUnit = 'h';
	} else if (rangeType === Utils.RANGE_TYPE_DAY || rangeType === Utils.RANGE_TYPE_NIGHT) {
		deltaUnit = 'd';
	} else if (rangeType === Utils.RANGE_TYPE_WEEK) {
		deltaUnit = 'w';
	} else if (rangeType === Utils.RANGE_TYPE_MONTH) {
		deltaUnit = 'M';
	} else if (rangeType === Utils.RANGE_TYPE_YEAR) {
		deltaUnit = 'y';
	}
	return deltaUnit;
}

Utils.genLastStartEndDt = function (targetDt, rangeType) {
	var deltaUnit = null;
	if (rangeType === Utils.RANGE_TYPE_DAY
		|| rangeType === Utils.RANGE_TYPE_NIGHT
		|| rangeType === Utils.RANGE_TYPE_WEEK) {
		deltaUnit = 'w';
	} else if (rangeType === Utils.RANGE_TYPE_MONTH) {
		deltaUnit = 'M';
	} else if (rangeType === Utils.RANGE_TYPE_YEAR) {
		deltaUnit = 'y';
	} else if (rangeType === Utils.RANGE_TYPE_HOUR) {
		deltaUnit = 'h'
	}
	var lastStartDt = moment(targetDt).subtract(deltaUnit, 1);
	var lastEndDt = moment(lastStartDt).add(Utils.getDtDetlaUnit(rangeType), 1);

	return {startDt: lastStartDt, endDt: lastEndDt};
}
