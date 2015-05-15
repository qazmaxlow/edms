var EtDropDown = function(elm, data){
    var that = this,
    body = document.body,
    keys = kendo.keys,
    support = kendo.support,
    ARIA_HIDDEN = "aria-hidden",
    EMPTYITEMLIST = '<div class="k-itemList"></div><div class="k-editPanel"><input></input><button class="add-btn">Add</button></div>',
    // EMPTYITEMLIST = '<div class="k-itemList"></div><div class="k-editPanel"><input></input><button class="add-btn">Add</button><label class="valid-msg">Invalid</label></div>',
    SPAN = "<SPAN/>",
    ns = ".kendoEtDropDown",
    MOUSEDOWN = "mousedown" + ns,
    KEYDOWN = "keydown" + ns,
    CLICK = "click" + ns;
    
    that.wrapper = '<SPAN unselectable="on" class="k-widget k-dropdown k-header"><SPAN unselectable="on" class="k-dropdown-wrap k-state-default">'
                + '<SPAN unselectable="on" class="k-input"></SPAN>' 
                + '<SPAN unselectable="on" class="k-select"><SPAN unselectable="on" class="k-icon k-i-arrow-s"></SPAN></SPAN>'
                + '</SPAN></SPAN>';

    that.wrapper = $(that.wrapper);
    that.wrapper.appendTo(elm);

    that.options = {
        readOnly: false,
        itemDisplayName: "Emails",
        emptyItemText: "Add Email",
        ignoreCase: true
    };

    if (data == null){
        that.value([]);
    } else {
        that.value(data);    
    }

    that.container = $("<DIV/>").attr(ARIA_HIDDEN, "true").addClass("k-et-dropdown-container").appendTo(body);
    var opt = {};
    opt.animation = {};
    opt.origin = "bottom center";
    opt.position = "top center";
    opt.name = "Popup";
    opt.isRtl = kendo.support.isRtl(opt.anchor);
    opt.anchor = that.wrapper;

    that.popup = new kendo.ui.Popup(that.container, opt);

    var div = $("<DIV/>").attr("id", kendo.guid()).appendTo(that.popup.element);//.on(MOUSEDOWN, preventDefault);
    div.html(EMPTYITEMLIST);

    // function validateEmail(sEmail) {
    //     var filter = /^([\w-\.]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([\w-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$/;
    //     if (filter.test(sEmail)) {
    //         return true;
    //     }
    //     else {
    //         return false;
    //     }
    // }

    function addAction(){
        // if (validateEmail(that.container.find("INPUT").val())){
            if (that.addItem(that.container.find("INPUT").val())){
                $(".invalid-msg").removeClass("invalid-msg").addClass("valid-msg");
                that.container.find("INPUT").val("");
                that.updatePopup();
            }        
        // } else {
        //     $(".valid-msg").addClass("invalid-msg").removeClass("valid-msg");
        // }
    }

    that.container.on(KEYDOWN, function(e){
        if (e.keyCode == keys.ESC) {
            that.popup.close();
            return;
        } else if (e.keyCode == keys.ENTER) {
            addAction();
            return;
        }
    });

    that.container.find(".add-btn").on(CLICK, addAction);

    that.container.find(".k-itemList").on(CLICK, function(e){
        var target = $(e.target);
        if (target.hasClass("k-select") || target.hasClass("k-icon")){
            var item = target.closest("DIV").find(".k-item").text();
            that.removeItem(item);
            that.updatePopup();
        }
    });
    
    that.wrapper.on(MOUSEDOWN, function(){
        if (that.popup.visible()){
            that.close();
        } else {
            that.open();    
        }
    });

};

EtDropDown.prototype = {
    ITEM: '<DIV class="k-itemRow"><DIV class="k-highlight"><SPAN class="k-item"></SPAN>'
         + '<SPAN class="k-select"><SPAN class="k-icon k-delete"></SPAN></SPAN></DIV></DIV>',

    value: function(data){
        if (data == null){
            return this.items;
        }

        if ($.isArray(data)){
            this.items = data;
        } else {
            this.items = [data];
        }
        this.updateTextbox();

        if (this.options.onchange && typeof this.options.onchange == "function"){
            this.options.onchange();
        }
    },

    addItem: function(item){
        if (item && item.trim()){
            item = item.trim();
            if (this.options.ignoreCase){
                for (var i=0; i<this.items.length; i++){
                    if (this.items[i].toLowerCase() == item.toLowerCase()){
                        return false;
                    }
                }
                this.items.push(item);
                this.updateTextbox();
                if (this.options.onchange && typeof this.options.onchange == "function"){
                    this.options.onchange();
                }
                return true;
            } else if (this.items.indexOf(item) == -1){
                this.items.push(item);
                this.updateTextbox();
                if (this.options.onchange && typeof this.options.onchange == "function"){
                    this.options.onchange();
                }
                return true;
            }
        }
        return false;
    },

    removeItem: function(item){
        if (item){
            var i = this.items.indexOf(item);
            if (i != -1){
                this.items.splice(i, 1);
                this.updateTextbox();
                if (this.options.onchange && typeof this.options.onchange == "function"){
                    this.options.onchange();
                }
            }
        }
    },

    updatePopup: function(){
        var list = $(this.popup.element).find(".k-itemList");
        list.html("");

        for (var i=0; i<this.items.length; i++){
            var item = $(this.ITEM);
            item.find(".k-item").html(this.items[i]);
            item.appendTo(list);
        }
    },

    updateTextbox: function(){
        if (this.items.length == 0 && this.options.emptyItemText){
            this.wrapper.find(".k-input").text(this.options.emptyItemText);
        } else if (this.items.length == 1){
            this.wrapper.find(".k-input").text(this.items[0]);
        } else {
            this.wrapper.find(".k-input").text(this.items.length + " " + this.options.itemDisplayName);
        }
    },

    setOptions: function(opt){
        var that = this;
        if (opt && typeof opt == "object"){
            $.each(opt, function(key, val){
                that.options[key] = val;
            });
        }
        that.wrapper.attr("aria-readonly", that.options.readOnly);
        that.updateTextbox();
    },

    open: function(){
        if (this.wrapper.attr("aria-readonly") == "true")
            return;

        var input = this.container.find("INPUT");
        this.updatePopup();
        input.val("");
        this.popup.open();
        setTimeout(function(){
            input.focus();
        }, 200);
    },

    close: function(){
        this.popup.close();
    }
}