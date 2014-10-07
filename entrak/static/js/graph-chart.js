function GraphChart(graphEleSel, yAxisSliderEleSel, xAxisSliderEleSel, retrieveReadingCallback, multiLangTexts) {
	this.graphEleSel = graphEleSel;
	this.yAxisSliderEleSel = yAxisSliderEleSel;
	this.xAxisSliderEleSel = xAxisSliderEleSel;
	this.retrieveReadingCallback = retrieveReadingCallback;

	this.plot = null;
	this.entrakSystem = null;
	this.totalSeries = null;
	this.sourceSeries = null;
	this.lastSeries = null;
	this.highestSeries = null;
	this.lowestSeries = null;
	this.customSeries = null;
	this.showLast = false;
	this.showHighest = false;
	this.showLowest = false;
	this.showCustom = false;
	this.highestDt = null;
	this.lowestDt = null;
	this.customDt = null;
	this.currentRangeType = null;
	this.currentDt = null;
	this.lastStartEndDt = null;
	this.currentSelectedSourceIdx = [];
	this.selectedSourceColorMap = {};
	this.currentXaxisOptions = {};
	this.currentUnit = null;
	this.xAxisSliderCallback = null;
	this.needResetXSlider = true;
	this.getSourceDataAjaxId = null;
	this.getSourceDataTimeoutId = null;
	this.growFinishCallback = null;

	Utils.setLangText(GraphChart, multiLangTexts);
}

GraphChart.DATA_UPDATE_INTERVAL = 60000

GraphChart.prototype.getTotalSeriesBaseOptions = function() {
	var optionInfos = {
		color: '#81D51D',
		label: GraphChart.TOTAL_TEXT,
		bars: {
			barWidth: 0.4,
			align: "center",
			show: true,
			fill: 1,
		},
	};

	return optionInfos;
};

GraphChart.prototype.SERIES_LINE_COLORS = ['#FFAE20', '#EF7C56', '#35BC99', '#C94CD7', '#587EFF'];
GraphChart.prototype.SERIES_BASE_OPTIONS = {
	lines: {
		lineWidth: 2.5,
		show: true,
	},
	points: {
		radius: 4,
		symbol: 'circle',
		fillColor: "#FFFFFF",
		show: true,
	},
	clickable: false,
};

GraphChart.prototype._retrieveSourceReadings = function(groupedSourceInfos, startDt, endDt, doneFunc) {
	var graphChartThis = this;

	$.ajax({
		type: "POST",
		url: "../source_readings/",
		data: {
			grouped_source_infos: JSON.stringify(groupedSourceInfos),
			range_type: Utils.API_RANGE_TYPES[graphChartThis.currentRangeType],
			unit_category_code: graphChartThis.currentUnit.code,
			has_detail_rate: graphChartThis.currentUnit.hasDetailRate,
			global_rate: graphChartThis.currentUnit.globalRate,
			start_dt: startDt.unix(),
			end_dt: endDt.unix(),
		},
	}).done(function(data) {
		doneFunc(data);
	});
}

GraphChart.prototype.needUpdatePeriodically = function() {
	var realtimeBoundStartEndDt = Utils.genStartEndDt(moment(), this.currentRangeType);
	return ((this.currentDt.isSame(realtimeBoundStartEndDt.startDt)
		|| this.currentDt.isAfter(realtimeBoundStartEndDt.startDt))
		&& this.currentDt.isBefore(realtimeBoundStartEndDt.endDt));
}

