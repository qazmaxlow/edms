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

Utils.UNIT_KWH = 'kwh';

Utils.getNowMoment = function (startOf) {

	// TODO: hardcode now should be change after have real data
	result = moment();
	// result = moment().year(2014).month(5).date(9);
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

Utils.genLastDtDeltaUnit = function (rangeType) {
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

	return deltaUnit;
}

Utils.genLastStartEndDt = function (targetDt, rangeType) {
	var deltaUnit = Utils.genLastDtDeltaUnit(rangeType);
	var lastStartDt = moment(targetDt).subtract(deltaUnit, 1);
	var lastEndDt = moment(lastStartDt).add(Utils.getDtDetlaUnit(rangeType), 1);

	return {startDt: lastStartDt, endDt: lastEndDt};
}

Utils.setupUnitChoiceLayout = function (targetEleSel, unitCategorys, staticPrefix, unitClickedFunc) {
	var unitChoice = $(targetEleSel);
	$.each(unitCategorys, function(idx, unitCategory) {
		var unitLiDom = $("<li>"
			+ "<img src='" + staticPrefix + "images/unit/" + unitCategory.imgOff + "'>"
			+ "</li>");
		unitLiDom.find('img').hover(function() {
			$(this).attr("src", staticPrefix + "images/unit/" + unitCategory.imgOn);
		}, function() {
			$(this).attr("src", staticPrefix + "images/unit/" + unitCategory.imgOff);
		});
		unitChoice.append(unitLiDom);
	});
	unitChoice.find("li").each(function (unitCategoryIdx) {
		$(this).click({unitCategory: unitCategorys[unitCategoryIdx]}, function(event) {
			unitClickedFunc(event.data.unitCategory);
		});
	});
}

Utils.setupTimeChoiceLayout = function(targetEleSel, timeRangeClickedFunc) {
	var timeRangeTypes = [Utils.RANGE_TYPE_YEAR, Utils.RANGE_TYPE_MONTH,
		Utils.RANGE_TYPE_WEEK, Utils.RANGE_TYPE_DAY,
		Utils.RANGE_TYPE_NIGHT, Utils.RANGE_TYPE_HOUR];
	var timeChoice = $(targetEleSel);
	$.each(timeRangeTypes, function(idx, rangeType) {
		var timeLiDom = $("<li id='time-choice-" + rangeType + "-icon' range_type='" + rangeType + "'></li>");
		timeLiDom.insertBefore("#select-dt-section");
	})
	timeChoice.find("li").click(function () {
		var newRangeType = $(this).attr("range_type");
		timeRangeClickedFunc(newRangeType);
	});
}

Utils.setupDropDownPanelBtn = function() {
	$('.expand-drop-down-panel-btn').click(function () {
		var menuLinks = $('.drop-down-panel-content');
		if (menuLinks.css('display') === 'none') {
			$(this).css({transform: 'rotate(180deg)'});
		} else {
			$(this).css({transform: 'rotate(0deg)'});
		}
		menuLinks.slideToggle(700, "easeOutBounce", function() {});
	}).css({transform: 'rotate(180deg)'});
}

Utils.formatWithCommas = function (val) {
    return val.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

Utils.fixed1DecIfLessThan10 = function(val) {
	var numOfDec = (val < 10) ? 1 : 0;
	return val.toFixed(numOfDec);
}
