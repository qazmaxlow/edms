function EnergySummary() {}

EnergySummary.prototype.getSummaryWithSystem = function(entrakSystem, getSummaryCallback) {
	var sourceIds = entrakSystem.getAllSourceIds();
	this.getSummaryWithSourceIds(sourceIds, getSummaryCallback);
}

EnergySummary.prototype.getSummaryWithSourceIds = function(sourceIds, getSummaryCallback) {
	var energySummaryThis = this;
	var uptilMoment = Utils.getNowMoment();
	var startDt = moment(uptilMoment).startOf('day');
	var lastStartDt = moment(startDt).subtract('w', 1);
	var lastEndDt = moment(uptilMoment).subtract('w', 1);

	$.ajax({
		type: "POST",
		url: "../summary/",
		data: {
			source_ids: JSON.stringify(sourceIds),
			start_dt: startDt.unix(),
			end_dt: uptilMoment.unix(),
			last_start_dt: lastStartDt.unix(),
			last_end_dt: lastEndDt.unix(),
		},
	}).done(function(data) {
		energySummaryThis.realtimeConsumption = data.realtime;
		energySummaryThis.lastConsumption = data.last;
		getSummaryCallback();
	});
}

EnergySummary.prototype.assignSummaryToHtml = function(lastValSel, currentValSel, percentNumSel, imgSel, mediaUrlPrefix) {
	$(lastValSel).text(Utils.formatWithCommas(this.lastConsumption.toFixed(0)));
	$(currentValSel).text(Utils.formatWithCommas(this.realtimeConsumption.toFixed(0)));

	var diffPercentage = Utils.fixed1DecIfLessThan10((Math.abs(this.realtimeConsumption - this.lastConsumption)/this.lastConsumption)*100);
	$(percentNumSel).text(diffPercentage);

	var summaryBgImg = null;
	if (this.lastConsumption > this.realtimeConsumption) {
		summaryBgImg = mediaUrlPrefix+'images/summary-lower.png';
	} else if (this.lastConsumption < this.realtimeConsumption) {
		summaryBgImg = mediaUrlPrefix+'images/summary-higher.png';
	} else {
		summaryBgImg = mediaUrlPrefix+'images/summary-neutral.png';
	}
	$(imgSel).css("background-image", 'url(' + summaryBgImg + ')');
}