GraphChart.prototype.getSourceReadings = function (fromAutoRefresh) {
	fromAutoRefresh = typeof fromAutoRefresh !== 'undefined' ? fromAutoRefresh : false;

	var graphChartThis = this;
	var startEndDt = this.genCurrentStartEndDt();
	this.lastStartEndDt = Utils.genLastStartEndDt(startEndDt.startDt, this.currentRangeType);
	var groupedSourceInfos = this.entrakSystem.getGroupedSourceInfos();
	var requestingAjaxId = moment().toDate().getTime();
	this.getSourceDataAjaxId = requestingAjaxId;

	clearTimeout(this.getSourceDataTimeoutId);
	if (graphChartThis.needUpdatePeriodically()) {
		this.getSourceDataTimeoutId = setTimeout(function() {
			graphChartThis.getSourceReadings(true);
		}, GraphChart.DATA_UPDATE_INTERVAL);
	}

	this._retrieveSourceReadings(groupedSourceInfos, startEndDt.startDt, startEndDt.endDt, function(data) {
		// ensure it is the latest requsting one
		if (requestingAjaxId === graphChartThis.getSourceDataAjaxId) {
			graphChartThis.updateXAxisOptions(startEndDt.startDt);
			graphChartThis.transformReadingToChartDatasets(data);
			graphChartThis.plotGraphChart();

			graphChartThis.retrieveReadingCallback(fromAutoRefresh);
		}
	});
}

GraphChart.prototype.getLastSourceReadings = function() {
	var graphChartThis = this;
	var startEndDt = this.lastStartEndDt;
	var groupedSourceInfos = [{name: GraphChart.PREVIOUS_TEXT, source_ids: graphChartThis.entrakSystem.getAllSourceIds()}];
	this._retrieveSourceReadings(groupedSourceInfos, startEndDt.startDt, startEndDt.endDt, function(data) {
		graphChartThis.transformReadingToSeries(data[0], 'lastSeries');
		graphChartThis.lastSeries.color = "#F7AF25";
		graphChartThis.updateCompareChoice();
	});
}

GraphChart.prototype.getCustomSourceReadings = function() {
	var graphChartThis = this;
	var startEndDt = this.customDt;
	var groupedSourceInfos = [{name: GraphChart.CUSTOM_TEXT, source_ids: graphChartThis.entrakSystem.getAllSourceIds()}];
	this._retrieveSourceReadings(groupedSourceInfos, startEndDt.startDt, startEndDt.endDt, function(data) {
		graphChartThis.transformReadingToSeries(data[0], 'customSeries');
		graphChartThis.customSeries.color = "#587EFF";
		graphChartThis.updateCompareChoice();
	});
}

GraphChart.prototype.getHighestSourceReadings = function(doneCallback) {
	var graphChartThis = this;
	var startEndDt = this.genCurrentStartEndDt();
	var sourceInfos = {name: GraphChart.HIGHEST_TEXT, source_ids: graphChartThis.entrakSystem.getAllSourceIds()};

	$.ajax({
		type: "POST",
		url: "../highest_lowest_source_readings/",
		data: {
			start_dt: startEndDt.startDt.unix(),
			source_infos: JSON.stringify(sourceInfos),
			range_type: Utils.API_RANGE_TYPES[graphChartThis.currentRangeType],
			unit_category_code: graphChartThis.currentUnit.code,
			has_detail_rate: graphChartThis.currentUnit.hasDetailRate,
			global_rate: graphChartThis.currentUnit.globalRate,
			tz_offset: graphChartThis.currentDt.toDate().getTimezoneOffset(),
			is_highest: true,
		},
	}).done(function(data) {
		if (data["timestamp"] !== null) {
			graphChartThis.highestDt = moment.unix(data["timestamp"]);
			graphChartThis.transformReadingToSeries(data, 'highestSeries');
			graphChartThis.highestSeries.color = "#ED6D43";
			graphChartThis.updateCompareChoice();
		} else {
			graphChartThis.highestDt = null;
			graphChartThis.highestSeries = null;
		}

		doneCallback();
	}).fail(function(jqXHR, textStatus) {
		console.log(jqXHR.responseText);
	});
}

