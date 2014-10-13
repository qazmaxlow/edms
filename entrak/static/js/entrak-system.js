function EntrakSystem() {
    this.systemTree = null;
    this.langCode = 'en';
}

EntrakSystem.prototype.assignSystemTree = function(jsonStr) {
    var entrakSysThis = this;
    var systems = JSON.parse(jsonStr);

    $.each(systems, function(idx, system) {
        system.sources = {};

        if (idx === 0) {
            entrakSysThis.systemTree = new Arboreal(null, system);
        } else {
            var parentCodes = $(system.path.split(',')).filter(function(){
                return this != "";
            });
            var parentCode = parentCodes[parentCodes.length - 1];
            var parentNode = entrakSysThis.systemTree.find(function (node) {
                return node.data.code == parentCode;
            });
            parentNode.appendChild(system);
        }
    });
}

EntrakSystem.prototype.addSourceToSystem = function(jsonStr) {
    var entrakSysThis = this;
    var sources = JSON.parse(jsonStr);

    $.each(sources, function(idx, source) {
        var systemNode = entrakSysThis.systemTree.find(function (node) {
            return (source.systemCode === node.data.code);
        });
        systemNode.data.sources[source.id] = source;
    })
}

EntrakSystem.prototype.getGroupedSourceInfos = function() {
    var entrakSysThis = this;
    var groupedSourceIds = [];
    $.each(entrakSysThis.systemTree.children, function(subSystemIdx, subSystem) {
        var sourceIds = [];
        subSystem.traverseDown(function (node){
            for (var sourceId in node.data.sources) {
                sourceIds.push(sourceId);
            }
        });

        groupedSourceIds.push({name: subSystem.data.nameInfo[entrakSysThis.langCode], code: subSystem.data.code, source_ids:sourceIds});
    })

    $.each(entrakSysThis.systemTree.data.sources, function(sourceId, source){
        groupedSourceIds.push({name: source.nameInfo[entrakSysThis.langCode], source_ids:[sourceId]});
    });

    return groupedSourceIds;
}

EntrakSystem.prototype.getAllSourceIds = function () {
    var sourceIds = [];
    this.systemTree.traverseDown(function (node) {
        for (var sourceId in node.data.sources) {
            sourceIds.push(sourceId);
        }
    });

    return sourceIds;
}
