function ReportGenerator(systemTree, timezone, reportType, multiLangTexts) {
    this.systemTree = systemTree;
    this.timezone = timezone;
    this.reportType = reportType;
    this.groupedSourceInfos = null;
    this.savingInfo = null;
    this.holidays = null;
    this.sumUpUsages = null;
    this.currentDt = null;
    this.currentEndDt = null;
    this.isPdf = false;

    var firstRecordDt = moment.unix(this.systemTree.data.firstRecord).tz(this.timezone);
    if (firstRecordDt.date() === 1) {
        this.beginningStartDt = moment(firstRecordDt).startOf('M');
    } else {
        this.beginningStartDt = moment(firstRecordDt).add(1, 'M').startOf('M');
    }

    this.multiLangTexts = multiLangTexts;
};

ReportGenerator.REPORT_TYPE_MONTH = 'month';
ReportGenerator.REPORT_TYPE_YEAR = 'year';
ReportGenerator.REPORT_TYPE_QUARTER = 'quarter';
ReportGenerator.REPORT_TYPE_CUSTOM_MONTH = 'custom-month';
ReportGenerator.REPORT_TYPE_WEEK = 'week';

ReportGenerator.MAX_PERCENTAGE_VALUE = 5;
ReportGenerator.DONUT_COLORS = ['#68C0D4', '#8C526F', '#D5C050', '#8B8250', '#5759A7', '#6EC395',
    '#EE9646', '#EE5351', '#178943', '#BA1E6A', '#045A6F', '#0298BB'];
ReportGenerator.OTHER_PERCENT_COLOR = '#D55398'
ReportGenerator.OTHER_INFO_COLOR = '#5E5E5E';
ReportGenerator.FIRST_SPLIT_PIE_COLOR = '#7ACB39';
ReportGenerator.SECOND_SPLIT_PIE_COLOR = '#3F952C';

ReportGenerator.MAIN_SERIES_BASE_OPTIONS = {
    lines: {
        lineWidth: 2.5,
        show: true,
    },
    points: {
        radius: 4,
        symbol: 'circle',
        show: true,
    },
};
ReportGenerator.MAIN_PLOT_OPTIONS = {
    legend: {
        show: true,
        noColumns: 2,
        backgroundColor: "#F4F3F4",
    },
    yaxis: {
        font: {
            size: 12,
            weight: "bold",
            family: "sans-serif",
            color: "#5B5B5B"
        },
    },
    xaxis: {
        tickLength: 0,
        font: {
            size: 12,
            weight: "bold",
            family: "sans-serif",
            color: "#5B5B5B"
        },
    },
    grid: {
        borderWidth: {
            'top': 0,
            'right': 0,
            'bottom': 2,
            'left': 2,
        },
        borderColor: {
            'bottom': "#FFFFFF",
            'left': "#FFFFFF",
        },
    },
}

ReportGenerator.SUB_INFO_SERIES_BASE_OPTIONS = {
    lines: {
        lineWidth: 1.5,
        show: true,
    },
};
ReportGenerator.SUB_INFO_PLOT_OPTIONS = {
    legend: {
        show: true,
        noColumns: 2,
        backgroundColor: "#F4F3F4",
    },
    yaxis: {
        font: {
            size: 10,
            weight: "bold",
            family: "sans-serif",
            color: "#5B5B5B"
        },
    },
    xaxis: {
        tickLength: 0,
        font: {
            size: 10,
            weight: "bold",
            family: "sans-serif",
            color: "#5B5B5B"
        },
    },
    grid: {
        borderWidth: {
            'top': 0,
            'right': 0,
            'bottom': 2,
            'left': 2,
        },
        borderColor: {
            'bottom': "#FFFFFF",
            'left': "#FFFFFF",
        },
    },
}

ReportGenerator.LINE_CHART_CURRENT_COLOR = "#047FA1";
ReportGenerator.LINE_CHART_LAST_COLOR = "#EDBA3C";

ReportGenerator.prototype.genDtText = function(targetDt, endDt) {
    var currentDtName = "";
    if (this.reportType === ReportGenerator.REPORT_TYPE_MONTH) {
        currentDtName = targetDt.format(this.multiLangTexts.reportTypeMonthDtFormat);
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_YEAR) {
        currentDtName = targetDt.format(this.multiLangTexts.reportTypeYearDtFormat);
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_QUARTER) {
        currentDtName = targetDt.format(this.multiLangTexts.reportTypeYearDtFormat)+' Q'+this.getQuarterIdx(this.currentDt);
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_CUSTOM_MONTH) {
        if (endDt === undefined || endDt === null) {
            currentDtName = targetDt.format(this.multiLangTexts.reportTypeCustomMonthDtFormat);
        } else {
            currentDtName = targetDt.format(this.multiLangTexts.reportTypeCustomMonthDtFormat)
                +this.multiLangTexts.genDtTo
                +endDt.format(this.multiLangTexts.reportTypeCustomMonthDtFormat);
        }
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_WEEK) {
        currentDtName = targetDt.format(this.multiLangTexts.reportTypeWeekDtFormat);
        currentDtName += this.multiLangTexts.genDtTo + moment(targetDt).add(1, 'w').format(this.multiLangTexts.reportTypeWeekDtFormat);
    }

    return currentDtName;
}

ReportGenerator.prototype.genReportName = function() {
    var reportName = this.genDtText(this.currentDt, this.currentEndDt);
    if (this.langCode === 'zh-tw') {
        reportName += " 能源使用報告";
    } else {
        if (this.reportType === ReportGenerator.REPORT_TYPE_MONTH
            || this.reportType === ReportGenerator.REPORT_TYPE_CUSTOM_MONTH) {
            reportName += " - Monthly Energy Report";
        } else if (this.reportType === ReportGenerator.REPORT_TYPE_YEAR) {
            reportName += " - Yearly Energy Report";
        } else if (this.reportType === ReportGenerator.REPORT_TYPE_QUARTER) {
            reportName += " - Quarterly Energy Report";
        } else if (this.reportType === ReportGenerator.REPORT_TYPE_WEEK) {
            reportName += " - Weekly Energy Report";
        }
    }

    return reportName;
}

ReportGenerator.prototype.getQuarterIdx = function(targetDt) {
    return (targetDt.month()/3) + 1;
}

