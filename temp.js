$scope.realTimeOptions = {
            // transitions: false,
            chartArea: {
                margin: 0,
                background: "#FCFCFC"
            },
            series: [{
                type: "column",
                name: "Today",
                color: "#81d51d",
                gap: 1.2,
                overlay: {
                    gradient: "none"
                },
                border: {
                    width: 0
                },
                data: today_measures
            }, {
                type: "line",
                name: "Last Week",
                color: "#354960",
                line: {
                    width: 2
                },
                data: last_week_measures
            }],
            legend: {
                visible: false
            },
            categoryAxis: {
                categories: hours,
                labels: {
                    step: 2,
                    font: "0.857em ITCAvantGardeStd-Bk",
                    padding: {
                     top: 5
                    },
                    color: "#4B4B4B",
                    template: "#= to_ampm(value) #"
                },
                line: {
                    visible: true,
                    width: 2,
                    color: "#ECECEC"
                },
                majorGridLines: {
                    visible: false
                },
                majorTicks: {
                    size: 0
                }
            },
            valueAxis: {
                line: {
                    visible: false
                },
                labels: {
                        format: "{0}",
                        font: "0.857em ITCAvantGardeStd-Bk",
                        color: "#4B4B4B"
                    },
                min: 0
            },
            tooltip: {
                visible: true,
                template: "# if (value < 1) { # #=kendo.toString(value, 'n2')# # } else if (value < 10) { # #=kendo.toString(value, 'n1') # # } else { # #=kendo.toString(value, 'n0') # # } #",
                background: "#EFEFEF",
                border: {
                    color: "#333",
                    width: 2
                },
            }

        }



        var ca = {
            margin: 0,
            background: '#FCFCFC'
        };
        var le = {
            visible: false,
            position: 'bottom'
        };
        var sd = {
            type: 'column'
        };
        var va = {
            visible: false,
            line: {
                visible: false
            },
            majorGridLines: {
                visible: false
            },
            min: 0
        };
        var catAxis = {
            visible: true,
            line: {
                visible: true,
                width: 2,
                color: "#D3D3D3"
            },
            majorGridLines: {
                visible: false
            },
            majorTicks: {
                size: 0
            }
        };

 $scope.soFarOptionsThis = {
            // transitions: false,
            series: [{
                markers: { visible: true },
                data: thisCost,
                color: '#354960',
                opacity: 0.6,
                gap: 0.1,
                overlay: {
                    gradient: "none"
                },
                border: {
                    width: 0
                },
                highlight: {
                    visible: false
                },
                labels: {
                    visible: true,
                    font: "bold 1.357em ITCAvantGardeStd-Bk",
                    color: "#354960",
                    format: "$ ##,#"
                }
            }],
            chartArea: ca,
            legend: le,
            seriesDefaults: sd,
            valueAxis: va,
            categoryAxis: catAxis
        }
        $scope.soFarOptionsLast = {
            // transitions: false,
            series: [{
                markers: { visible: true },
                data: lastCost,
                color: '#7a7a7a',
                opacity: 0.6,
                gap: 0.1,
                overlay: {
                    gradient: "none"
                },
                border: {
                    width: 0
                },
                highlight: {
                    visible: false
                },
                labels: {
                    visible: true,
                    font: "bold 1.357em ITCAvantGardeStd-Bk",
                    color: "#878787",
                    format: "$ ##,#"
                }
            }],
            chartArea: ca,
            legend: le,
            seriesDefaults: sd,
            valueAxis: va,
            categoryAxis: catAxis
        }
 $scope.lastWeekStatOptions = {
            dataSource: {
                data: []
            },
            chartArea: {
                margin: 0,
                background: "#FCFCFC"
            },
            // seriesDefaults: {
            //     type: "area",
            //     opacity: 0.6
            // },
            series: [{
                type: "area",
                opacity: 0.6,
                markers: {visible: true},
                field: "value",
                color: "#354960",
                line: {
                    width: 2
                }
            },{
                type: "column", //add this to give some space before the first data point and after the last data point
                field: "dummy"
            }],
            valueAxis: {
                labels: {
                    format: "{0}",
                    font: "0.857em ITCAvantGardeStd-Bk",
                    color: "#4B4B4B"
                },
                line: {
                    visible: false
                },
                majorGridLines: {
                    color: "#ECECEC",
                    visible: true
                },
                majorUnit: dayStep,
                max: dayMaxStep,
                min: 0
            },
            categoryAxis: {
                field: "weekday",
                type: "date",
                majorGridLines: {
                    //color: "#ECECEC",
                    visible: false
                },
                labels: {
                    font: "0.857em ITCAvantGardeStd-Bk",
                    color: "#4B4B4B",
                    dateFormats: {
                        days: "ddd"
                    }
                },
                line: {
                    color: "#ECECEC",
                    width: 2,
                    visible: true
                },
                majorTicks: {
                    size: 0

                }
            },
            tooltip: {
                visible: true,
                //format: "{0}%",
                template: "# if (value < 1) { # #=kendo.toString(value, 'n2')# # } else if (value < 10) { # #=kendo.toString(value, 'n1') # # } else { # #=kendo.toString(value, 'n0') # # } #",
                background: "#EFEFEF",
                border: {
                    color: "#333",
                    width: 2
                },
            }
        };