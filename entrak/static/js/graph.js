function Graph(graphEleSel, sourceChoiceEleSel, yAxisSliderEleSel, xAxisSliderEleSel) {
	this.graphEleSel = graphEleSel;
	this.sourceChoiceEleSel = sourceChoiceEleSel;
	this.yAxisSliderEleSel = yAxisSliderEleSel;
	this.xAxisSliderEleSel = xAxisSliderEleSel;

	this.plot = null;
	this.systemTree = null;
	this.units = [];
	this.currentSelectedSystem = null;
	this.totalSeries = null;
	this.sourceDatasets = null;
	this.currentRangeType = null;
	this.currentDt = null;
	this.currentXaxisOptions = {};
	this.currentUnit = null;
	this.xAxisSliderCallback = null;
}

Graph.prototype.RANGE_TYPE_HOUR		= 'hour';
Graph.prototype.RANGE_TYPE_DAY		= 'day';
Graph.prototype.RANGE_TYPE_NIGHT	= 'night';
Graph.prototype.RANGE_TYPE_WEEK		= 'week';
Graph.prototype.RANGE_TYPE_MONTH	= 'month';
Graph.prototype.RANGE_TYPE_YEAR		= 'year';
Graph.prototype.RANGE_TYPE_REALTIME	= 'realtime';

Graph.prototype.API_RANGE_TYPES = {
	'hour': 'hour',
	'day': 'day',
	'night': 'day',
	'week': 'week',
	'month': 'month',
	'year': 'year',
};

Graph.prototype.UNIT_KWH = 'kwh';

Graph.prototype.TOTAL_SERIES_BASE_OPTIONS = {
	color: '#81D51D',
	label: 'Total',
	lines: {
		lineWidth: 2.5,
		show: true
	},
	points: {
		radius: 4,
		symbol: 'circle',
		fillColor: "#81D51D",
		show: true
	},
	bars: {
		barWidth: 0.4,
		align: "center",
		show: true,
		fill: 1,
	},
};

Graph.prototype.SERIES_LINE_COLORS = ['#FFAE20', '#EF7C56', '#35BC99', '#C94CD7', '#587EFF'];
Graph.prototype.SERIES_BASE_OPTIONS = {
	lines: {
		lineWidth: 2.5,
		show: true,
	},
	points: {
		radius: 4,
		symbol: 'circle',
		fillColor: "#FFFFFF",
		show: true
	},
};

Graph.prototype.getSourceReadings = function () {
	var graphThis = this;
	var startEndDt = this.genStartEndDt();
	var sourceIds = this.getSourceIdsUnderTree();
	$.ajax({
		type: "POST",
		url: "../source_readings/",
		data: {
			source_ids: sourceIds,
			range_type: graphThis.API_RANGE_TYPES[graphThis.currentRangeType],
			start_dt: startEndDt.startDt.unix(),
			end_dt: startEndDt.endDt.unix(),
		},
	}).done(function(data) {
		$.each({data: data['readings'], lastData: data['last_readings']}, function (dataKey, readings) {
			graphThis.addDataToSystem(dataKey, readings);
		})

		graphThis.updateXAxisOptions(startEndDt.startDt);
		graphThis.transformReadingToChartDatasets();
		graphThis.plotGraph();
	});
}

Graph.prototype.addDataToSystem = function (dataKey, readings) {
	var graphThis = this;
	for (var sourceId in readings) {
		var systemNode = graphThis.findSystemNodeBySourceId(sourceId);
		systemNode.data.sources[sourceId][dataKey] = {};
		$.each(readings[sourceId], function(readingTimestamp, value) {
			systemNode.data.sources[sourceId][dataKey][readingTimestamp] = value;
		})
	}
}

Graph.prototype.addSourceToSystem = function (systemCode, sourceId, source) {
	var systemNode = this.systemTree.find(function (node) {
		return (systemCode === node.data.code);
	});
	systemNode.data.sources[sourceId] = source;
}

Graph.prototype.getSourceIdsUnderTree = function () {
	var sourceIds = [];
	this.currentSelectedSystem.traverseDown(function (node) {
		for (var sourceId in node.data.sources) {
			sourceIds.push(sourceId);
		}
	});

	return sourceIds;
}