ReportGenerator.prototype.genEndDt = function(startDt, targetReportType) {
    var endDt;
    if (targetReportType === ReportGenerator.REPORT_TYPE_MONTH) {
        endDt = moment(startDt).add(1, 'M');
    } else if (targetReportType === ReportGenerator.REPORT_TYPE_YEAR) {
        endDt = moment(startDt).add(1, 'Y');
    } else if (targetReportType === ReportGenerator.REPORT_TYPE_QUARTER) {
        endDt = moment(startDt).add(3, 'M');
    } else if (targetReportType === ReportGenerator.REPORT_TYPE_WEEK) {
        endDt = moment(startDt).add(1, 'w');
    }

    return endDt;
}

ReportGenerator.prototype.updateDtInfo = function(startDt, customEndDt) {
    this.currentDt = startDt;
    if (this.reportType === ReportGenerator.REPORT_TYPE_CUSTOM_MONTH) {
        this.currentEndDt = moment(customEndDt).add(1, 'd');
    } else {
        this.currentEndDt = this.genEndDt(this.currentDt, this.reportType);
    }
}

ReportGenerator.prototype.getReportData = function(callbackFunc) {
    var reportGenThis = this;

    var requestData = {
        report_type: this.reportType,
        start_timestamp: this.currentDt.unix(),
        end_timestamp: this.currentEndDt.unix(),
    }

    $.ajax({
        type: "POST",
        url: "../report_data/",
        data: requestData,
    }).done(function(data) {
        callbackFunc(data);
    }).fail(function(jqXHR, textStatus) {
        console.log(jqXHR.responseText);
    });
}

ReportGenerator.prototype.genLastDt = function(targetDt, dayDiff) {
    var result;
    if (this.reportType === ReportGenerator.REPORT_TYPE_MONTH) {
        result = moment(targetDt).subtract(1, 'M');
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_YEAR) {
        result = moment(targetDt).subtract(1, 'y');
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_QUARTER) {
        result = moment(targetDt).subtract(3, 'M');
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_CUSTOM_MONTH) {
        result = moment(targetDt).subtract(dayDiff, 'd');
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_WEEK) {
        result = moment(targetDt).subtract(1, 'w');
    }

    return result;
}

