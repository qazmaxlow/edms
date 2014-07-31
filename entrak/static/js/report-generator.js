function ReportGenerator(systemTree, timezone) {
	this.systemTree = systemTree;
	this.timezone = timezone;
	this.groupedSourceInfos = null;
	this.savingInfo = null;
	this.holidays = null;
	this.currentDt = null;
	this.currentEndDt = null;
	this.beginningStartDt = null;
};

ReportGenerator.REPORT_TYPE_MONTH = 'month';

ReportGenerator.KEY_STATISTICS_ROW_COLORS = ['#67C3D8', '#8C516F', '#D85299'];

ReportGenerator.MAX_PERCENTAGE_PIECE = 5;
ReportGenerator.DONUT_COLORS = ['#5DB9CF', '#814864', '#CF498D', '#807647', '#CFB948'];
ReportGenerator.OTHER_INFO_COLOR = '#000000';
ReportGenerator.FIRST_SPLIT_PIE_COLOR = '#7ACB39';
ReportGenerator.SECOND_SPLIT_PIE_COLOR = '#3F952C';

ReportGenerator.prototype.getReportData = function(currentDt, callbackFunc) {
	var reportGenThis = this;
	this.currentDt = currentDt;
	this.currentEndDt = moment(this.currentDt).add('M', 1);
	var	lastStartDt = reportGenThis.genLastDt(this.currentDt, ReportGenerator.REPORT_TYPE_MONTH);

	var firstRecordDt = moment.unix(this.systemTree.data.firstRecord).tz(this.timezone);
	if (firstRecordDt.date() === 1) {
		this.beginningStartDt = moment(firstRecordDt).startOf('M');
	} else {
		this.beginningStartDt = moment(firstRecordDt).add('M', 1).startOf('M');
	}
	var beginningEndDt = moment(this.beginningStartDt).add('M', 1);

	var lastSamePeriodStartDt = moment(this.currentDt).subtract('y', 1);
	var lastSamePeriodEndDt = moment(this.currentEndDt).subtract('y', 1);

	var requestData = {
		start_dt: this.currentDt.unix(),
		end_dt: this.currentEndDt.unix(),
		beginning_start_dt: this.beginningStartDt.unix(),
		beginning_end_dt: beginningEndDt.unix(),
		last_same_period_start_dt: lastSamePeriodStartDt.unix(),
		last_same_period_end_dt: lastSamePeriodEndDt.unix(),
		last_start_dt: lastStartDt.unix(),
		last_end_dt: this.currentDt.unix(),
	};

	$.ajax({
		type: "POST",
		url: "../report_data/",
		data: requestData,
	}).done(function(data) {
		console.log(data);
		callbackFunc(data);
	});
}

ReportGenerator.prototype.genLastDt = function(targetDt, reportType) {
	var result;
	if (reportType === ReportGenerator.REPORT_TYPE_MONTH) {
		result = moment(targetDt).subtract('M', 1);
	}

	return result;
}

ReportGenerator.prototype.assignData = function(data) {
	var reportGenThis = this;
	this.groupedSourceInfos = data.groupedSourceInfos;
	$.each(this.groupedSourceInfos, function(idx, sourceInfo) {
		var systemNode = reportGenThis.systemTree.find(function (node) {
			return (sourceInfo.systemCode === node.data.code);
		});
		sourceInfo.system = systemNode;
	});

	this.savingInfo = data.savingInfo;
	this.holidays = data.holidays;
}

ReportGenerator.prototype.insertSubInfo = function(target, template, bullet, color, name, percentVal) {
	var templateInfo = {
		bullet: bullet,
		color: color,
		name: name,
		percentVal: percentVal+"%"
	};
	var subInfoHtml = Mustache.render(template, templateInfo);
	target.append(subInfoHtml);
}

ReportGenerator.prototype.generateFullReport = function() {
	this.generateKeyStatistics();

	var combinedCurrentReadings = {};

	$.each(this.groupedSourceInfos, function(groupIdx, info) {
		$.each(info.currentReadings, function(timestamp, readingVal) {
			combinedCurrentReadings[timestamp] = ((timestamp in combinedCurrentReadings) ? combinedCurrentReadings[timestamp] : 0)
				+ readingVal; 
		});
	});

	this.generateWeekdayReport(combinedCurrentReadings);
}

