function EnergySummary() {}

EnergySummary.prototype.getSummaryWithSystem = function(entrakSystem, getSummaryCallback) {
    var sourceIds = entrakSystem.getAllSourceIds();
    this.getSummaryWithSourceIds(sourceIds, getSummaryCallback);
}

EnergySummary.prototype.getSummaryWithSourceIds = function(sourceIds, getSummaryCallback) {
    var energySummaryThis = this;
    var uptilMoment = Utils.getNowMoment();
    var startDt = moment(uptilMoment).startOf('month');
    var lastStartDt = moment(startDt).subtract(1, 'M');
    var lastEndDt = moment(uptilMoment).subtract(1, 'M');

    $.ajax({
        type: "POST",
        url: "../measures/show_summary/",
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

    var diffPercentage = Utils.fixedDecBaseOnVal((Math.abs(this.realtimeConsumption - this.lastConsumption)/this.lastConsumption)*100);
    $(percentNumSel).text(diffPercentage);
}