GraphChart.prototype.getLowestSourceReadings = function(doneCallback) {
	var graphChartThis = this;
	var startEndDt = this.genCurrentStartEndDt();
	var sourceInfos = {name: GraphChart.LOWEST_TEXT, source_ids: graphChartThis.entrakSystem.getAllSourceIds()};

	$.ajax({
		type: "POST",
		url: "../highest_lowest_source_readings/",
		data: {
			start_dt: startEndDt.startDt.unix(),
			source_infos: JSON.stringify(sourceInfos),
			range_type: Utils.API_RANGE_TYPES[graphChartThis.currentRangeType],
			unit_category_code: graphChartThis.currentUnit.code,
			has_detail_rate: graphChartThis.currentUnit.hasDetailRate,
			global_rate: graphChartThis.currentUnit.globalRate,
			tz_offset: graphChartThis.currentDt.toDate().getTimezoneOffset(),
			is_highest: false,
		},
	}).done(function(data) {
		if (data["timestamp"] !== null) {
			graphChartThis.lowestDt = moment.unix(data["timestamp"]);
			graphChartThis.transformReadingToSeries(data, 'lowestSeries');
			graphChartThis.lowestSeries.color = "#35BC99";
			graphChartThis.updateCompareChoice();
		} else {
			graphChartThis.lowestDt = null;
			graphChartThis.lowestSeries = null;
		}

		doneCallback();
	});
}

GraphChart.prototype.getDisplayEnergyReadings = function() {
	var graphChartThis = this;
	$.ajax({
		type: "POST",
		url: "../display_energy_readings/",
		data: {
		},
	}).done(function(data) {
		graphChartThis.updateXAxisOptions(moment().startOf('day'));

		var seriesData = {};
		$.each(data, function(key, readings) {
			seriesData[key] = [];
			$.each(readings, function(timestamp, value) {
				var transformedX = graphChartThis.transformXCoordinate(timestamp);
				seriesData[key].push([transformedX, value]);
			})

			seriesData[key].sort(function (a, b) {
				return a[0]-b[0];
			});
		})

		var series = [
			$.extend(true, {data: seriesData['current']}, graphChartThis.getTotalSeriesBaseOptions()),
			$.extend(true, {color: "#F16D4E", data: seriesData['last']}, graphChartThis.SERIES_BASE_OPTIONS),
		];

		graphChartThis.plot = $(graphChartThis.graphEleSel).plot(series, {
			xaxis: {
				tickLength: 0,
				min: graphChartThis.currentXaxisOptions.min,
				max: graphChartThis.currentXaxisOptions.max,
				ticks: graphChartThis.currentXaxisOptions.ticks,
				font: {
					size: 14,
					weight: "bold",
					family: "sans-serif",
					color: "#2E3E52"
				},
			},
			yaxis: {
				font: {
					size: 14,
					weight: "bold",
					family: "sans-serif",
					color: "#2E3E52"
				},
			},
			legend: {
				show: false,
			},
			grid: {
				borderWidth: {
					'top': 0,
					'right': 0,
					'bottom': 1.2,
					'left': 1.2,
				},
				borderColor: {
					'bottom': "#9BCEDA",
					'left': "#9BCEDA",
				},
			},
		}).data("plot");
		
	}).fail(function(jqXHR, textStatus) {
		console.log(jqXHR.responseText);
	});
}

GraphChart.prototype.transformXCoordinate = function (value) {
	value_dt = moment.unix(value);
	if (this.currentRangeType === Utils.RANGE_TYPE_HOUR) {
		value = value_dt.minute();
	} else if (this.currentRangeType === Utils.RANGE_TYPE_DAY) {
		value = value_dt.hour();
	} else if (this.currentRangeType === Utils.RANGE_TYPE_NIGHT) {
		value = value_dt.hour();
		if (value >= 20) {
			value -= 20;
		} else {
			value += 4;
		}
	} else if (this.currentRangeType === Utils.RANGE_TYPE_WEEK) {
		value = value_dt.day();
	} else if (this.currentRangeType === Utils.RANGE_TYPE_MONTH) {
		value = value_dt.date() - 1;
	} else if (this.currentRangeType === Utils.RANGE_TYPE_YEAR) {
		value = value_dt.month();
	}

	return value;
}

