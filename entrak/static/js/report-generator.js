function ReportGenerator(systemTree, timezone) {
	this.systemTree = systemTree;
	this.timezone = timezone;
	this.groupedSourceInfos = null;
	this.savingInfo = null;
	this.currentDt = null;
};

ReportGenerator.REPORT_TYPE_MONTH = 'month';

ReportGenerator.KEY_STATISTICS_ROW_COLORS = ['#67C3D8', '#8C516F', '#D85299'];

ReportGenerator.MAX_PERCENTAGE_PIECE = 5;
ReportGenerator.DONUT_COLORS = ['#5DB9CF', '#814864', '#CF498D', '#807647', '#CFB948'];
ReportGenerator.OTHER_INFO_COLOR = '#000000';

ReportGenerator.prototype.getReportData = function(currentDt, callbackFunc) {
	var reportGenThis = this;
	this.currentDt = currentDt;
	var endDt = moment(currentDt).add('M', 1);
	var	lastStartDt = reportGenThis.genLastDt(currentDt, ReportGenerator.REPORT_TYPE_MONTH);

	var firstRecordDt = moment.unix(this.systemTree.data.firstRecord).tz(this.timezone);
	var beginningStartDt;
	if (firstRecordDt.date() === 1) {
		beginningStartDt = moment(firstRecordDt).startOf('M');
	} else {
		beginningStartDt = moment(firstRecordDt).add('M', 1).startOf('M');
	}
	var beginningEndDt = moment(beginningStartDt).add('M', 1);

	var lastSamePeriodStartDt = moment(currentDt).subtract('y', 1);
	var lastSamePeriodEndDt = moment(endDt).subtract('y', 1);

	var requestData = {
		start_dt: currentDt.unix(),
		end_dt: endDt.unix(),
		beginning_start_dt: beginningStartDt.unix(),
		beginning_end_dt: beginningEndDt.unix(),
		last_same_period_start_dt: lastSamePeriodStartDt.unix(),
		last_same_period_end_dt: lastSamePeriodEndDt.unix(),
		last_start_dt: lastStartDt.unix(),
		last_end_dt: currentDt.unix(),
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
