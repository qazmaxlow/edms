function Graph(graphEleSel, sourceChoiceEleSel, yAxisSliderEleSel) {
	this.graphEleSel = graphEleSel;
	this.sourceChoiceEleSel = sourceChoiceEleSel;
	this.yAxisSliderEleSel = yAxisSliderEleSel;

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
}

Graph.prototype.RANGE_TYPE_HOUR		= 'hour';
Graph.prototype.RANGE_TYPE_DAY		= 'day';
Graph.prototype.RANGE_TYPE_NIGHT	= 'night';
Graph.prototype.RANGE_TYPE_WEEK		= 'week';
Graph.prototype.RANGE_TYPE_MONTH	= 'month';
Graph.prototype.RANGE_TYPE_YEAR		= 'year';

Graph.prototype.API_RANGE_TYPES = {
	'hour': 'hour',
	'day': 'day',
	'night': 'day',
	'week': 'week',
	'month': 'month',
	'year': 'year',
};

Graph.prototype.UNIT_KWH = 'kwh';

Graph.prototype.getSourceReadings = function () {
	var graphThis = this;
	var startEndDt = this.genStartEndDtStamp();
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
		for (var sourceId in data) {
			var systemNode = graphThis.findSystemNodeBySourceId(sourceId);
			systemNode.data.sources[sourceId]['data'] = {};
			$.each(data[sourceId], function(readingTimestamp, value) {
				systemNode.data.sources[sourceId]['data'][readingTimestamp] = value;
			})
		}

		graphThis.updateXAxisOptions(startEndDt.startDt);
		graphThis.transformReadingToChartDatasets();
		graphThis.plotGraph();
	});
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
			value -= 24;
		};
	} else if (this.currentRangeType === this.RANGE_TYPE_WEEK) {
		value = value_dt.day();
	} else if (this.currentRangeType === this.RANGE_TYPE_MONTH) {
		value = value_dt.date();
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

	this.plot.getOptions().series.grow.active = false;
	this.plot.setData(willPlotSeries);
	this.plot.setupGrid();
	this.plot.draw();
	this.plot.getOptions().series.grow.active = true;

	this.refreshYAxisSlider();
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

		var series = {
			label: source.name,
			lines: sourceLineOptions,
			data: [],
		};
		$.each(source.data, function(readingTimestamp, readingVal) {
			var transformedVal = graphThis.transformReading(source, readingTimestamp, readingVal);
			series.data.push([graphThis.transformXCoordinate(readingTimestamp), transformedVal]);
		});
		this.sourceDatasets.push(series);
	}

	for (var childrenIdx in tree.children) {
		var subTree = tree.children[childrenIdx];
		var series = {};
		series.label = subTree.data.name;
		series.lines = sourceLineOptions;
		series.data = [];
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

	this.totalSeries = {
		label: 'Total',
		bars: {
			barWidth: 0.4,
			align: "center",
			show: true,
		},
		data: [],
	};
	for (var readingTimestamp in totalReadings) {
		this.totalSeries.data.push([graphThis.transformXCoordinate(readingTimestamp), totalReadings[readingTimestamp]]);
	}
}

Graph.prototype.plotGraph = function () {
	this.plot = $(this.graphEleSel).plot([this.totalSeries], {
		series: {
	        grow: {
	            active: true,
	            duration: 800,
	        }
	    },
	    xaxis: {
	    	min: this.currentXaxisOptions.min,
	    	max: this.currentXaxisOptions.max,
	    	ticks: this.currentXaxisOptions.ticks,
	    }
	}).data("plot");
	this.setupSourceChoice();
	this.refreshYAxisSlider();
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
		var willPlotSeries = [graphThis.totalSeries];

		choiceContainer.find("input:checked").each(function () {
			var seriesIdx = parseInt($(this).attr("series_idx"), 10);
			willPlotSeries.push(graphThis.sourceDatasets[seriesIdx]);
		});

		graphThis.plot.getOptions().series.grow.active = false;
		graphThis.plot.setData(willPlotSeries);
		graphThis.plot.setupGrid();
		graphThis.plot.draw();
		graphThis.plot.getOptions().series.grow.active = true;
	});
}

Graph.prototype.refreshYAxisSlider = function () {
	var graphThis = this;
	var currentYMax = this.plot.getAxes().yaxis.max;
	var yMin = currentYMax*0.25;
	var yMax = currentYMax*1.75;
	var step = (yMax-yMin)/1000;
	$(this.yAxisSliderEleSel).slider("option", {
		min: yMin,
		max: yMax,
		step: step,
		value: currentYMax,
	}).off("slide")
	.on("slide", function(event, ui) {
		graphThis.plot.getAxes().yaxis.options.max = Math.round(ui.value);
		graphThis.plot.setupGrid();
		graphThis.plot.draw();
	});
}

Graph.prototype.genStartEndDtStamp = function () {
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
	} else if (this.currentRangeType === this.RANGE_TYPE_DAY) {
		min = -1;
		max = 24;
		
		for (var i = 0; i < 12; i++) {
			var tickLabel = moment(startDt).add('h', i*2).format('ha');
			ticks.push([i*2, tickLabel]);
		};
	} else if (this.currentRangeType === this.RANGE_TYPE_NIGHT) {
		min = -13;
		max = 12;

		for (var i = 0; i < 12; i++) {
			var tickLabel = moment(startDt).add('h', i*2).format('ha');
			ticks.push([(i*2)-12, tickLabel]);
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
		min = 0;
		max = dayOfEndOfMonth+2;
		for (var i = 0; i < max; i++) {
			ticks.push([i, i]);
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