ReportGenerator.prototype.generateKeyStatistics = function() {
	var reportGenThis = this;
	var totalEnergyUsage = 0;
	var totalCo2Usage = 0;
	var totalMoneyUsage = 0;

	$.each(reportGenThis.groupedSourceInfos, function(idx, info) {
		totalEnergyUsage += info.currentTotalEnergy;
		totalCo2Usage += info.currentTotalCo2;
		totalMoneyUsage += info.currentTotalMoney;
	});

	$("#current-energy-usage").text(Utils.formatWithCommas(totalEnergyUsage.toFixed(0)));
	$("#current-co2-usage").html(Utils.formatWithCommas((totalCo2Usage/1000).toFixed(0)) + " tons");
	$("#current-money-usage").text(Utils.formatWithCommas("$ " + totalMoneyUsage.toFixed(0)));

	var savedEnergyPercentSuffix, savedCo2SubText, savedMoneySubText,
		carImpactSubText, forestImpactSubText, elephantImpactSubText;
	if (reportGenThis.savingInfo.energy >= 0) {
		savedEnergyPercentSuffix = "less";
		savedCo2SubText = "of CO<sub>2</sub> reduced";
		savedMoneySubText = "in savings";
		carImpactSubText = "taken off the road for a month";
		forestImpactSubText = "of tropical rainforest protected";
		elephantImpactSubText = "Reduced CO<sub>2</sub> emissions equal to the weight of";
	} else {
		savedEnergyPercentSuffix = "more";
		savedCo2SubText = "of CO<sub>2</sub> increased";
		savedMoneySubText = "extra spending";
		carImpactSubText = "more on the road for a month";
		forestImpactSubText = "of tropical rainforest cut down";
		elephantImpactSubText = "Extra CO<sub>2</sub> emissions equal to the weight of";
	}
	var savedEnergyText = Utils.formatWithCommas(Math.abs(Utils.fixed1DecIfLessThan10(reportGenThis.savingInfo.energy))) + "% ";
	savedEnergyText += savedEnergyPercentSuffix;
	$("#save-energy-usage").text(savedEnergyText);

	// baseline should be just before first record
	var firstRecordMonth = moment.unix(this.systemTree.data.firstRecord).tz(this.timezone).startOf('M');
	var compareToDt = moment(this.currentDt).year(firstRecordMonth.year());
	if (compareToDt >= firstRecordMonth) {
		compareToDt.subtract('y', 1);
	}

	$("#save-energy-subtext").text("than " + compareToDt.format('MMM YYYY'));
	var savedCo2Text = Utils.formatWithCommas((Math.abs(reportGenThis.savingInfo.co2)/1000).toFixed(0));
	savedCo2Text += " tons";
	$("#save-co2-usage").text(savedCo2Text);
	$("#save-co2-subtext").html(savedCo2SubText);
	var savedMoneyText = "$ " + Utils.formatWithCommas(Math.abs(reportGenThis.savingInfo.money).toFixed(0));
	$("#save-money-usage").text(savedMoneyText);
	$("#save-money-subtext").text(savedMoneySubText);

	var co2InCar = Utils.formatWithCommas(Math.abs((reportGenThis.savingInfo.co2*0.003).toFixed(0)));
	$("#car-impact").text(co2InCar + " cars");
	$("#car-impact-subtext").text(carImpactSubText);
	var co2InForest = Utils.formatWithCommas(Math.abs((reportGenThis.savingInfo.co2*0.016).toFixed(0)));
	$("#forest-impact").text(co2InForest + " m²");
	$("#forest-impact-subtext").text(forestImpactSubText);
	var co2InElephant = Utils.formatWithCommas(Math.abs((reportGenThis.savingInfo.co2*0.00033).toFixed(0)));
	$("#elephant-impact").text(co2InElephant + " elephants");
	$("#elephant-impact-subtext").html(elephantImpactSubText);

	var keyRowTemplate = $("#key-statistics-row-template").html();
	Mustache.parse(keyRowTemplate);

	var keyStatSubDataContainer = $("#key-statistic-sub-data");
	keyStatSubDataContainer.empty();
	$.each(reportGenThis.groupedSourceInfos, function(idx, info) {
		var templateInfo = {
			energyVal: info.currentTotalEnergy,
			co2Val: info.currentTotalCo2,
			moneyVal: info.currentTotalMoney
		};
		$.each(templateInfo, function(key, value) {
			templateInfo[key] = Utils.formatWithCommas(value.toFixed(0));
		});

		if (info.systemCode === report.entrakSystem.systemTree.data.code) {
			templateInfo.usageTypeName = info.sourceName;
			templateInfo.order = info.sourceOrder;
		} else {
			templateInfo.usageTypeName = info.system.data.name;
			templateInfo.order = -1;
		}
		templateInfo.nameBackgroundColor = ReportGenerator.KEY_STATISTICS_ROW_COLORS[(
				idx%ReportGenerator.KEY_STATISTICS_ROW_COLORS.length
			)]

		var rowHtml = Mustache.render(keyRowTemplate, templateInfo);
		keyStatSubDataContainer.append(rowHtml);
	});

	keyStatSubDataContainer.find(">div").tsort(
		'span.usage-type-name', {attr: 'order'},
		'span.usage-type-name', {order:'asc'});

	var keySubInfoTemplate = $("#key-percent-sub-info-template").html();
	Mustache.parse(keySubInfoTemplate);

	var transformedDatas = [];
	var energyPercentSum = 0;
	var co2PercentSum = 0;
	var moneyPercentSum = 0;
	$.each(reportGenThis.groupedSourceInfos, function(infoIdx, info) {
		var dataInfo = {
			totalEnergy: info.currentTotalEnergy,
			totalCo2: info.currentTotalCo2,
			totalMoney: info.currentTotalMoney};
		dataInfo.name = (info.systemCode === report.entrakSystem.systemTree.data.code) ? info.sourceName : info.system.data.name;
		if (infoIdx < reportGenThis.groupedSourceInfos.length-1) {
			dataInfo.energyPercent = parseFloat(Utils.fixed1DecIfLessThan10((info.currentTotalEnergy/totalEnergyUsage)*100));
			dataInfo.co2Percent = parseFloat(Utils.fixed1DecIfLessThan10((info.currentTotalCo2/totalCo2Usage)*100));
			dataInfo.moneyPercent = parseFloat(Utils.fixed1DecIfLessThan10((info.currentTotalMoney/totalMoneyUsage)*100));
			energyPercentSum += dataInfo.energyPercent;
			co2PercentSum += dataInfo.co2Percent;
			moneyPercentSum += dataInfo.moneyPercent;
		} else {
			dataInfo.energyPercent = (100-energyPercentSum);
			dataInfo.co2Percent = (100-co2PercentSum);
			dataInfo.moneyPercent = (100-moneyPercentSum);
		}
		transformedDatas.push(dataInfo);
	});

	var needPlotDonuts = [
		{
			donutSel: '#energy-donut',
			sortVal: "totalEnergy",
			targetKey: "energyPercent",
			subInfoContainerSel: '#energy-percent-sub-info',
			otherInfoContainerSel: '#energy-percent-other-info'
		},
		{
			donutSel: '#co2-donut',
			sortVal: "totalCo2",
			targetKey: "co2Percent",
			subInfoContainerSel: '#co2-percent-sub-info',
			otherInfoContainerSel: '#co2-percent-other-info'
		},
		{
			donutSel: '#money-donut',
			sortVal: "totalMoney",
			targetKey: "moneyPercent",
			subInfoContainerSel: '#money-percent-sub-info',
			otherInfoContainerSel: '#money-percent-other-info'
		},
	];
	$.each(needPlotDonuts, function(donutIdx, donutInfo) {
		var donutSel = donutInfo.donutSel;
		var targetKey = donutInfo.targetKey;
		var subInfoContainer = $(donutInfo.subInfoContainerSel);
		var otherInfoContainer = $(donutInfo.otherInfoContainerSel);

		transformedDatas.sort(function(a, b) {
			return b[donutInfo.sortVal]-a[donutInfo.sortVal];
		});
		var plotData = [];
		if (transformedDatas.length <= ReportGenerator.MAX_PERCENTAGE_PIECE) {
			$.each(transformedDatas, function(dataIdx, dataInfo) {
				var matchColor = ReportGenerator.DONUT_COLORS[dataIdx];
				plotData.push({
					label: dataInfo[targetKey],
					data: dataInfo[targetKey],
					color: matchColor
				});

				reportGenThis.insertSubInfo(
					subInfoContainer,
					keySubInfoTemplate,
					'•',
					matchColor,
					dataInfo.name,
					dataInfo[targetKey]);
			})

			otherInfoContainer.parent().hide();
		} else {
			var donutSumPercent = 0;
			for (var i=0; i<ReportGenerator.MAX_PERCENTAGE_PIECE-1; i++) {
				var matchColor = ReportGenerator.DONUT_COLORS[i];
				plotData.push({
					label: transformedDatas[i][targetKey],
					data: transformedDatas[i][targetKey],
					color: matchColor
				});
				donutSumPercent += transformedDatas[i][targetKey];

				reportGenThis.insertSubInfo(
					subInfoContainer,
					keySubInfoTemplate,
					'•',
					matchColor,
					transformedDatas[i].name,
					transformedDatas[i][targetKey]);
			}
			plotData.push({
				label: parseFloat((100-donutSumPercent).toFixed(1)),
				data: (100-donutSumPercent),
				color: ReportGenerator.DONUT_COLORS[ReportGenerator.MAX_PERCENTAGE_PIECE-1]
			});

			for (var i=(ReportGenerator.MAX_PERCENTAGE_PIECE-1); i<transformedDatas.length; i++) {
				reportGenThis.insertSubInfo(
					otherInfoContainer,
					keySubInfoTemplate,
					'',
					ReportGenerator.OTHER_INFO_COLOR,
					transformedDatas[i].name,
					transformedDatas[i][targetKey]);
			}

			otherInfoContainer.parent().show();
		}

		$.plot(donutSel, plotData, {
			series: {
				pie: {
					show: true,
					innerRadius: 0.38,
					stroke: {
						width: 0
					},
					label: {
						radius: 0.92,
						formatter: function(label, series) {
							return '<span>' + label + '</span><span class="pie-text-percent">%</span>';
						}
					}
				}
			},
			legend: {
				show: false,
			}
		});
		
	});
}