GraphChart.prototype.updateUnit = function (newUnit) {
	this.currentUnit = newUnit;
	this.getSourceReadings();
}

GraphChart.prototype.transformReadingToChartDatasets = function (groupedReadings) {
	var graphChartThis = this;
	this.sourceSeries = [];
	
	var totalReadings = {};

	$.each(groupedReadings, function(groupIdx, readingInfos) {
		var series = $.extend(
			true,
			{
				label: readingInfos.name,
				data: []
			},
			graphChartThis.SERIES_BASE_OPTIONS);
		$.each(readingInfos.readings, function(readingTimestamp, readingVal) {
			var transformedX = graphChartThis.transformXCoordinate(readingTimestamp);
			series.data.push([transformedX, readingVal]);
			series.data.sort(function (a, b) {
				return a[0]-b[0];
			});

			if (transformedX in totalReadings) {
				totalReadings[transformedX] += readingVal;
			} else {
				totalReadings[transformedX] = readingVal;
			}
		});

		graphChartThis.sourceSeries.push(series);
	});

	this.totalSeries = $.extend(true, {data: []}, this.getTotalSeriesBaseOptions());
	$.each(totalReadings, function(readingTimestamp, readingVal) {
		graphChartThis.totalSeries.data.push([readingTimestamp, readingVal]);
	});
}

GraphChart.prototype.transformReadingToSeries = function (readingInfo, targetName) {
	var graphChartThis = this;

	var series = $.extend(
		true,
		{
			label: readingInfo.name,
			data: []
		},
		graphChartThis.SERIES_BASE_OPTIONS);
	$.each(readingInfo.readings, function(readingTimestamp, readingVal) {
		var transformedX = graphChartThis.transformXCoordinate(readingTimestamp);
		series.data.push([transformedX, readingVal]);
		series.data.sort(function (a, b) {
			return a[0]-b[0];
		});
	});

	this[targetName] = series;
}