ReportGenerator.prototype.genConsecutiveLasts = function(numOfLast, startDt, dayDiff) {
    var result = [];
    result.push(startDt.unix());
    var nextDt = startDt;
    for (var i = 0; i < numOfLast; i++) {
        nextDt = this.genLastDt(nextDt, dayDiff);
        result.push(nextDt.unix());
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
    this.sumUpUsages = data.sumUpUsages;
    this.overnightStartDt = moment().hour(data.overnightStartHr).minute(data.overnightStartMin);
    this.overnightEndDt = moment().hour(data.overnightEndHr).minute(data.overnightEndMin);
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

ReportGenerator.prototype.getReportTypeName = function() {
    var reportTypeName;
    if (this.reportType === ReportGenerator.REPORT_TYPE_MONTH
        || this.reportType === ReportGenerator.REPORT_TYPE_CUSTOM_MONTH) {
        reportTypeName = this.multiLangTexts.reportTypeNameMonth;
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_YEAR) {
        reportTypeName = this.multiLangTexts.reportTypeNameYear;
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_QUARTER) {
        reportTypeName = this.multiLangTexts.reportTypeNameQuarter;
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_WEEK) {
        reportTypeName = this.multiLangTexts.reportTypeNameWeek;
    }

    return reportTypeName;
}

ReportGenerator.prototype.updateReportInnerText = function() {
    var reportTypeName = this.getReportTypeName();

    $(".report-type-name").text(reportTypeName.toUpperCase());
    $(".report-type-name-lower").text(reportTypeName);
    if (this.langCode === 'en') {
        $(".report-type-name-lower-plural").text(reportTypeName+'s');
    } else {
        $(".report-type-name-lower-plural").text(reportTypeName);
    }
}

ReportGenerator.prototype.generateFullReport = function() {
    this.updateReportInnerText();

    this.generateKeyStatistics();
    this.generateComparePast();

    var combinedCurrentReadings = {};
    $.each(this.groupedSourceInfos, function(groupIdx, info) {
        $.each(info.currentReadings, function(timestamp, readingVal) {
            combinedCurrentReadings[timestamp] = ((timestamp in combinedCurrentReadings) ? combinedCurrentReadings[timestamp] : 0)
                + readingVal; 
        });
    });

    this.generateWeekdayReport(combinedCurrentReadings);
    this.generateWeekendReport(combinedCurrentReadings);

    var combinedOvernightCurrentReadings = {};
    $.each(this.groupedSourceInfos, function(groupIdx, info) {
        $.each(info.overnightcurrentReadings, function(timestamp, readingVal) {
            combinedOvernightCurrentReadings[timestamp] = 
                ((timestamp in combinedOvernightCurrentReadings) ? combinedOvernightCurrentReadings[timestamp] : 0)
                + readingVal; 
        });
    });
    this.generateOvernightReport(combinedOvernightCurrentReadings);

    if (this.reportType === ReportGenerator.REPORT_TYPE_YEAR
        || this.reportType === ReportGenerator.REPORT_TYPE_QUARTER
        || this.reportType === ReportGenerator.REPORT_TYPE_WEEK) {
        if (this.reportType === ReportGenerator.REPORT_TYPE_YEAR) {
            $(".compare-last-same-period").hide();
        } else {
            $(".compare-last-same-period").show();
        }
        $(".calendar-vertical-info").show();

        $(".calendar-info-container").hide();
        $(".calendar-bottom-info").hide();
        $(".bottom-info-separator").hide();
    } else {
        $(".compare-last-same-period").show();
        $(".calendar-info-container").show();
        $(".calendar-bottom-info").show();
        $(".bottom-info-separator").show();

        $(".calendar-vertical-info").hide();
    }
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
    $("#current-co2-usage").html(Utils.formatWithCommas((totalCo2Usage/1000).toFixed(0)) + this.multiLangTexts.tons);
    $("#current-money-usage").text(Utils.formatWithCommas("$ " + totalMoneyUsage.toFixed(0)));

    var positiveOrNegativePrefix, carImpactSuffix, carImpactSubText, forestImpactSubText, pandaImpactSubText;
    if (reportGenThis.savingInfo.energy >= 0) {
        $(".basic-info-container").addClass('positive-saving');
        $(".basic-info-container").removeClass('negative-saving');
        positiveOrNegativePrefix = "-";
        savedMoneySubText = "in savings";
        if (this.langCode === 'zh-tw') {
            carImpactSuffix = '減少';
            carImpactSubText = "在馬路上不停行走一";
            forestImpactSubText = "保護了熱帶雨林";
            pandaImpactSubText = "減少排放二氧化碳的重量，等於";
        } else {
            carImpactSubText = "taken off the road for a ";
            forestImpactSubText = "of tropical rainforest protected";
            pandaImpactSubText = "Reduced CO<sub>2</sub> emissions equal to the weight of";
        }
    } else {
        $(".basic-info-container").addClass('negative-saving');
        $(".basic-info-container").removeClass('positive-saving');
        positiveOrNegativePrefix = "+";
        savedMoneySubText = "extra spending";
        if (this.langCode === 'zh-tw') {
            carImpactSuffix = '增加';
            carImpactSubText = "在馬路上不停行走一";
            forestImpactSubText = "砍伐了熱帶雨林";
            pandaImpactSubText = "額外排放二氧化碳的重量，等於";
        } else {
            carImpactSubText = "more on the road for a ";
            forestImpactSubText = "of tropical rainforest cut down";
            pandaImpactSubText = "Extra CO<sub>2</sub> emissions equal to the weight of";
        }
    }
    var savedEnergyText = Utils.formatWithCommas(Math.abs(Utils.fixedDecBaseOnVal(reportGenThis.savingInfo.energy)))
        + "<span class='basic-info-percent-symbol'>%</span> ";
    savedEnergyText = positiveOrNegativePrefix + savedEnergyText;
    $("#save-energy-usage").html(savedEnergyText);

    // baseline should be just before first record
    var firstRecordMonth = moment.unix(this.systemTree.data.firstRecord).tz(this.timezone).startOf('M');
    var compareToDt = moment(this.currentDt).year(firstRecordMonth.year());
    if (compareToDt >= firstRecordMonth) {
        compareToDt.subtract(1, 'y');
    }

    var savedCo2Text = Utils.formatWithCommas((Math.abs(reportGenThis.savingInfo.co2)/1000).toFixed(0));
    savedCo2Text = positiveOrNegativePrefix + savedCo2Text + this.multiLangTexts.tonsCo2;
    $("#save-co2-usage").html(savedCo2Text);
    var savedMoneyText = "$ " + Utils.formatWithCommas(Math.abs(reportGenThis.savingInfo.money).toFixed(0));
    savedMoneyText = positiveOrNegativePrefix + savedMoneyText;
    $("#save-money-usage").text(savedMoneyText);

    var co2InCar = Utils.formatWithCommas(Math.abs((reportGenThis.savingInfo.co2*0.003).toFixed(0)));
    if (this.langCode === 'zh-tw') {
        $("#car-impact").text(carImpactSuffix + co2InCar + "輛車");
    } else {
        $("#car-impact").text(co2InCar + " cars");
    }
    carImpactSubText += this.getReportTypeName();
    $("#car-impact-subtext").text(carImpactSubText);
    var co2InForest = Utils.formatWithCommas(Math.abs((reportGenThis.savingInfo.co2*0.016).toFixed(0)));
    $("#forest-impact").text(co2InForest + this.multiLangTexts.mSquare);
    $("#forest-impact-subtext").text(forestImpactSubText);
    var co2InElephant = Utils.formatWithCommas(Math.abs((reportGenThis.savingInfo.co2*0.00667).toFixed(0)));
    $("#panda-impact").text(co2InElephant + this.multiLangTexts.pandas);
    $("#panda-impact-subtext").html(pandaImpactSubText);

    var transformedDatas = [];
    var energyPercentSum = 0;
    $.each(reportGenThis.groupedSourceInfos, function(infoIdx, info) {
        var dataInfo = {
            totalEnergy: info.currentTotalEnergy,
            co2Val: info.currentTotalCo2,
            moneyVal: info.currentTotalMoney
        };
        dataInfo.name = (info.systemCode === reportGenThis.systemTree.data.code) ? info.sourceNameInfo[reportGenThis.langCode] : info.system.data.nameInfo[reportGenThis.langCode];
        if (infoIdx < reportGenThis.groupedSourceInfos.length-1) {
            dataInfo.energyPercent = parseFloat(Utils.fixedDecBaseOnVal((info.currentTotalEnergy/totalEnergyUsage)*100));
            energyPercentSum += dataInfo.energyPercent;
        } else {
            dataInfo.energyPercent = parseFloat(Utils.fixedDecBaseOnVal(100-energyPercentSum));
        }
        transformedDatas.push(dataInfo);
    });

    transformedDatas.sort(function(a, b) {
        return b.totalEnergy-a.totalEnergy;
    });

    var keyRowTemplate = $("#key-statistics-row-template").html();
    Mustache.parse(keyRowTemplate);

    var keyStatSubDataContainer = $("#key-statistic-sub-data");
    keyStatSubDataContainer.empty();
    $.each(transformedDatas, function(dataIdx, dataInfo) {
        var templateInfo = {
            energyVal: dataInfo.totalEnergy,
            co2Val: dataInfo.co2Val,
            moneyVal: dataInfo.moneyVal
        };
        $.each(templateInfo, function(key, value) {
            templateInfo[key] = Utils.formatWithCommas(value.toFixed(0));
        });

        templateInfo.usageTypeName = dataInfo.name;

        if (dataInfo.energyPercent < ReportGenerator.MAX_PERCENTAGE_VALUE) {
            templateInfo.extraClass = 'other-key-statistics-row';
        }

        var rowHtml = Mustache.render(keyRowTemplate, templateInfo);
        keyStatSubDataContainer.append(rowHtml);
    });

    var plotData = [];
    var otherPercent = 0;
    $.each(transformedDatas, function(dataIdx, dataInfo) {
        if (dataInfo.energyPercent >= ReportGenerator.MAX_PERCENTAGE_VALUE) {
            var matchColor = ReportGenerator.DONUT_COLORS[dataIdx%ReportGenerator.DONUT_COLORS.length];
            plotData.push({
                label: dataInfo.energyPercent,
                data: dataInfo.energyPercent,
                color: matchColor,
            });
        } else {
            otherPercent += dataInfo.energyPercent;
        }
    });
    var otherPercentIdx = null;
    if (otherPercent !== 0) {
        otherPercent = otherPercent.toFixed(1);
        otherPercentIdx = plotData.length;
        plotData.push({
            label: otherPercent,
            data: otherPercent,
            color: ReportGenerator.OTHER_PERCENT_COLOR,
        });
    }

    $.plot("#energy-donut", plotData, {
        series: {
            pie: {
                show: true,
                radius: 0.6,
                innerRadius: 0.3,
                stroke: {
                    width: 0
                },
                label: {
                    radius: 0.85,
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
    if (otherPercentIdx !== null) {
        $('.pieLabel:eq('+otherPercentIdx+')').css('color', ReportGenerator.OTHER_PERCENT_COLOR);
    }

    var keySubInfoTemplate = $("#key-percent-sub-info-template").html();
    Mustache.parse(keySubInfoTemplate);
    var legendContainer;
    if (this.isPdf) {
        legendContainer = $('.donut-legend-container-left');
    } else {
        legendContainer = $('.donut-legend-container-center');
    }
    legendContainer.empty();
    var alreadyInsertOther = false;
    $.each(transformedDatas, function(dataIdx, dataInfo) {
        var templateInfo = {
            name: dataInfo.name,
            percentVal: dataInfo.energyPercent,
        };

        if (dataInfo.energyPercent >= ReportGenerator.MAX_PERCENTAGE_VALUE) {
            var matchColor = ReportGenerator.DONUT_COLORS[dataIdx%ReportGenerator.DONUT_COLORS.length];
            templateInfo.color = matchColor;
            templateInfo.namePrefix = '• ';
        } else {
            if (!alreadyInsertOther) {
                var otherTemplateInfo = {
                    color: ReportGenerator.OTHER_PERCENT_COLOR,
                    namePrefix: '• ',
                    name: 'Other',
                    percentVal: otherPercent,
                };

                var otherInfoHtml = Mustache.render(keySubInfoTemplate, otherTemplateInfo);
                legendContainer.append(otherInfoHtml);

                alreadyInsertOther = true;
            }

            templateInfo.color = ReportGenerator.OTHER_INFO_COLOR;
            templateInfo.extraClass = 'other-sub-info';
        }

        if (reportGenThis.isPdf
            && ($('.donut-legend-container-left .key-percent-sub-info').length >= 10) ) {
            legendContainer = $('.donut-legend-container-right');
        }

        var subInfoHtml = Mustache.render(keySubInfoTemplate, templateInfo);
        legendContainer.append(subInfoHtml);
    });
}

ReportGenerator.prototype.transformXCoordinate = function(timestamp, startDt) {
    var result;
    if (this.reportType === ReportGenerator.REPORT_TYPE_MONTH) {
        result = moment.unix(timestamp).tz(this.timezone).date();
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_YEAR) {
        result = moment.unix(timestamp).tz(this.timezone).dayOfYear();
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_QUARTER
        || this.reportType === ReportGenerator.REPORT_TYPE_CUSTOM_MONTH) {
        result = moment.unix(timestamp).tz(this.timezone).diff(startDt, 'days');
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_WEEK) {
        result = moment.unix(timestamp).tz(this.timezone).day();
    }

    return result;
}

ReportGenerator.prototype.genCompareSeriesFromReadings = function(readings, options, label, color, startDt) {
    var reportGenThis = this;
    var series = $.extend(true, {data: []}, options);
    $.each(readings, function(timestamp, value) {
        series.data.push([reportGenThis.transformXCoordinate(timestamp, startDt), value]);
    });
    series.data.sort(function (a, b) {
        return a[0]-b[0];
    });
    series.label = label;
    series.color = color;
    if ("points" in series) {
        series.points.fillColor = color;
    }

    return series;
}

ReportGenerator.prototype.genXAxisOptions = function() {
    options = {ticks: []};
    if (this.reportType === ReportGenerator.REPORT_TYPE_MONTH) {
        options.min = 0;
        options.max = 32;
        for (var i = options.min; i < options.max-1; i+=2) {
            options.ticks.push([i, i]);
        }
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_YEAR) {
        options.min = 0;
        options.max = 366;
        for (var i = options.min; i < options.max-1; i+=30) {
            options.ticks.push([i, i]);
        }
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_QUARTER) {
        var dayDiff = this.currentEndDt.diff(this.currentDt, 'days');
        options.min = -1;
        options.max = dayDiff + 2;
        for (var i = 0; i < 3; i++) {
            var tickDt = moment(this.currentDt).add(i, 'M');
            var tickDtDayDiff = tickDt.diff(this.currentDt, 'days');
            options.ticks.push([tickDtDayDiff, tickDt.format('MMM D')]);
            tickDt.date(15);
            options.ticks.push([tickDtDayDiff+14, tickDt.format('MMM D')]);
        }
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_CUSTOM_MONTH) {
        var dayDiff = this.currentEndDt.diff(this.currentDt, 'days');
        options.min = -1;
        options.max = dayDiff + 1;
        for (var i = 0; i < dayDiff; i++) {
            var tickDt = moment(this.currentDt).add(i, 'd');
            if (tickDt.date() === 1 || tickDt.date()%5 === 0 && tickDt.date() !== 30) {
                options.ticks.push([i, tickDt.format('MMM D')]);
            }
        }
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_WEEK) {
        options.min = -1;
        options.max = 7;
        var weekTexts = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        for (var i = 0; i < 7; i++) {
            options.ticks.push([i, weekTexts[i]]);
        }
    }

    return options;
}

ReportGenerator.prototype.genComparePastLabel = function(targetDt) {
    var result;

    if (this.reportType === ReportGenerator.REPORT_TYPE_MONTH) {
        result = targetDt.format("MMM");
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_YEAR) {
        result = targetDt.format("YYYY");
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_QUARTER) {
        result = targetDt.format("YYYY ")+'Q'+this.getQuarterIdx(targetDt);
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_CUSTOM_MONTH
        || this.reportType === ReportGenerator.REPORT_TYPE_WEEK) {
        result = targetDt.format(this.multiLangTexts.comparePastLabelFormat);
    }

    return result;
}

ReportGenerator.prototype.plotCompareLineChart = function(targetEleSel, currentReadings, lastReadings, plotOptions, seriesOptions) {
    var reportGenThis = this;

    var currentSeries = this.genCompareSeriesFromReadings(currentReadings,
        seriesOptions,
        this.genComparePastLabel(this.currentDt),
        ReportGenerator.LINE_CHART_CURRENT_COLOR,
        this.currentDt);
    var dayDiff = null;
    if (this.reportType === ReportGenerator.REPORT_TYPE_CUSTOM_MONTH) {
        dayDiff = this.currentEndDt.diff(this.currentDt, 'days');
    }
    var lastSeries = this.genCompareSeriesFromReadings(lastReadings,
        seriesOptions,
        this.genComparePastLabel(this.genLastDt(this.currentDt, dayDiff)),
        ReportGenerator.LINE_CHART_LAST_COLOR,
        this.genLastDt(this.currentDt, dayDiff));

    var xAxisOptions = this.genXAxisOptions();
    plotOptions.xaxis.min = xAxisOptions.min;
    plotOptions.xaxis.max = xAxisOptions.max;
    plotOptions.xaxis.ticks = xAxisOptions.ticks;

    $(targetEleSel).empty();
    $(targetEleSel).plot([lastSeries, currentSeries], plotOptions);
}

ReportGenerator.prototype.insertEmptyBlock = function(targetEleSel, blockClass) {
    var emptyBlockTemplate = $("#empty-block-template").html();
    Mustache.parse(emptyBlockTemplate);

    var templateInfo = {blockClass: blockClass};
    var emptyBlockHtml = Mustache.render(emptyBlockTemplate, templateInfo);

    $(targetEleSel).append(emptyBlockHtml);
}

ReportGenerator.prototype.insertComparePastSubInfo = function(template, info, classIdentifier) {
    var titleText, infoClass;
    if (info.lastTotalEnergy === 0) {
        titleText = "-";
        infoClass = "invalid-saving";
    } else {
        if (pastDiffPercent >= 0) {
            infoClass = "negative-saving";
        } else {
            infoClass = "positive-saving";
        }

        if (this.langCode === 'zh-tw') {
            titleText = this.multiLangTexts.overall;
            var pastDiffPercent = (info.currentTotalEnergy-info.lastTotalEnergy)/info.lastTotalEnergy*100;
            titleText += "比上"+this.getReportTypeName();

            if (pastDiffPercent >= 0) {
                titleText += "多用";
            } else {
                titleText += "少用";
            }
            titleText += parseFloat(Utils.fixedDecBaseOnVal(Math.abs(pastDiffPercent))) + '%';
        } else {
            titleText = this.multiLangTexts.overall;
            var pastDiffPercent = (info.currentTotalEnergy-info.lastTotalEnergy)/info.lastTotalEnergy*100;
            titleText += parseFloat(Utils.fixedDecBaseOnVal(Math.abs(pastDiffPercent)));

            if (pastDiffPercent >= 0) {
                titleText += "% more";
            } else {
                titleText += "% less";
            }
            titleText += " energy than last "+this.getReportTypeName();
        }
    }

    var name = ("sourceNameInfo" in info) ? info.sourceNameInfo[this.langCode] : info.system.data.nameInfo[this.langCode];
    name = name.toUpperCase();

    var templateInfo = {
        classIdentifier: classIdentifier,
        name: name,
        lineChartTitle: titleText,
        infoClass: infoClass,
        dayOfThe: this.getReportTypeName(),
    };

    var subInfoHtml = Mustache.render(template, templateInfo);
    $(".compare-past-sub-info-container").append(subInfoHtml);
}

ReportGenerator.prototype.generateComparePast = function() {
    var reportGenThis = this;
    var currentTotalUsage = this.sumUpUsages[0];
    var lastTotalUsage = this.sumUpUsages[1];
    var pastDiffPercentText, pastDiffPercentSuffix;
    if (lastTotalUsage === 0) {
        pastDiffPercentText = "-";
        pastDiffPercentSuffix = "";
        $(".compare-past-desc").addClass('invalid-saving');
        $(".compare-past-desc").removeClass('positive-saving');
        $(".compare-past-desc").removeClass('negative-saving');
    } else {
        var pastDiffPercent = (currentTotalUsage-lastTotalUsage)/lastTotalUsage*100;
        pastDiffPercentText = parseFloat(Utils.fixedDecBaseOnVal(Math.abs(pastDiffPercent)));
        if (pastDiffPercent >= 0) {
            pastDiffPercentSuffix = this.multiLangTexts.more;
            $(".compare-past-desc").addClass("negative-saving");
            $(".compare-past-desc").removeClass("positive-saving");
        } else {
            pastDiffPercentSuffix = this.multiLangTexts.less;
            $(".compare-past-desc").addClass("positive-saving");
            $(".compare-past-desc").removeClass("negative-saving");
        }

        $(".compare-past-desc").removeClass("invalid-saving");
    }
    $(".compare-past-percent").text(pastDiffPercentText);
    $(".compare-past-percent-suffix").text(pastDiffPercentSuffix);

    var maxUsage = Math.max.apply(Math, this.sumUpUsages);
    $(".compare-past-basic-info .compare-past-bar-container").each(function (eleIdx) {
        var usageIdx = reportGenThis.sumUpUsages.length-1-eleIdx;
        var usageVal = reportGenThis.sumUpUsages[usageIdx];
        if (usageVal > 0) {
            var eleHeight = usageVal/maxUsage*100;
            $(this).find(".compare-past-bar").css("height", eleHeight*0.9+"%");
            $(this).find(".compare-past-bar-val").css("bottom", eleHeight*0.9+"%")
            .text(Utils.formatWithCommas(usageVal.toFixed(0)));
        } else {
            $(this).find(".compare-past-bar").css("height", "0%");
            $(this).find(".compare-past-bar-val").css("bottom", "0%").text('N/A');
        }
    });

    var barNameEles = $(".compare-past-bar-name");
    var dayDiff = null;
    if (this.reportType === ReportGenerator.REPORT_TYPE_CUSTOM_MONTH) {
        dayDiff = this.currentEndDt.diff(this.currentDt, 'days');
    }
    var lastPeriodDts = this.genConsecutiveLasts(5, this.currentDt, dayDiff);
    $.each(lastPeriodDts, function(periodIdx, periodUnix) {
        var periodDt = moment.unix(periodUnix).tz(reportGenThis.timezone);
        var barNameEleIdx = lastPeriodDts.length-1-periodIdx;
        $(barNameEles[barNameEleIdx]).text(reportGenThis.genComparePastLabel(periodDt).toUpperCase());
    });

    var combinedCurrentReadings = {};
    var combinedLastReadings = {};
    $.each(this.groupedSourceInfos, function(groupIdx, info) {
        $.each(info.currentReadings, function(timestamp, value) {
            if (timestamp in combinedCurrentReadings) {
                combinedCurrentReadings[timestamp] += value;
            } else {
                combinedCurrentReadings[timestamp] = value;
            }
        });
        $.each(info.lastReadings, function(timestamp, value) {
            if (timestamp in combinedLastReadings) {
                combinedLastReadings[timestamp] += value;
            } else {
                combinedLastReadings[timestamp] = value;
            }
        });
    });
    var mainSeriesBaseOptions = $.extend(true, {}, ReportGenerator.MAIN_SERIES_BASE_OPTIONS);
    if (this.reportType === ReportGenerator.REPORT_TYPE_YEAR) {
        delete mainSeriesBaseOptions.points;
    }
    this.plotCompareLineChart(".detail-container>div.compare-past-line-chart",
        combinedCurrentReadings, combinedLastReadings,
        ReportGenerator.MAIN_PLOT_OPTIONS, mainSeriesBaseOptions);

    $(".compare-past-sub-info-container").empty();
    var subInfoTemplate = $("#compare-past-sub-info-template").html();
    Mustache.parse(subInfoTemplate);
    $.each(this.groupedSourceInfos, function(groupIdx, info) {
        var classIdentifier = "compare-past-sub-info-"+groupIdx;
        reportGenThis.insertComparePastSubInfo(subInfoTemplate, info, classIdentifier);

        reportGenThis.plotCompareLineChart("."+classIdentifier+" .compare-past-line-chart",
            info.currentReadings, info.lastReadings,
            ReportGenerator.SUB_INFO_PLOT_OPTIONS, ReportGenerator.SUB_INFO_SERIES_BASE_OPTIONS);
    });

    if (this.groupedSourceInfos.length%2 !== 0) {
        this.insertEmptyBlock(".compare-past-sub-info-container", 'compare-past-sub-info');
    }

    if (lastTotalUsage === 0) {
        $(".footnote-sybmol").show();
        $(".single-asterisk-text").css('visibility', 'block');
    } else {
        $(".footnote-sybmol").hide();
        $(".single-asterisk-text").css('visibility', 'hidden');
    }
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
            lessMoreText = this.multiLangTexts.calendarLess;
        } else {
            comparePercentEle.addClass("negative-saving");
            comparePercentEle.removeClass("positive-saving");
            lessMoreText = this.multiLangTexts.calendarMore;
        }
        comparePercentEle.find(".compare-percent").text(Utils.fixedDecBaseOnVal(Math.abs(usagePercent)));
    }

    var comparedSubtext;
    if (oldUsage === 0) {
        comparedSubtext = this.multiLangTexts.comparedTo+compareToDateText+" *";
    } else {
        comparedSubtext = lessMoreText+' '+this.multiLangTexts.comparedTo+compareToDateText;
    }
    comparePercentEle.find(".compare-subtext").html(comparedSubtext);
}

ReportGenerator.prototype._genSubComparePercentInfo = function(oldUsage, newUsage, compareToDateText) {
    var result = {};
    if (oldUsage === 0) {
        result.percentText = "-";
        result.subText = this.multiLangTexts.comparedTo+compareToDateText+" *";
        result.savingClass = "invalid-saving";
    } else {
        var percent = (newUsage-oldUsage)/oldUsage*100;
        if (percent >= 0) {
            result.subText = this.multiLangTexts.calendarMore;
            result.savingClass = "negative-saving";
        } else {
            result.subText = this.multiLangTexts.calendarLess;
            result.savingClass = "positive-saving";
        }
        result.subText += ' '+this.multiLangTexts.comparedTo+compareToDateText;
        result.percentText = Utils.formatWithCommas(Math.abs(percent).toFixed(0));
    }

    return result;
}

ReportGenerator.prototype._fillCalendar = function(eleSel, readings, averageUsage, isNotConcernFunc) {
    var reportGenThis = this;
    var calendarInfoContainer = $(eleSel);
    calendarInfoContainer.find(".calendar-title").text(this.genDtText(this.currentDt));

    var calendarContainer = calendarInfoContainer.find(".calendar-day-container");
    calendarContainer.empty();

    var calendarStartDt = moment(this.currentDt).startOf('w');
    var calendarEndDt = moment(this.currentEndDt).subtract(1, 's').endOf('w');
    for (var calendarNowDt=calendarStartDt; calendarNowDt.isBefore(calendarEndDt); calendarNowDt.add(1, 'd')) {
        var calendarDayEle = $("<div class='calendar-day'></div>");
        calendarDayEle.append("<div class='calendar-day-digit'>"+calendarNowDt.date()+"</div>");

        if (calendarNowDt.isBefore(reportGenThis.currentDt)
            || calendarNowDt.isSame(reportGenThis.currentEndDt)
            || calendarNowDt.isAfter(reportGenThis.currentEndDt)) {
            calendarDayEle.addClass('calendar-day-out-range');
        } else if (isNotConcernFunc(calendarNowDt)) {
            calendarDayEle.addClass('calendar-day-not-concern');
        } else {
            var diffPercent;
            if (calendarNowDt.unix() in readings) {
                diffPercent = (readings[calendarNowDt.unix()]-averageUsage)/averageUsage*100;
            } else {
                diffPercent = 0;
            }
            diffPercent = parseFloat(Utils.fixedDecBaseOnVal(diffPercent));
            
            var diffPercentText;
            if (diffPercent >= 0) {
                diffPercentText = "<span class='calendar-day-plus-symbol'>+</span> "+diffPercent;
            } else {
                diffPercentText = "<span class='calendar-day-minus-symbol'>-</span> "+Math.abs(diffPercent);
            }
            if (diffPercent >= 5) {
                calendarDayEle.addClass('calendar-day-worse');
            } else if (diffPercent <= -5) {
                calendarDayEle.addClass('calendar-day-better');
            }
            calendarDayEle.append("<div class='calendar-day-percent'>"
                +diffPercentText
                +"<span class='calendar-day-percent-symbol'>%</span></div>");
        }

        calendarContainer.append(calendarDayEle);
    }
}

ReportGenerator.prototype._insertCalendarSubInfo = function(eleSel, classIdPrefix,
    calendarTypeName, currentUsageKey, beginningUsageKey, lastUsageKey, lastSamePeriodUsageKey,
    beginningDateText, firstSplitText, secondSplitText, swapSplitPercent) {
    var reportGenThis = this;
    var detailContainer = $(eleSel);
    var subInfoTemplate = $("#sub-calendar-info-template").html();
    Mustache.parse(subInfoTemplate);

    detailContainer.empty();

    var transformedDatas = [];
    $.each(this.groupedSourceInfos, function(groupIdx, info) {
        transformedDatas.push(info);
    });
    transformedDatas.sort(function(a, b) {
        return b[currentUsageKey].average-a[currentUsageKey].average;
    });

    $.each(transformedDatas, function(dataIdx, info) {
        var classIdentifier = classIdPrefix+dataIdx;
        var averageUsage = info[currentUsageKey].average;
        var compareBeginningInfo = reportGenThis._genSubComparePercentInfo(
            info[beginningUsageKey].average, averageUsage, beginningDateText);
        var compareLastInfo = reportGenThis._genSubComparePercentInfo(
            info[lastUsageKey].average, averageUsage, reportGenThis.multiLangTexts.lastMonth);
        var compareLastSamePeriodInfo = reportGenThis._genSubComparePercentInfo(
            info[lastSamePeriodUsageKey].average, averageUsage, reportGenThis.multiLangTexts.samePeriodLastYear);
        var firstSplitPercent = parseFloat((info[currentUsageKey].total/info.currentTotalEnergy*100).toFixed(1));
        var secondSplitPercent = parseFloat((100-firstSplitPercent).toFixed(1));
        if (info[currentUsageKey].min.date !== null) {
            var lowestDt = moment(info[currentUsageKey].min.date, 'YYYY-MM-DD');
            var lowestText = lowestDt.format(reportGenThis.multiLangTexts.calendarUsageDtFormat)+' - '
                +Utils.formatWithCommas(info[currentUsageKey].min.val.toFixed(0))
                +' kWh';
        } else {
            var lowestText = '-';
        }
        if (info[currentUsageKey].max.date !== null) {
            var highestDt = moment(info[currentUsageKey].max.date, 'YYYY-MM-DD');
            var highestText = highestDt.format(reportGenThis.multiLangTexts.calendarUsageDtFormat)+' - '
                +Utils.formatWithCommas(info[currentUsageKey].max.val.toFixed(0))
                +' kWh';
        } else {
            var highestText = '-';
        }
        

        if (swapSplitPercent) {
            var tempSplitPercent = secondSplitPercent;
            secondSplitPercent = firstSplitPercent;
            firstSplitPercent = tempSplitPercent;
        }

        var name = ('sourceNameInfo' in info) ? info.sourceNameInfo[reportGenThis.langCode].toUpperCase() : info.system.data.nameInfo[reportGenThis.langCode].toUpperCase();
        name = (dataIdx+1) + '. ' + name;

        var templateInfo = {
            classIdentifier: classIdentifier,
            typeName: calendarTypeName,
            name: name,
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

    if (this.groupedSourceInfos.length%2 !== 0) {
        this.insertEmptyBlock(eleSel, 'sub-calendar-info-block');
    }
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

ReportGenerator.prototype.generateCalendarReport = function(targetSel, combinedReadings, currentUsageKey, beginningUsageKey,
    lastUsageKey, lastSamePeriodUsageKey, lowestUsage, lowestDt, highestUsage, highestDt, swapSplitPercent, isNotConcernFunc,
    classIdPrefix, calendarTypeName, firstSplitText, secondSplitText) {
    var reportGenThis = this;

    var allTotalUsage = 0;
    var totalUsage = 0;
    var averageUsage = 0;
    var beginningUsage = 0;
    var lastUsage = 0;
    var lastSamePeriodUsage = 0;

    $.each(this.groupedSourceInfos, function(groupIdx, info) {
        allTotalUsage += info.currentTotalEnergy;
        totalUsage += info[currentUsageKey].total;
        averageUsage += info[currentUsageKey].average;
        beginningUsage += info[beginningUsageKey].average;
        lastUsage += info[lastUsageKey].average;
        lastSamePeriodUsage += info[lastSamePeriodUsageKey].average;
    });

    var targetContainer = $(targetSel);
    targetContainer.find(".average-usage").text(Utils.formatWithCommas(averageUsage.toFixed(0)));
    var beginningDateText = this.beginningStartDt.format(this.multiLangTexts.beginDtFormat) + " **";
    this._fillInComparePercent(targetSel+" .compare-beginning", beginningUsage, averageUsage, beginningDateText);
    this._fillInComparePercent(targetSel+" .compare-last", lastUsage, averageUsage, this.multiLangTexts.lastMonth);
    this._fillInComparePercent(targetSel+" .compare-last-same-period", lastSamePeriodUsage, averageUsage, this.multiLangTexts.samePeriodLastYear);

    if (lowestDt !== null) {
        targetContainer.find(".lowest-usage-val").text(Utils.formatWithCommas(lowestUsage.toFixed(0)));
        targetContainer.find(".lowest-usage-date").text(lowestDt.format(this.multiLangTexts.calendarUsageDtFormat));
    }
    
    if (highestDt !== null) {
        targetContainer.find(".highest-usage-val").text(Utils.formatWithCommas(highestUsage.toFixed(0)));
        targetContainer.find(".highest-usage-date").text(highestDt.format(this.multiLangTexts.calendarUsageDtFormat));
    }

    var firstSplitPercent = parseFloat((totalUsage/allTotalUsage*100).toFixed(1));
    var secondSplitPercent = parseFloat((100-firstSplitPercent).toFixed(1));
    if (swapSplitPercent) {
        var tempSplitPercent = secondSplitPercent;
        secondSplitPercent = firstSplitPercent;
        firstSplitPercent = tempSplitPercent;
    }
    targetContainer.find(".first-split-val").text(firstSplitPercent+"%");
    targetContainer.find(".second-split-val").text(secondSplitPercent+"%");

    this._plotCalendarSubPieChart(targetSel+" .energy-split-pie",
        firstSplitPercent, secondSplitPercent,
        ReportGenerator.FIRST_SPLIT_PIE_COLOR, ReportGenerator.SECOND_SPLIT_PIE_COLOR);

    if (this.reportType === ReportGenerator.REPORT_TYPE_MONTH
        || this.reportType === ReportGenerator.REPORT_TYPE_CUSTOM_MONTH) {
        this._fillCalendar(targetSel+" .calendar-info-container", combinedReadings, averageUsage, isNotConcernFunc);
    } else if (this.reportType === ReportGenerator.REPORT_TYPE_YEAR
        || this.reportType === ReportGenerator.REPORT_TYPE_QUARTER
        || this.reportType === ReportGenerator.REPORT_TYPE_WEEK) {
        $(targetSel+" .calendar-title").text(this.genDtText(this.currentDt));
    }

    this._insertCalendarSubInfo(targetSel+" .detail-container", classIdPrefix, calendarTypeName,
        currentUsageKey, beginningUsageKey, lastUsageKey, lastSamePeriodUsageKey,
        beginningDateText, firstSplitText, secondSplitText, swapSplitPercent);

    if($(targetSel).find('.invalid-saving').length > 0) {
        $(targetSel).find('.not-available-footnote').addClass('showed-not-available-footnote').show();
    } else {
        $(targetSel).find('.not-available-footnote').removeClass('showed-not-available-footnote').hide();
    }
}

ReportGenerator.prototype.generateWeekdayReport = function(combinedReadings) {
    var reportGenThis = this;
    var lowestUsage = null;
    var lowestDt = null;
    var highestUsage = 0;
    var highestDt = null;

    $.each(combinedReadings, function(timestamp, val) {
        var dt = moment.unix(timestamp).tz(reportGenThis.timezone);
        if ((dt.day() >= 1 && dt.day() <= 5) && ($.inArray(dt.format("YYYY-MM-DD"), reportGenThis.holidays) == -1)) {
            if (val > highestUsage) {
                highestUsage = val;
                highestDt = dt;
            }
            if (lowestUsage === null) {
                lowestUsage = val;
                lowestDt = dt;
            } else if (val < lowestUsage) {
                lowestUsage = Math.min(val, lowestUsage);
                lowestDt = dt;
            }
        }
    });

    var isNotConcernFunc = function(targetDt) {
        return (targetDt.day() == 0
            || targetDt.day() == 6
            || ($.inArray(targetDt.format("YYYY-MM-DD"), reportGenThis.holidays) != -1))
    }

    this.generateCalendarReport('#weekday-info', combinedReadings,
        'currentWeekdayInfo', 'beginningWeekdayInfo',
        'lastWeekdayInfo', 'lastSamePeriodWeekdayInfo', lowestUsage, lowestDt, highestUsage, highestDt,
        false, isNotConcernFunc, 'weekday-sub-calendar', this.multiLangTexts.calendarTypeWeekday,
        this.multiLangTexts.calendarSplitWeekdays, this.multiLangTexts.calendarSplitWeekends);
}

ReportGenerator.prototype.generateWeekendReport = function(combinedReadings) {
    var reportGenThis = this;
    var lowestUsage = null;
    var lowestDt = null;
    var highestUsage = 0;
    var highestDt = null;

    $.each(combinedReadings, function(timestamp, val) {
        var dt = moment.unix(timestamp).tz(reportGenThis.timezone);
        if (dt.day() === 0 || dt.day() === 6 || ($.inArray(dt.format("YYYY-MM-DD"), reportGenThis.holidays) != -1)) {
            if (val > highestUsage) {
                highestUsage = val;
                highestDt = dt;
            }
            if (lowestUsage === null) {
                lowestUsage = val;
                lowestDt = dt;
            } else if (val < lowestUsage) {
                lowestUsage = Math.min(val, lowestUsage);
                lowestDt = dt;
            }
        }
    });

    var isNotConcernFunc = function(targetDt) {
        return (targetDt.day() >= 1
            && targetDt.day() <= 5
            && ($.inArray(targetDt.format("YYYY-MM-DD"), reportGenThis.holidays) == -1))
    }

    this.generateCalendarReport('#weekend-info', combinedReadings,
        'currentWeekendInfo', 'beginningWeekendInfo',
        'lastWeekendInfo', 'lastSamePeriodWeekendInfo', lowestUsage, lowestDt, highestUsage, highestDt,
        true, isNotConcernFunc, 'weekend-sub-calendar', this.multiLangTexts.calendarTypeWeekend,
        this.multiLangTexts.calendarSplitWeekdays, this.multiLangTexts.calendarSplitWeekends);
}

ReportGenerator.prototype.generateOvernightReport = function(combinedReadings) {
    var reportGenThis = this;
    var lowestUsage = null;
    var lowestDt = null;
    var highestUsage = 0;
    var highestDt = null;

    $.each(combinedReadings, function(timestamp, val) {
        var dt = moment.unix(timestamp).tz(reportGenThis.timezone);
        if (val > highestUsage) {
            highestUsage = val;
            highestDt = dt;
        }

        if (lowestUsage === null) {
            lowestUsage = val;
            lowestDt = dt;
        } else if (val < lowestUsage) {
            lowestUsage = Math.min(val, lowestUsage);
            lowestDt = dt;
        }
    });

    var isNotConcernFunc = function(targetDt) {
        return false;
    }

    this.generateCalendarReport('#overnight-info', combinedReadings,
        'currentOvernightInfo', 'beginningOvernightInfo',
        'lastOvernightInfo', 'lastSamePeriodOvernightInfo', lowestUsage, lowestDt, highestUsage, highestDt,
        true, isNotConcernFunc, 'overnight-sub-calendar', this.multiLangTexts.calendarTypeOvernight,
        this.multiLangTexts.calendarSplitDaytime, this.multiLangTexts.calendarSplitOvernight);

    $('.overnight-footnote').text('*** '
        + this.overnightStartDt.format(reportGenThis.multiLangTexts.overnightFootnoteFormat)
        + ' - '
        + this.overnightEndDt.format(reportGenThis.multiLangTexts.overnightFootnoteFormat));
}