ReportGenerator.prototype.generateCalendarReport = function() {
	//
}

ReportGenerator.prototype._fillInComparePercent = function(eleSel, oldUsage, newUsage, compareToDateText) {
	var comparePercentEle = $(eleSel);
	if (oldUsage === 0) {
		comparePercentEle.addClass("invalid-saving");
		comparePercentEle.removeClass("negative-saving");
		comparePercentEle.removeClass("negative-saving");
		comparePercentEle.find(".compare-percent").text("-");

		lessMoreText = "";
	} else {
		var usagePercent = (oldUsage-newUsage)/oldUsage*100;
		var lessMoreText;
		comparePercentEle.removeClass("invalid-saving");
		if (usagePercent >= 0 ) {
			comparePercentEle.addClass("positive-saving");
			comparePercentEle.removeClass("negative-saving");
			lessMoreText = "less";
		} else {
			comparePercentEle.addClass("negative-saving");
			comparePercentEle.removeClass("positive-saving");
			lessMoreText = "more";
		}
		comparePercentEle.find(".compare-percent").text(Utils.fixed1DecIfLessThan10(Math.abs(usagePercent)));
	}

	var comparedSubtext;
	if (oldUsage === 0) {
		comparedSubtext = "compared<br>to "+compareToDateText+" ***";
	} else {
		comparedSubtext = lessMoreText+" compared<br>to "+compareToDateText;
	}
	comparePercentEle.find(".compare-subtext").html(comparedSubtext);
}