GraphChart.prototype.plotGraphChart = function () {
	var graphChartThis = this;

	var willPlotSeries = [];
	$.each(this.currentSelectedSourceIdx, function(idx, seriesIdx) {
		var series = $.extend(true, {}, graphChartThis.sourceSeries[seriesIdx]);
		series.color = graphChartThis.selectedSourceColorMap[seriesIdx];
		willPlotSeries.push(series);
	});

	willPlotSeries.splice(0, 0, this.totalSeries);

	this.plot = $(this.graphEleSel).plot(willPlotSeries, {
		series: {
			grow: {
				active: true,
				duration: 800,
			}
		},
		xaxis: {
			tickLength: 0,
			min: this.currentXaxisOptions.min,
			max: this.currentXaxisOptions.max,
			ticks: this.currentXaxisOptions.ticks,
			font: {
				size: 14,
				weight: "bold",
				family: "sans-serif",
				color: "#2E3E52"
			},
		},
		yaxis: {
			font: {
				size: 14,
				weight: "bold",
				family: "sans-serif",
				color: "#2E3E52"
			},
			tickFormatter: function formatter(val, axis) {
				var factor = axis.tickDecimals ? Math.pow(10, axis.tickDecimals) : 1;
				var formatted = "" + Math.round(val * factor) / factor;
				if (parseFloat(formatted) >= 1000) {
					formatted = Utils.formatWithCommas(formatted)
				}
				return formatted;
			},
		},
		legend: {
			show: true,
			noColumns: 6,
			container: $('.chart-legend-container'),
		},
		grid: {
			clickable: true,
			hoverable: true,
			borderWidth: {
				'top': 0,
				'right': 0,
				'bottom': 1.2,
				'left': 1.2,
			},
			borderColor: {
				'bottom': "#9BCEDA",
				'left': "#9BCEDA",
			},
		},
		tooltip: true,
		tooltipOpts: {
			content: "%s: %y",
			shifts: {
				x: -60,
				y: 25
			}
		},
		selection: {
			mode: "x",
			color: "#81D51D",
		}
	}).data("plot");
	$(this.graphEleSel).on('growFinished', function() {
		graphChartThis.plot.getOptions().series.grow.active = false;
		if (graphChartThis.growFinishCallback !== null) {
			graphChartThis.growFinishCallback();
		}
		$(this.graphEleSel).off('growFinished');
	});
	this.refreshYAxisSlider();
	this.plot.setupGrid();
	this.plot.draw();

	if (this.needResetXSlider) {
		this.needResetXSlider = false;
		this.resetXAxisSlider();
	} else {
		this.refreshXAxisSlider();
	}

	$(this.graphEleSel).off('plotclick').on('plotclick', function(event, pos, item) {
		if (item && graphChartThis.currentRangeType !== Utils.RANGE_TYPE_HOUR) {
			var startEndDt = graphChartThis.genCurrentStartEndDt();
			graphChartThis.currentDt = graphChartThis.transformXToDt(startEndDt.startDt, item.datapoint[0]);

			if (graphChartThis.currentRangeType === Utils.RANGE_TYPE_DAY
				|| graphChartThis.currentRangeType === Utils.RANGE_TYPE_NIGHT) {
				graphChartThis.currentRangeType = Utils.RANGE_TYPE_HOUR;
			} else if (graphChartThis.currentRangeType === Utils.RANGE_TYPE_WEEK
				|| graphChartThis.currentRangeType === Utils.RANGE_TYPE_MONTH) {
				graphChartThis.currentRangeType = Utils.RANGE_TYPE_DAY;
			} else if (graphChartThis.currentRangeType === Utils.RANGE_TYPE_YEAR) {
				graphChartThis.currentRangeType = Utils.RANGE_TYPE_MONTH;
			}
			
			graphChartThis.getSourceReadings();
		}
	});
}

GraphChart.prototype.updateSourceChoice = function (selectedSeriesIdxs) {
	var graphChartThis = this;
	this.currentSelectedSourceIdx = selectedSeriesIdxs;

	var newColorMap = {};
	var availableColors = graphChartThis.SERIES_LINE_COLORS.slice(0);
	$.each(this.currentSelectedSourceIdx, function(idx, value) {
		if (value in graphChartThis.selectedSourceColorMap) {
			newColorMap[value] = graphChartThis.selectedSourceColorMap[value];
			availableColors.splice($.inArray(graphChartThis.selectedSourceColorMap[value], availableColors), 1);
		} else {
			newColorMap[value] = null;
		}
	});
	$.each(newColorMap, function(key, value) {
		if (value === null) {
			newColorMap[key] = availableColors.shift();
		}
	});
	this.selectedSourceColorMap = newColorMap;
	
	var willPlotSeries = [];
	$.each(this.currentSelectedSourceIdx, function(idx, seriesIdx) {
		var series = $.extend(true, {}, graphChartThis.sourceSeries[seriesIdx]);
		series.color = graphChartThis.selectedSourceColorMap[seriesIdx];
		willPlotSeries.push(series);
	});

	willPlotSeries.splice(0, 0, this.totalSeries);

	this.plot.setData(willPlotSeries);
	this.plot.setupGrid();
	this.plot.draw();
}