Graph.prototype.findSystemNodeBySourceId = function (sourceId) {
	return this.currentSelectedSystem.find(function (node) {
		return (sourceId in node.data.sources);
	});
}

Graph.prototype.sumUpSourceReading = function (sourceReadings, sources) {
	var graphThis = this;
	$.each(sources, function (sourceId, source) {
		$.each(source.data, function(readingTimestamp, readingVal) {
			var transformedVal = graphThis.transformReading(source, readingTimestamp, readingVal);
			if (readingTimestamp in sourceReadings) {
				sourceReadings[readingTimestamp] += transformedVal;
			} else {
				sourceReadings[readingTimestamp] = transformedVal;
			}
		})
	})
}

Graph.prototype.transformXCoordinate = function (value) {
	value_dt = moment.unix(value);
	if (this.currentRangeType === this.RANGE_TYPE_HOUR) {
		value = value_dt.minute();
	} else if (this.currentRangeType === this.RANGE_TYPE_DAY) {
		value = value_dt.hour();
	} else if (this.currentRangeType === this.RANGE_TYPE_NIGHT) {
		value = value_dt.hour();
		if (value >= 12) {
			value -= 12;
		} else {
			value += 12;
		}
	} else if (this.currentRangeType === this.RANGE_TYPE_WEEK) {
		value = value_dt.day();
	} else if (this.currentRangeType === this.RANGE_TYPE_MONTH) {
		value = value_dt.date() - 1;
	} else if (this.currentRangeType === this.RANGE_TYPE_YEAR) {
		value = value_dt.month();
	}

	return value;
}

Graph.prototype.updateUnit = function (newUnit) {
	var graphThis = this;
	this.currentUnit = newUnit;
	this.transformReadingToChartDatasets();

	var willPlotSeries = [this.totalSeries];
	$(this.sourceChoiceEleSel).find("input:checked").each(function () {
		var seriesIdx = parseInt($(this).attr("series_idx"), 10);
		willPlotSeries.push(graphThis.sourceDatasets[seriesIdx]);
	});

	this.plot.setData(willPlotSeries);
	this.refreshYAxisSlider();
	this.plot.setupGrid();
	this.plot.draw();
}

Graph.prototype.transformReading = function (source, readingTimestamp, value) {
	var graphThis = this;
	if (this.currentUnit === this.UNIT_KWH) {
		return value;
	}

	var matchUnits = $.grep(this.units, function (unit) {
		return (unit.category === graphThis.currentUnit
			&& unit.catId === source.units[graphThis.currentUnit]
			&& unit.effectiveDate.unix() < readingTimestamp)
	});
	matchUnits.sort(function (a, b) {
		return b.effectiveDate.unix() - a.effectiveDate.unix();
	});
	var matchUnit = matchUnits[0];

	return matchUnit.rate*value;
}

Graph.prototype.transformReadingToChartDatasets = function () {
	var graphThis = this;
	var tree = this.currentSelectedSystem;
	this.sourceDatasets = [];
	var totalReadings = {};
	var sourceLineOptions = {show: true};

	this.sumUpSourceReading(totalReadings, tree.data.sources);
	for (var sourceId in tree.data.sources) {
		var source = tree.data.sources[sourceId];

		var series = $.extend(
			true,
			{
				label: source.name,
				data: []
			},
			this.SERIES_BASE_OPTIONS);
		$.each(source.data, function(readingTimestamp, readingVal) {
			var transformedVal = graphThis.transformReading(source, readingTimestamp, readingVal);
			series.data.push([graphThis.transformXCoordinate(readingTimestamp), transformedVal]);
		});
		this.sourceDatasets.push(series);
	}

	for (var childrenIdx in tree.children) {
		var subTree = tree.children[childrenIdx];
		var series = $.extend(
			true,
			{
				label: subTree.data.name,
				data: []
			},
			this.SERIES_BASE_OPTIONS);
		var sourceReadings = {};

		this.sumUpSourceReading(sourceReadings, subTree.data.sources);

		subTree.traverseDown(function (node) {
			graphThis.sumUpSourceReading(sourceReadings, node.data.sources);
		});

		for (var readingTimestamp in sourceReadings) {
			series.data.push([graphThis.transformXCoordinate(readingTimestamp), sourceReadings[readingTimestamp]]);

			if (readingTimestamp in totalReadings) {
				totalReadings[readingTimestamp] += sourceReadings[readingTimestamp];
			} else {
				totalReadings[readingTimestamp] = sourceReadings[readingTimestamp];
			}
		};
		this.sourceDatasets.push(series);
	};

	this.totalSeries = $.extend(true, {data: []}, this.TOTAL_SERIES_BASE_OPTIONS);
	for (var readingTimestamp in totalReadings) {
		this.totalSeries.data.push([graphThis.transformXCoordinate(readingTimestamp), totalReadings[readingTimestamp]]);
	}
}