ReportGenerator.prototype._genSubComparePercentInfo = function(oldUsage, newUsage, compareToDateText) {
	var result = {};
	if (oldUsage === 0) {
		result.percentText = "-";
		result.subText = "compared<br>to "+compareToDateText+" ***";
		result.savingClass = "invalid-saving";
	} else {
		var percent = (oldUsage-newUsage)/oldUsage*100;
		if (percent >= 0) {
			result.subText = "more";
			result.savingClass = "negative-saving";
		} else {
			result.subText = "less";
			result.savingClass = "positive-saving";
		}
		result.subText += " compared<br>to "+compareToDateText;
		result.percentText = Utils.formatWithCommas(Math.abs(percent).toFixed(0));
	}

	return result;
}

ReportGenerator.prototype._fillCalendar = function(eleSel, readings, averageUsage) {
	var reportGenThis = this;
	var calendarInfoContainer = $(eleSel);
	calendarInfoContainer.find(".calendar-title").text(this.currentDt.format('MMM YYYY'));

	var calendarContainer = calendarInfoContainer.find(".calendar-day-container");
	calendarContainer.empty();

	var calendarStartDt = moment(this.currentDt).startOf('w');
	var calendarEndDt = moment(this.currentEndDt).endOf('w');
	for (var calendarNowDt=calendarStartDt; calendarNowDt.isBefore(calendarEndDt); calendarNowDt.add('d', 1)) {
		var calendarDayEle = $("<div class='calendar-day'></div>");
		calendarDayEle.append("<div class='calendar-day-digit'>"+calendarNowDt.date()+"</div>");

		if (calendarNowDt.isBefore(reportGenThis.currentDt)
			|| calendarNowDt.isSame(reportGenThis.currentEndDt)
			|| calendarNowDt.isAfter(reportGenThis.currentEndDt)) {
			calendarDayEle.addClass('calendar-day-out-range');
		} else if (calendarNowDt.day() == 0
			|| calendarNowDt.day() == 6
			|| ($.inArray(calendarNowDt.format("YYYY-MM-DD"), reportGenThis.holidays) != -1)) {
			calendarDayEle.addClass('calendar-day-not-concern');
		} else {
			var diffPercent = (readings[calendarNowDt.unix()]-averageUsage)/averageUsage*100;
			var diffPercentText;
			if (diffPercent >= 0) {
				diffPercentText = "<span class='calendar-day-plus-symbol'>+</span> "+diffPercent.toFixed(0);
			} else {
				diffPercentText = "<span class='calendar-day-minus-symbol'>-</span> "+Math.abs(diffPercent.toFixed(0));
			}
			if (diffPercent >= 5) {
				calendarDayEle.addClass('calendar-day-better');
			} else if (diffPercent <= -5) {
				calendarDayEle.addClass('calendar-day-worse');
			}
			calendarDayEle.append("<div class='calendar-day-percent'>"
				+diffPercentText
				+"<span class='calendar-day-percent-symbol'>%</span></div>");
		}

		calendarContainer.append(calendarDayEle);
	}
}