GraphChart.prototype.updateCompareChoice = function () {
	var graphChartThis = this;
	var willPlotSeries = [];
	if (this.showLast && graphChartThis.lastSeries !== null) {
		willPlotSeries.push(graphChartThis.lastSeries);
	}
	if (this.showHighest && graphChartThis.highestSeries !== null) {
		willPlotSeries.push(graphChartThis.highestSeries);
	}
	if (this.showLowest && graphChartThis.lowestSeries !== null) {
		willPlotSeries.push(graphChartThis.lowestSeries);
	}
	if (this.showCustom && graphChartThis.customSeries !== null) {
		willPlotSeries.push(graphChartThis.customSeries);
	}

	willPlotSeries.splice(0, 0, this.totalSeries);

	this.plot.setData(willPlotSeries);
	this.refreshYAxisSlider();
	this.plot.setupGrid();
	this.plot.draw();
}

function roundMax(val) {
	var targetRoundDigit = val.toFixed(0).length - 2;
	return Math.ceil(val/(Math.pow(10, targetRoundDigit))+3)*Math.pow(10, targetRoundDigit);
}

GraphChart.prototype.refreshYAxisSlider = function () {
	var graphThis = this;

	var currentYMax = 0;
	$.each(graphThis.plot.getData(), function(seriesIdx, series) {
		var targetDatas = (series.dataOrg !== undefined) ? series.dataOrg : series.data;
		var yMax = Math.max.apply(Math, targetDatas.map(function(val) {
			return val[1];
		}));
		currentYMax = Math.max(currentYMax, yMax);
	});

	currentYMax = roundMax(currentYMax);
	graphThis.plot.getAxes().yaxis.options.max = currentYMax;
	var yMin = currentYMax*0.05;
	var yMax = currentYMax*1.75;
	var step = (yMax-yMin)/500;
	$(this.yAxisSliderEleSel).slider("option", {
		min: yMin,
		max: yMax,
		step: step,
		value: currentYMax,
	}).off("slide")
	.on("slide", function(event, ui) {
		graphThis.plot.getAxes().yaxis.options.max = ui.value;
		graphThis.plot.setupGrid();
		graphThis.plot.draw();
	});
}

GraphChart.prototype.resetXAxisSlider = function () {
	var xAxisSlider = $(this.xAxisSliderEleSel);
	xAxisSlider.slider("option", "values", [0, 0]);

	this.refreshXAxisSlider();
}

GraphChart.prototype.refreshXAxisSlider = function () {
	var graphChartThis = this;
	var xAxisSlider = $(this.xAxisSliderEleSel);
	xAxisSlider.slider("option", "min", this.currentXaxisOptions.min+1);
	xAxisSlider.slider("option", "max", this.currentXaxisOptions.max);

	$(this.xAxisSliderEleSel).off('slide').on('slide', function(event, ui) {
		graphChartThis.setHighlightRegion(ui.values);
	});

	var uiValues = $(this.xAxisSliderEleSel).slider("values");
	if (uiValues[0] !== uiValues[1]) {
		graphChartThis.setHighlightRegion(uiValues);
	}
}

GraphChart.prototype.setHighlightRegion = function (uiValues) {
	var startEndDt = this.genCurrentStartEndDt();

	var startIdx = uiValues[0];
	var endIdx = uiValues[1];
	this.plot.setSelection({
		xaxis: {
			from: startIdx-0.5,
			to: endIdx-0.5,
		}
	});

	var result = this.sumUpSeriesValueInRange(startIdx, endIdx);
	this.xAxisSliderCallback(
		uiValues,
		this.transformXToDt(startEndDt.startDt, startIdx),
		this.transformXToDt(startEndDt.startDt, endIdx),
		result
	);
}

GraphChart.prototype.transformXToDt = function (startDt, xVal) {
	var dtUnit = null;
	if (this.currentRangeType === Utils.RANGE_TYPE_HOUR) {
		dtUnit = 'm';
	} else if (this.currentRangeType === Utils.RANGE_TYPE_DAY || this.currentRangeType === Utils.RANGE_TYPE_NIGHT) {
		dtUnit = 'h';
	} else if (this.currentRangeType === Utils.RANGE_TYPE_WEEK || this.currentRangeType === Utils.RANGE_TYPE_MONTH) {
		dtUnit = 'd';
	} else if (this.currentRangeType === Utils.RANGE_TYPE_YEAR) {
		dtUnit = 'M';
	}

	return moment(startDt).add(xVal, dtUnit);
}

