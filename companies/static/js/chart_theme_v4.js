var rto = {
    // transitions: false,
    "chartArea": {
        "margin": 0,
        "background": "#FCFCFC"
    },
    "series": [{
        "type": "column",
        "name": "Today",
        "color": "#45af49", 
        "gap": 1.2,
        "overlay": {
            "gradient": "none"
        },
        "border": {
            "width": 0
        }
    }, {
        "type": "line",
        "name": "Last Week",
        "color": "#fdb813",
        "line": {
            "width": 2
        }
    }],
    "legend": {
        "visible": false
    },
    "categoryAxis": {
        "categories": "hours",
        "labels": {
            "step": 2,
            "font": "0.857em Roboto",
            "padding": {
             "top": 5
            },
            "color": "#4B4B4B",
            "template": "#= to_ampm(value) #"
        },
        "line": {
            "visible": true,
            "width": 2,
            "color": "#ECECEC"
        },
        "majorGridLines": {
            "visible": false
        },
        "majorTicks": {
            "size": 0
        }
    },
    "valueAxis": {
        "line": {
            "visible": false
        },
        "labels": {
                "format": "{0}",
                "font": "0.857em Roboto",
                "color": "#4B4B4B"
            },
        "min": 0
    },
    "tooltip": {
        "visible": true,
        "template": "# if (value < 1) { # #=kendo.toString(value, 'n2')# # } else if (value < 10) { # #=kendo.toString(value, 'n1') # # } else { # #=kendo.toString(value, 'n0') # # } #",
        "background": "#EFEFEF",
        "border": {
            "color": "#333",
            "width": 2
        },
    }

};

var lwso = {
    "dataSource": {
        "data": []
    },
    "chartArea": {
        "margin": 0,
        "background": "#FCFCFC"
    },
    // seriesDefaults: {
    //     type: "area",
    //     opacity: 0.6
    // },
    "series": [{
        "type": "line",
        "opacity": 0.6,
        "markers": {"visible": true},
        "field": "value",
        "color": "#fdb813",
        "line": {
            "width": 3
        }
    },{
        "type": "column", //add this to give some space before the first data point and after the last data point
        "field": "dummy"
    }],
    "valueAxis": {
        "labels": {
            "format": "{0}",
            "font": "0.857em Roboto",
            "color": "#4B4B4B"
        },
        "line": {
            "visible": false
        },
        "majorGridLines": {
            "color": "#ECECEC",
            "visible": true
        },
        "majorUnit": "dayStep",
        "max": "dayMaxStep",
        "min": 0
    },
    "categoryAxis": {
        "field": "weekday",
        "type": "date",
        "majorGridLines": {
            "color": "#ECECEC",
            "visible": true
        },
        "labels": {
            "font": "0.857em Roboto",
            "color": "#4B4B4B",
            "dateFormats": {
                "days": "ddd"
            }
        },
        "line": {
            "color": "#b4b4b4",
            "width": 2,
            "visible": true
        },
        "majorTicks": {
            "size": 0

        }
    },
    "tooltip": {
        "visible": true,
        //format: "{0}%",
        "template": "# if (value < 1) { # #=kendo.toString(value, 'n2')# # } else if (value < 10) { # #=kendo.toString(value, 'n1') # # } else { # #=kendo.toString(value, 'n0') # # } #",
        "background": "#EFEFEF",
        "border": {
            "color": "#333",
            "width": 2
        },
    }
};

var ca = {
    "margin": 0,
    "background": '#FCFCFC'
};
var le = {
    "visible": false,
    "position": 'bottom'
};
var sd = {
    "type": 'column'
};
var va = {
    "visible": false,
    "line": {
        "visible": false
    },
    "majorGridLines": {
        "visible": false
    },
    "min": 0
};
var catAxis = {
    "visible": true,
    "line": {
        "visible": true,
        "width": 2,
        "color": "#D3D3D3"
    },
    "majorGridLines": {
        "visible": false
    },
    "majorTicks": {
        "size": 0
    }
};

var sfot = {
    // transitions: false,
    "series": [{
        "markers": { "visible": true },
        "data": "thisCost",
        "color": "#fdb813",
        "opacity": 0.5,
        "gap": 0.1,
        "overlay": {
            "gradient": "none"
        },
        "border": {
            "width": 0
        },
        "highlight": {
            "visible": false
        },
        "labels": {
            "visible": true,
            "font": "bold 1.357em Roboto",
            "color": "#fdb813",
            "format": "$ ##,#"
        }
    }],
    "chartArea": ca,
    "legend": le,
    "seriesDefaults": sd,
    "valueAxis": va,
    "categoryAxis": catAxis
}

var sfol = {
    // transitions: false,
    "series": [{
        "markers": { "visible": true },
        "data": "lastCost",
        "color": '#45af49',
        "opacity": 0.5,
        "gap": 0.1,
        "overlay": {
            "gradient": "none"
        },
        "border": {
            "width": 0
        },
        "highlight": {
            "visible": false
        },
        "labels": {
            "visible": true,
            "font": "bold 1.357em Roboto",
            "color": "#45af49",
            "format": "$ ##,#"
        }
    }],
    "chartArea": ca,
    "legend": le,
    "seriesDefaults": sd,
    "valueAxis": va,
    "categoryAxis": catAxis
}