function GraphChart(graphEleSel, yAxisSliderEleSel, xAxisSliderEleSel, retrieveReadingCallback) {
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
	this.currentXaxisOptions = {};
	this.currentUnit = null;
	this.xAxisSliderCallback = null;
}

GraphChart.prototype.TOTAL_SERIES_BASE_OPTIONS = {
	color: '#81D51D',
	label: 'Total',
	// lines: {
	// 	lineWidth: 2.5,
	// 	show: true
	// },
	// points: {
	// 	radius: 4,
	// 	symbol: 'circle',
	// 	fillColor: "#81D51D",
	// 	show: true
	// },
	bars: {
		barWidth: 0.4,
		align: "center",
		show: true,
		fill: 1,
	},
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

GraphChart.prototype.getSourceReadings = function () {
	var graphChartThis = this;
	var startEndDt = this.genCurrentStartEndDt();
	this.lastStartEndDt = Utils.genLastStartEndDt(startEndDt.startDt, this.currentRangeType);
	var groupedSourceInfos = this.entrakSystem.getGroupedSourceInfos();

	this._retrieveSourceReadings(groupedSourceInfos, startEndDt.startDt, startEndDt.endDt, function(data) {
		graphChartThis.updateXAxisOptions(startEndDt.startDt);
		graphChartThis.transformReadingToChartDatasets(data);
		graphChartThis.plotGraphChart();

		graphChartThis.retrieveReadingCallback();
	});
}

GraphChart.prototype.getLastSourceReadings = function() {
	var graphChartThis = this;
	var startEndDt = this.lastStartEndDt;
	var groupedSourceInfos = [{name: 'Previous', source_ids: graphChartThis.entrakSystem.getAllSourceIds()}];
	this._retrieveSourceReadings(groupedSourceInfos, startEndDt.startDt, startEndDt.endDt, function(data) {
		graphChartThis.transformReadingToSeries(data[0], 'lastSeries');
		graphChartThis.lastSeries.color = "#F7AF25";
		graphChartThis.updateCompareChoice();
	});
}

GraphChart.prototype.getCustomSourceReadings = function() {
	var graphChartThis = this;
	var startEndDt = this.customDt;
	var groupedSourceInfos = [{name: 'Custom', source_ids: graphChartThis.entrakSystem.getAllSourceIds()}];
	this._retrieveSourceReadings(groupedSourceInfos, startEndDt.startDt, startEndDt.endDt, function(data) {
		graphChartThis.transformReadingToSeries(data[0], 'customSeries');
		graphChartThis.customSeries.color = "#587EFF";
		graphChartThis.updateCompareChoice();
	});
}

GraphChart.prototype.getHighestSourceReadings = function(doneCallback) {
	var graphChartThis = this;
	var sourceInfos = {name: 'Highest', source_ids: graphChartThis.entrakSystem.getAllSourceIds()};

	$.ajax({
		type: "POST",
		url: "../highest_lowest_source_readings/",
		data: {
			source_infos: JSON.stringify(sourceInfos),
			range_type: Utils.API_RANGE_TYPES[graphChartThis.currentRangeType],
			tz_offset: graphChartThis.currentDt.toDate().getTimezoneOffset(),
			is_highest: true,
		},
	}).done(function(data) {
		graphChartThis.highestDt = moment.unix(data["timestamp"]);
		graphChartThis.transformReadingToSeries(data, 'highestSeries');
		graphChartThis.highestSeries.color = "#ED6D43";
		graphChartThis.updateCompareChoice();

		doneCallback();
	});
}

GraphChart.prototype.getLowestSourceReadings = function(doneCallback) {
	var graphChartThis = this;
	var sourceInfos = {name: 'Lowest', source_ids: graphChartThis.entrakSystem.getAllSourceIds()};

	$.ajax({
		type: "POST",
		url: "../highest_lowest_source_readings/",
		data: {
			source_infos: JSON.stringify(sourceInfos),
			range_type: Utils.API_RANGE_TYPES[graphChartThis.currentRangeType],
			tz_offset: graphChartThis.currentDt.toDate().getTimezoneOffset(),
			is_highest: false,
		},
	}).done(function(data) {
		graphChartThis.lowestDt = moment.unix(data["timestamp"]);
		graphChartThis.transformReadingToSeries(data, 'lowestSeries');
		graphChartThis.lowestSeries.color = "#35BC99";
		graphChartThis.updateCompareChoice();

		doneCallback();
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

	this.totalSeries = $.extend(true, {data: []}, this.TOTAL_SERIES_BASE_OPTIONS);
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

GraphChart.prototype.setSeriesLineColor = function (sourceSeries) {
	var graphThis = this;
	$.each(sourceSeries, function (idx, series) {
		series.color = graphThis.SERIES_LINE_COLORS[idx];
	});
}

GraphChart.prototype.plotGraphChart = function () {
	var graphThis = this;
	this.plot = $(this.graphEleSel).plot([this.totalSeries], {
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
		},
		legend: {
			show: true,
			noColumns: 6,
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
		graphThis.plot.getOptions().series.grow.active = false;
		$(this.graphEleSel).off('growFinished');
	});
	this.refreshYAxisSlider();
	this.plot.setupGrid();
	this.plot.draw();

	this.refreshXAxisSlider();

	$(this.graphEleSel).off('plotclick').on('plotclick', function(event, pos, item) {
		if (item && graphThis.currentRangeType !== Utils.RANGE_TYPE_HOUR) {
			var startEndDt = graphThis.genCurrentStartEndDt();
			graphThis.currentDt = graphThis.transformXToDt(startEndDt.startDt, item.datapoint[0]);

			if (graphThis.currentRangeType === Utils.RANGE_TYPE_DAY
				|| graphThis.currentRangeType === Utils.RANGE_TYPE_NIGHT) {
				graphThis.currentRangeType = Utils.RANGE_TYPE_HOUR;
			} else if (graphThis.currentRangeType === Utils.RANGE_TYPE_WEEK
				|| graphThis.currentRangeType === Utils.RANGE_TYPE_MONTH) {
				graphThis.currentRangeType = Utils.RANGE_TYPE_DAY;
			} else if (graphThis.currentRangeType === Utils.RANGE_TYPE_YEAR) {
				graphThis.currentRangeType = Utils.RANGE_TYPE_MONTH;
			}
			
			graphThis.getSourceReadings();
		}
	});
}

GraphChart.prototype.updateSourceChoice = function (selectedSeriesIdxs) {
	var graphChartThis = this;
	this.currentSelectedSourceIdx = selectedSeriesIdxs;

	var willPlotSeries = [];
	$.each(this.currentSelectedSourceIdx, function(idx, seriesIdx) {
		willPlotSeries.push(graphChartThis.sourceSeries[seriesIdx]);
	});
	this.setSeriesLineColor(willPlotSeries);

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
	var yMin = currentYMax*0.25;
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

GraphChart.prototype.refreshXAxisSlider = function () {
	var graphThis = this;
	var startEndDt = this.genCurrentStartEndDt();
	var xAxisSlider = $(this.xAxisSliderEleSel);
	xAxisSlider.slider("option", "min", this.currentXaxisOptions.min+1);
	xAxisSlider.slider("option", "max", this.currentXaxisOptions.max);
	xAxisSlider.slider("option", "values", [0, 0]);
	xAxisSlider.off('slide').on('slide', function(event, ui) {
		var startIdx = ui.values[0];
		var endIdx = ui.values[1];
		graphThis.plot.setSelection({
			xaxis: {
				from: ui.values[0]-0.5,
				to: ui.values[1]-0.5,
			}
		});

		var result = graphThis.sumUpSeriesValueInRange(startIdx, endIdx);
		graphThis.xAxisSliderCallback(
			ui.values,
			graphThis.transformXToDt(startEndDt.startDt, startIdx),
			graphThis.transformXToDt(startEndDt.startDt, endIdx),
			result
		);
	});
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

	return moment(startDt).add(dtUnit, xVal);
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
			var tickLabel = moment(startDt).add('m', i*5).format('h:mma');
			ticks.push([i*5, tickLabel]);
		};
	} else if (this.currentRangeType === Utils.RANGE_TYPE_DAY) {
		min = -1;
		max = 24;
		
		for (var i = 0; i < 12; i++) {
			var tickLabel = moment(startDt).add('h', i*2).format('ha');
			ticks.push([i*2, tickLabel]);
		};
	} else if (this.currentRangeType === Utils.RANGE_TYPE_NIGHT) {
		min = -1;
		max = 12;

		for (var i = 0; i < 6; i++) {
			var tickLabel = moment(startDt).add('h', i*2).format('ha');
			ticks.push([i*2, tickLabel]);
		};
	} else if (this.currentRangeType === Utils.RANGE_TYPE_WEEK) {
		min = -1;
		max = 7;
		var tickLabels = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
		for (var i = 0; i < tickLabels.length; i++) {
			ticks.push([i, tickLabels[i]]);
		};
	} else if (this.currentRangeType === Utils.RANGE_TYPE_MONTH) {
		var dayOfEndOfMonth = moment(startDt).endOf('month').date();
		min = -1;
		max = dayOfEndOfMonth+1;
		for (var i = 0; i < dayOfEndOfMonth; i++) {
			ticks.push([i, i+1]);
		};
	} else if (this.currentRangeType === Utils.RANGE_TYPE_YEAR) {
		min = -1;
		max = 12;
		for (var i = 0; i < max; i++) {
			var tickLabel = moment(startDt).add('M', i).format('MMM');
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
	this.getSourceReadings();
}

GraphChart.prototype.goPrevOrNext = function (direction) {
	var delta = (direction === 'prev') ? -1 : 1;
	var deltaUnit = Utils.getDtDetlaUnit(this.currentRangeType);
	this.currentDt.add(deltaUnit, delta);
	this.getSourceReadings();
}

GraphChart.prototype.goPrev = function () {
	this.goPrevOrNext('prev');
}

GraphChart.prototype.goNext = function () {
	this.goPrevOrNext('next');
}

GraphChart.prototype.getSummary = function(getSummaryCallback) {
	var graphChartThis = this;
	var uptilMoment = Utils.getNowMoment();
	var startDt = moment(uptilMoment).startOf('day');
	var lastStartDt = moment(startDt).subtract('d', 1);
	var lastEndDt = moment(uptilMoment).subtract('d', 1);

	var sourceIds = this.entrakSystem.getAllSourceIds();
	$.ajax({
		type: "POST",
		url: "../summary/",
		data: {
			source_ids: JSON.stringify(sourceIds),
			range_type: Utils.API_RANGE_TYPES[Utils.RANGE_TYPE_HOUR],
			start_dt: startDt.unix(),
			end_dt: uptilMoment.unix(),
			last_start_dt: lastStartDt.unix(),
			last_end_dt: lastEndDt.unix(),
		},
	}).done(function(data) {
		graphChartThis.realtimeConsumption = data.realtime;
		graphChartThis.lastConsumption = data.last;
		getSummaryCallback();
	});
}