ReportGenerator.prototype._insertCalendarSubInfo = function(eleSel, classIdPrefix,
	calendarTypeName, beginningDateText, firstSplitText, secondSplitText) {
	var reportGenThis = this;
	var detailContainer = $(eleSel);
	var subInfoTemplate = $("#sub-calendar-info-template").html();
	Mustache.parse(subInfoTemplate);

	$.each(this.groupedSourceInfos, function(groupIdx, info) {
		var classIdentifier = classIdPrefix+groupIdx;
		var averageUsage = info.currentWeekdayInfo.average;
		var compareBeginningInfo = reportGenThis._genSubComparePercentInfo(
			info.beginningWeekdayInfo.average, averageUsage, beginningDateText);
		var compareLastInfo = reportGenThis._genSubComparePercentInfo(
			info.lastWeekdayInfo.average, averageUsage, "last month");
		var compareLastSamePeriodInfo = reportGenThis._genSubComparePercentInfo(
			info.lastSamePeriodWeekdayInfo.average, averageUsage, "same period last year");
		var firstSplitPercent = parseFloat((info.currentWeekdayInfo.total/info.currentTotalEnergy*100).toFixed(1));
		var secondSplitPercent = parseFloat((100-firstSplitPercent).toFixed(1));
		var lowestDt = moment(info.currentWeekdayInfo.min.date, 'YYYY-MM-DD');
		var lowestText = lowestDt.format('D MMM YYYY')+' - '
			+Utils.formatWithCommas(info.currentWeekdayInfo.min.val.toFixed(0))
			+' kWh';
		var highestDt = moment(info.currentWeekdayInfo.max.date, 'YYYY-MM-DD');
		var highestText = highestDt.format('D MMM YYYY')+' - '
			+Utils.formatWithCommas(info.currentWeekdayInfo.max.val.toFixed(0))
			+' kWh';

		var templateInfo = {
			classIdentifier: classIdentifier,
			typeName: calendarTypeName,
			name: ('sourceName' in info) ? info.sourceName : info.system.data.name,
			averageUsage: Utils.formatWithCommas(averageUsage.toFixed(0)),
			compareBeginningClass: compareBeginningInfo.savingClass,
			compareBeginningPercent: compareBeginningInfo.percentText,
			compareBeginningSubtext: compareBeginningInfo.subText,
			compareLastClass: compareLastInfo.savingClass,
			compareLastPercent: compareLastInfo.percentText,
			compareLastSubtext: compareLastInfo.subText,
			compareLastSamePeriodClass: compareLastSamePeriodInfo.savingClass,
			compareLastSamePeriodPercent: compareLastSamePeriodInfo.percentText,
			compareLastSamePeriodSubtext: compareLastSamePeriodInfo.subText,
			firstSplitText: firstSplitText,
			secondSplitText: secondSplitText,
			firstSplitPercent: firstSplitPercent+"%",
			secondSplitPercent: secondSplitPercent+"%",
			lowestText: lowestText,
			highestText: highestText,
		};
		var subInfoHtml = Mustache.render(subInfoTemplate, templateInfo);
		detailContainer.append(subInfoHtml);

		reportGenThis._plotCalendarSubPieChart("."+classIdentifier+" .energy-split-pie",
			firstSplitPercent, secondSplitPercent,
			ReportGenerator.FIRST_SPLIT_PIE_COLOR, ReportGenerator.SECOND_SPLIT_PIE_COLOR);
	});
}