Graph.prototype.setSeriesLineColor = function (sourceSeries) {
	var graphThis = this;
	$.each(sourceSeries, function (idx, series) {
		series.color = graphThis.SERIES_LINE_COLORS[idx];
	});
}

Graph.prototype.plotGraph = function () {
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
	this.setupSourceChoice();
	this.refreshYAxisSlider();
	this.plot.setupGrid();
	this.plot.draw();

	this.refreshXAxisSlider();
}

Graph.prototype.setupSourceChoice = function () {
	var graphThis = this;
	var choiceContainer = $(this.sourceChoiceEleSel);
	choiceContainer.empty();

	$.each(this.sourceDatasets, function(seriesIdx, series) {
		var choiceHtml = "<div>";
		choiceHtml += "<input type='checkbox' " + "series_idx='" + seriesIdx + "'"
			+ " name='" + series.label + "'"
			+ " ></input><label>" + series.label + "</label></div>";
		choiceContainer.append(choiceHtml);
	});

	choiceContainer.find("input").click(function () {
		var willPlotSeries = [];

		choiceContainer.find("input:checked").each(function () {
			var seriesIdx = parseInt($(this).attr("series_idx"), 10);
			willPlotSeries.push(graphThis.sourceDatasets[seriesIdx]);
		});
		graphThis.setSeriesLineColor(willPlotSeries);

		willPlotSeries.splice(0, 0, graphThis.totalSeries);

		graphThis.plot.setData(willPlotSeries);
		graphThis.plot.setupGrid();
		graphThis.plot.draw();
	});
}

function roundMax(val) {
	var targetRoundDigit = val.toFixed(0).length - 2;
	return Math.ceil(val/(Math.pow(10, targetRoundDigit))+3)*Math.pow(10, targetRoundDigit);
}