GraphChart.prototype.sumUpSeriesValueInRange = function (startIdx, endIdx) {
	return this.sourceSeries.map(function (series) {
		var value = series.data.reduce(function (previousVal, currentPts, index, array) {
			var value = (currentPts[0] >= startIdx && currentPts[0] < endIdx) ? currentPts[1] : 0;
			return previousVal + value;
		}, 0);

		return {label: series.label, value: value};
	});
}

GraphChart.prototype.genCurrentStartEndDt = function () {
	return Utils.genStartEndDt(this.currentDt, this.currentRangeType);
}

GraphChart.prototype.updateXAxisOptions = function (startDt) {
	var min = null;
	var max = null;
	var ticks = [];

	if (this.currentRangeType === Utils.RANGE_TYPE_HOUR) {
		min = -1;
		max = 60;
		for (var i = 0; i < 12; i++) {
			var tickLabel = moment(startDt).add(i*5, 'm').locale('en').format('h:mma');
			ticks.push([i*5, tickLabel]);
		};
	} else if (this.currentRangeType === Utils.RANGE_TYPE_DAY) {
		min = -1;
		max = 24;
		
		for (var i = 0; i < 12; i++) {
			var tickLabel = moment(startDt).add(i*2, 'h').locale('en').format('ha');
			ticks.push([i*2, tickLabel]);
		};
	} else if (this.currentRangeType === Utils.RANGE_TYPE_NIGHT) {
		min = -1;
		max = 12;

		for (var i = 0; i < 6; i++) {
			var tickLabel = moment(startDt).add(i*2, 'h').locale('en').format('ha');
			ticks.push([i*2, tickLabel]);
		};
	} else if (this.currentRangeType === Utils.RANGE_TYPE_WEEK) {
		min = -1;
		max = 7;
		var tickLabels = moment.weekdays();
		for (var i = 0; i < tickLabels.length; i++) {
			ticks.push([i, tickLabels[i]]);
		};
	} else if (this.currentRangeType === Utils.RANGE_TYPE_MONTH) {
		var dayOfEndOfMonth = moment(startDt).endOf('month').date();
		min = -1;
		max = dayOfEndOfMonth;
		for (var i = 0; i < dayOfEndOfMonth; i++) {
			ticks.push([i, i+1]);
		};
	} else if (this.currentRangeType === Utils.RANGE_TYPE_YEAR) {
		min = -1;
		max = 12;
		for (var i = 0; i < max; i++) {
			var tickLabel = moment(startDt).add(i, 'M').format('MMM');
			ticks.push([i, tickLabel]);
		}
	}

	this.currentXaxisOptions = {min: min, max: max, ticks: ticks};
}

GraphChart.prototype.updateCurrentDt = function (newDt) {
	this.currentDt = newDt;
	this.getSourceReadings();
}

GraphChart.prototype.updateCompareDt = function (newDt) {
	this.customDt = Utils.genStartEndDt(newDt, this.currentRangeType);;
}

GraphChart.prototype.updateCurrentRangeType = function (newRangeType) {
	this.currentRangeType = newRangeType;
	this.needResetXSlider = true;
	this.getSourceReadings();
}

GraphChart.prototype.goPrevOrNext = function (direction) {
	var delta = (direction === 'prev') ? -1 : 1;
	var deltaUnit = Utils.getDtDetlaUnit(this.currentRangeType);
	this.currentDt.add(delta, deltaUnit);
	this.getSourceReadings();
}

GraphChart.prototype.goPrev = function () {
	this.goPrevOrNext('prev');
}

GraphChart.prototype.goNext = function () {
	this.goPrevOrNext('next');
}
