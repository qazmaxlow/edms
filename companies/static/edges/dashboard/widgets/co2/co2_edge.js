
(function(compId){var _=null,y=true,n=false,x2='5.0.0',x4='rgba(0,0,0,0)',e10='${left_3}',x1='5.0.1',x17='64px',x16='82px',e19='${right_1}',x18='auto',e12='${right_2_Smoke}',x13='right_1',ky='skewY',e11='${right_2}',o='opacity',x8='rgba(255,255,255,1)',x14='0.98',kx='skewX',x15='0px',x3='5.0.1.386',e9='${right_2Copy}',g='image',i='none';var g6='smoke.svg',g5='co2.svg',g7='smoke-two.svg';var im='images/',aud='media/',vid='media/',js='js/',fonts={},opts={'gAudioPreloadPreference':'auto','gVideoPreloadPreference':'auto'},resources=[],scripts=[],symbols={"stage":{v:x1,mv:x2,b:x3,stf:i,cg:i,rI:n,cn:{dom:[{id:'co2',t:g,r:['77px','227px','395px','173px','auto','auto'],f:[x4,im+g5,'0px','0px']},{id:'right_2',t:g,r:['324px','216px','50px','39px','auto','auto'],o:'0',f:[x4,im+g6,'0px','0px']},{id:'right_2_Smoke',t:g,r:['395px','56px','65px','51px','auto','auto'],o:'0',f:[x4,im+g6,'0px','0px']},{id:'right_2Copy',t:g,r:['379px','158px','76px','59px','auto','auto'],o:'0',f:[x4,im+g6,'0px','0px']},{id:'left_3',t:g,r:['133px','179px','75px','59px','auto','auto'],o:'0',f:[x4,im+g7,'0px','0px']},{id:'left_3Copy2',t:g,r:['212px','29px','98px','73px','auto','auto'],o:'0.7',f:[x4,im+g7,'0px','0px'],filter:[0,0,1,1,0,0,0,6,"rgba(0,0,0,0)",0,0,0],tf:[[],['-22'],[],['1.40695','1.1513']]},{id:'left_3Copy3',t:g,r:['331px','3px','147px','90px','auto','auto'],o:'0.64',f:[x4,im+g7,'0px','0px'],filter:[0,0,1,1,0,0,0,4,"rgba(0,0,0,0)",0,0,0],tf:[[],['-22'],[],['1.40695','1.1513']]},{id:'left_3Copy4',t:g,r:['21px','-13px','220px','100px','auto','auto'],br:["22.009660930827px 10.867098262986px","22.009660930827px 10.867098262986px","22.009660930827px 10.867098262986px","22.009660930827px 10.867098262986px"],o:'0.55',f:[x4,im+g7,'0px','0px'],filter:[0,0,1,1,0,0,0,8,"rgba(0,0,0,0)",0,0,0],tf:[[],['-22'],[],['1.29731','1.3674']]}],style:{'${Stage}':{isStage:true,r:['null','null','550px','400px','auto','auto'],overflow:'hidden',f:[x8]}}},tt:{d:3000,a:y,data:[["eid11",o,0,0,"linear",e9,'0','0'],["eid15",o,625,571,"linear",e9,'0','1'],["eid17",o,2134,366,"easeOutQuad",e9,'1','0'],["eid32","location",0,2500,"easeInQuad",e10,[[174.23,226.5,0,0,0,0,0],[156.6,119.68,-30.63,-85.9,-46.33,-129.91,108.57],[108.55,47.78,-54.5,-110.26,-38.33,-77.56,195.32],[85.62,-29.5,0,0,0,0,276.23]]],["eid46",kx,0,0,"linear",e11,'0deg','0deg'],["eid19","location",1854,646,"linear",e12,[[427.25,81.26,0,0,0,0,0],[477.15,-25.25,0,0,0,0,117.62]]],["eid35",o,432,725,"easeOutQuad",e10,'0','1'],["eid44",o,0,0,"linear",e11,'0','0'],["eid45",o,168,750,"linear",e11,'0','1'],["eid30",o,1802,698,"easeOutQuad",e11,'1','0'],["eid10","location",0,2500,"easeInQuad",e9,[[411.54,216.5,0,0,0,0,0],[434.96,118.3,36.7,-64.34,89.37,-156.69,102.42],[486.1,43.28,80.45,-98.43,49.75,-60.88,193.29],[541.09,-29.5,0,0,0,0,284.52]]],["eid22",o,1854,396,"linear",e12,'0','0.7'],["eid23",o,2250,250,"linear",e12,'0.7','0'],["eid47",ky,0,0,"linear",e11,'0deg','0deg'],["eid25","location",0,2500,"linear",e11,[[341.15,245.5,0,0,0,0,0],[370.21,142.16,9.47,-86.25,16.71,-152.29,107.67],[364.23,43.69,5.08,-133.69,3.16,-83.25,206.43],[377.64,-25.5,0,0,0,0,277.26]]]]}},"right_1_symbol":{v:x1,mv:x2,b:x3,stf:i,cg:i,rI:n,cn:{dom:[{t:g,id:x13,o:x14,r:[x15,x15,x16,x17,x18,x18],f:[x4,im+g6,x15,x15]}],style:{'${symbolSelector}':{r:[_,_,x16,x17]}}},tt:{d:2000,a:y,data:[["eid5","location",0,2000,"easeInOutCirc",e19,[[41.01,32,0,0,0,0,0],[72.71,-82.69,104.85,-185.95,90.39,-160.3,119.95],[171.89,-200.11,0,0,0,0,274.26]]]]}}};AdobeEdge.registerCompositionDefn(compId,symbols,fonts,scripts,resources,opts);})("EDGE-18660633");
(function($,Edge,compId){var Composition=Edge.Composition,Symbol=Edge.Symbol;Edge.registerEventBinding(compId,function($){
//Edge symbol: 'stage'
(function(symbolName){Symbol.bindElementAction(compId,symbolName,"document","compositionReady",function(sym,e){var numbersX;var numbersY;function randomNumbers(){numbersX=Math.floor(Math.random()*500);numbersY=Math.floor(Math.random()*500);moveMe();}
randomNumbers();function moveMe(){sym.$("right_2").animate({left:numbersX,top:numbersY},1000,randomNumbers);}});
//Edge binding end
Symbol.bindTriggerAction(compId,symbolName,"Default Timeline",3000,function(sym,e){sym.play();});
//Edge binding end
})("stage");
//Edge symbol end:'stage'

//=========================================================

//Edge symbol: 'right_1_symbol'
(function(symbolName){Symbol.bindTriggerAction(compId,symbolName,"Default Timeline",2000,function(sym,e){sym.play(0);});
//Edge binding end
Symbol.bindSymbolAction(compId,symbolName,"creationComplete",function(sym,e){});
//Edge binding end
})("right_1_symbol");
//Edge symbol end:'right_1_symbol'
})})(AdobeEdge.$,AdobeEdge,"EDGE-18660633");