Graph.prototype.refreshYAxisSlider = function () {
	var graphThis = this;
	// first series is total and should be largest
	var targetDatas = (graphThis.plot.getData()[0].dataOrg !== undefined) ? graphThis.plot.getData()[0].dataOrg : graphThis.plot.getData()[0].data;
	var currentYMax = Math.max.apply(Math, targetDatas.map(function(val) {
		return val[1];
	}));
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

Graph.prototype.refreshXAxisSlider = function () {
	var graphThis = this;
	var startEndDt = this.genStartEndDt();
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

Graph.prototype.transformXToDt = function (startDt, xVal) {
	var dtUnit = null;
	if (this.currentRangeType === this.RANGE_TYPE_HOUR) {
		dtUnit = 'm';
	} else if (this.currentRangeType === this.RANGE_TYPE_DAY || this.currentRangeType === this.RANGE_TYPE_NIGHT) {
		dtUnit = 'h';
	} else if (this.currentRangeType === this.RANGE_TYPE_WEEK || this.currentRangeType === this.RANGE_TYPE_MONTH) {
		dtUnit = 'd';
	} else if (this.currentRangeType === this.RANGE_TYPE_YEAR) {
		dtUnit = 'M';
	}

	return moment(startDt).add(dtUnit, xVal);
}

Graph.prototype.sumUpSeriesValueInRange = function (startIdx, endIdx) {
	return this.sourceDatasets.map(function (series) {
		var value = series.data.reduce(function (previousVal, currentPts, index, array) {
			var value = (currentPts[0] >= startIdx && currentPts[0] < endIdx) ? currentPts[1] : 0;
			return previousVal + value;
		}, 0);

		return {label: series.label, value: value};
	});
}

Graph.prototype.genStartEndDt = function () {
	var startDt = null;
	var endDt = null;
	var currentDtClone = moment(this.currentDt);

	if (this.currentRangeType === this.RANGE_TYPE_HOUR) {
		startDt = currentDtClone;
		endDt = moment(startDt).add('h', 1);
	} else if (this.currentRangeType === this.RANGE_TYPE_DAY) {
		startDt = currentDtClone.startOf('day');
		endDt = moment(startDt).add('d', 1);
	} else if (this.currentRangeType == this.RANGE_TYPE_NIGHT) {
		if (currentDtClone.hour() >= 12) {
			startDt = currentDtClone.hour(12);
		} else {
			startDt = currentDtClone.hour(12).subtract('d', 1);
		}
		endDt = moment(startDt).add('d', 1);
	} else if (this.currentRangeType == this.RANGE_TYPE_WEEK) {
		startDt = currentDtClone.startOf('week');
		endDt = moment(startDt).add('d', 7);
	} else if (this.currentRangeType == this.RANGE_TYPE_MONTH) {
		startDt = currentDtClone.startOf('month');
		endDt = moment(startDt).add('M', 1);
	} else if (this.currentRangeType == this.RANGE_TYPE_YEAR) {
		startDt = currentDtClone.startOf('year');
		endDt = moment(startDt).add('y', 1);
	}

	return {startDt: startDt, endDt: endDt}
}

Graph.prototype.updateXAxisOptions = function (startDt) {
	var min = null;
	var max = null;
	var ticks = [];

	if (this.currentRangeType === this.RANGE_TYPE_HOUR) {
		min = -1;
		max = 60;
		for (var i = 0; i < 12; i++) {
			var tickLabel = moment(startDt).add('m', i*5).format('h:mma');
			ticks.push([i*5, tickLabel]);
		};
	} else if (this.currentRangeType === this.RANGE_TYPE_DAY || this.currentRangeType === this.RANGE_TYPE_NIGHT) {
		min = -1;
		max = 24;
		
		for (var i = 0; i < 12; i++) {
			var tickLabel = moment(startDt).add('h', i*2).format('ha');
			ticks.push([i*2, tickLabel]);
		};
	} else if (this.currentRangeType === this.RANGE_TYPE_WEEK) {
		min = -1;
		max = 7;
		var tickLabels = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
		for (var i = 0; i < tickLabels.length; i++) {
			ticks.push([i, tickLabels[i]]);
		};
	} else if (this.currentRangeType === this.RANGE_TYPE_MONTH) {
		var dayOfEndOfMonth = moment(startDt).endOf('month').date();
		min = -1;
		max = dayOfEndOfMonth+1;
		for (var i = 0; i < max; i++) {
			ticks.push([i, i+1]);
		};
	} else if (this.currentRangeType === this.RANGE_TYPE_YEAR) {
		min = -1;
		max = 12;
		for (var i = 0; i < max; i++) {
			var tickLabel = moment(startDt).add('M', i).format('MMM');
			ticks.push([i, tickLabel]);
		}
	}

	this.currentXaxisOptions = {min: min, max: max, ticks: ticks};
}

Graph.prototype.updateCurrentDt = function (newDt) {
	this.currentDt = newDt;
	this.getSourceReadings();
}

Graph.prototype.updateCurrentRangeType = function (newRangeType) {
	this.currentRangeType = newRangeType;
	this.getSourceReadings();
}

Graph.prototype.selectSystem = function (node) {
	if (node === this.currentSelectedSystem) {
		return;
	}

	this.currentSelectedSystem = node;
	this.getSourceReadings();
}

Graph.prototype.goPrevOrNext = function (direction) {
	var delta = (direction === 'prev') ? -1 : 1;
	if (this.currentRangeType === this.RANGE_TYPE_HOUR) {
		this.currentDt.add('h', delta);
	} else if (this.currentRangeType === this.RANGE_TYPE_DAY || this.currentRangeType === this.RANGE_TYPE_NIGHT) {
		this.currentDt.add('d', delta);
	} else if (this.currentRangeType === this.RANGE_TYPE_WEEK) {
		this.currentDt.add('w', delta);
	} else if (this.currentRangeType === this.RANGE_TYPE_MONTH) {
		this.currentDt.add('M', delta);
	} else if (this.currentRangeType === this.RANGE_TYPE_YEAR) {
		this.currentDt.add('y', delta);
	}
	this.getSourceReadings();
}

Graph.prototype.goPrev = function () {
	this.goPrevOrNext('prev');
}

Graph.prototype.goNext = function () {
	this.goPrevOrNext('next');
}