ReportGenerator.prototype._plotCalendarSubPieChart = function(eleSel, firstSplitPercent, secondSplitPercent, firstSplitColor, secondSplitColor) {
	var plotData = [
		{data: firstSplitPercent, color: firstSplitColor},
		{data: secondSplitPercent, color: secondSplitColor},
	];
	$.plot(eleSel, plotData, {
		series: {
			pie: {
				show: true,
				stroke: {
					width: 0
				},
				label: {
					show: false
				}
			}
		},
		legend: {
			show: false,
		}
	});
}

ReportGenerator.prototype.generateWeekdayReport = function(combinedReadings) {
	var reportGenThis = this;

	var allTotalUsage = 0;
	var totalUsage = 0;
	var averageUsage = 0;
	var beginningUsage = 0;
	var lastUsage = 0;
	var lastSamePeriodUsage = 0;

	var lowestWeekdayUsage = Number.MAX_SAFE_INTEGER;
	var lowestDt = null;
	var highestWeekdayUsage = 0;
	var highestDt = null;

	$.each(this.groupedSourceInfos, function(groupIdx, info) {
		allTotalUsage += info.currentTotalEnergy;
		totalUsage += info.currentWeekdayInfo.total;
		averageUsage += info.currentWeekdayInfo.average;
		beginningUsage += info.beginningWeekdayInfo.average;
		lastUsage += info.lastWeekdayInfo.average;
		lastSamePeriodUsage += info.lastSamePeriodWeekdayInfo.average;
	});

	var filteredReadings = {};
	$.each(combinedReadings, function(timestamp, val) {
		var dt = moment.unix(timestamp).tz(reportGenThis.timezone);
		if ((dt.day() >= 1 && dt.day() <= 5) && ($.inArray(dt.format("YYYY-MM-DD"), reportGenThis.holidays) == -1)) {
			filteredReadings[timestamp] = val;
			if (val > highestWeekdayUsage) {
				highestWeekdayUsage = val;
				highestDt = dt;
			}
			if (val < lowestWeekdayUsage) {
				lowestWeekdayUsage = Math.min(val, lowestWeekdayUsage);
				lowestDt = dt;
			}
		}
	});

	$("#weekday-info .average-usage").text(Utils.formatWithCommas(averageUsage.toFixed(0)));
	var beginningDateText = this.beginningStartDt.format("MMMM YYYY") + " **";
	this._fillInComparePercent("#weekday-info .compare-beginning", beginningUsage, averageUsage, beginningDateText);
	this._fillInComparePercent("#weekday-info .compare-last", lastUsage, averageUsage, "last month");
	this._fillInComparePercent("#weekday-info .compare-last-same-period", lastSamePeriodUsage, averageUsage, "same period last year");

	$("#weekday-info .lowest-usage-val").text(Utils.formatWithCommas(lowestWeekdayUsage.toFixed(0))+" kWh");
	$("#weekday-info .lowest-usage-date").text(lowestDt.format('D MMM YYYY'));
	$("#weekday-info .highest-usage-val").text(Utils.formatWithCommas(highestWeekdayUsage.toFixed(0))+" kWh");
	$("#weekday-info .highest-usage-date").text(highestDt.format('D MMM YYYY'));

	var weekdaySplitPercent = parseFloat((totalUsage/allTotalUsage*100).toFixed(1));
	var weekendSplitPercent = parseFloat((100-weekdaySplitPercent).toFixed(1));
	$("#weekday-info .first-split-val").text(weekdaySplitPercent);
	$("#weekday-info .second-split-val").text(weekendSplitPercent);

	this._plotCalendarSubPieChart("#weekday-info .energy-split-pie",
		weekdaySplitPercent, weekendSplitPercent,
		ReportGenerator.FIRST_SPLIT_PIE_COLOR, ReportGenerator.SECOND_SPLIT_PIE_COLOR);

	this._fillCalendar("#weekday-info .calendar-info-container", combinedReadings, averageUsage);

	this._insertCalendarSubInfo("#weekday-info .detail-container",
		'weekday-sub-calendar', 'Weekday', beginningDateText, 'Weekdays', 'Weekends');
}
