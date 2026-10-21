// Rebuild the three visible report pages and context tooltip, preserving the model binding.
// SVG measures are data-bound vector charts, not static snapshot illustrations.
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const root = path.resolve(__dirname, '..');
const report = path.join(root, 'RPT_EV_Analytics.Report');
const read = p => JSON.parse(fs.readFileSync(path.join(report, p), 'utf8'));
const write = (p, v) => { const f = path.join(report, p); fs.mkdirSync(path.dirname(f), {recursive:true}); fs.writeFileSync(f, JSON.stringify(v,null,2)+'\n'); };
const id = s => crypto.createHash('sha256').update(s).digest('hex').slice(0,20);
const L = v => ({expr:{Literal:{Value:typeof v==='boolean'?String(v):typeof v==='number'?`${v}D`:`'${v.replaceAll("'","''")}'`}}});
const I = v => ({expr:{Literal:{Value:`${v}L`}}});
const C = {bg:'#0B1220',card:'#131E2F',line:'#26354B',text:'#F8FAFC',muted:'#94A3B8',green:'#34D399',blue:'#38BDF8',amber:'#FBBF24',orange:'#FB923C'};
const color = v => ({solid:{color:L(v)}});
const O = (properties,selector) => [{properties,...(selector?{selector}:{})}];
const field = (table,name,measure=false) => ({[measure?'Measure':'Column']:{Expression:{SourceRef:{Entity:table}},Property:name}});
const P = (table,name,measure=false,label=name) => ({field:field(table,name,measure),queryRef:`${table}.${name}`,nativeQueryRef:name,displayName:label});
const M = name => P('EV Respondents',name,true);
const role = (...projections) => ({projections});
const q = s => '"'+s.replaceAll('"','""')+'"';
const measures = [];
const measure = (name,expression,format='0.00%',image=false) => measures.push({name,expression,format,image});
const rateAt = (table,column,value) => `CALCULATE([Purchase Intent Rate], REMOVEFILTERS('${table}'[${column}]), '${table}'[${column}] = "${value}")`;
for(const [prefix,t,c,lo,hi] of [
 ['Home Charging','Charging','Home_Charging_Possible','No','Yes'],
 ['Subsidy','Attitude and Incentive','Subsidy_Available','No','Yes'],
 ['Income','Income','income_band','Under 50k','100k+']
]) {
 measure(`${prefix} Baseline Intent`,rateAt(t,c,lo));
 measure(`${prefix} Comparison Intent`,rateAt(t,c,hi));
 measure(`${prefix} Gap pp`,`VAR A = [${prefix} Baseline Intent]\nVAR B = [${prefix} Comparison Intent]\nRETURN IF(NOT ISBLANK(A) && NOT ISBLANK(B), (B - A) * 100)`, '+0.00" pp";-0.00" pp";0.00" pp"');
}
measure('Share of Population','DIVIDE([Respondents], CALCULATE([Respondents], REMOVEFILTERS()))');
measure('Range Anxiety Order','IF(NOT ISBLANK([Respondents]), SWITCH(SELECTEDVALUE(\'Attitude and Incentive\'[Range_Anxiety_Level]), "Low", 1, "Medium", 2, "High", 3))','0');
measure('Segment Selection',`SELECTEDVALUE('Demographics'[age_band], "All / multiple ages") & " | " & SELECTEDVALUE('Income'[income_band], "All / multiple incomes")`,null);
measure('Executive Insight',`VAR T = FILTER(UNION(ROW("Factor", "Subsidy", "Gap", [Subsidy Gap pp]), ROW("Factor", "Income", "Gap", [Income Gap pp]), ROW("Factor", "Home charging", "Gap", [Home Charging Gap pp])), NOT ISBLANK([Gap]))\nVAR TopFactor = TOPN(1, T, ABS([Gap]), DESC, [Factor], ASC)\nRETURN IF(COUNTROWS(T) = 0, "No comparable groups in this selection", CONCATENATEX(TopFactor, [Factor] & ": " & FORMAT([Gap], "+0.00;-0.00;0.00") & " pp observed gap"))`,null);
const svgOpen = (w,h) => `<svg xmlns='http://www.w3.org/2000/svg' width='${w}' height='${h}' viewBox='0 0 ${w} ${h}'><rect width='100%' height='100%' fill='${C.card}'/>`;
const txt = (x,y,s,size=18,fill=C.text) => `<text x='${x}' y='${y}' font-family='Segoe UI,Arial' font-size='${size}' fill='${fill}'>${s}</text>`;
// Every pair uses a shared 0-100% scale. Filter only the compared attribute out;
// all other demographic/charging filters remain active. Missing groups stay blank.
function dumbbell(prefix,left,right,accent) {
 const a=`[${prefix} Baseline Intent]`, b=`[${prefix} Comparison Intent]`;
 const body = `${svgOpen(700,140)}${txt(24,28,left,17,C.muted)}${txt(380,28,right,17,accent)}`;
 const expr=`VAR A = ${a}\nVAR B = ${b}\nVAR XA = FORMAT(44 + A * 610, "0.0", "en-US")\nVAR XB = FORMAT(44 + B * 610, "0.0", "en-US")\nVAR Body = ${q(body)} & ${q(txt(24,55,"")) .replace('></text>','></text>')}\nVAR Chart = "<line x1='44' x2='654' y1='85' y2='85' stroke='${C.line}' stroke-width='2'/><line x1='" & XA & "' x2='" & XB & "' y1='85' y2='85' stroke='${accent}' stroke-width='5'/><circle cx='" & XA & "' cy='85' r='8' fill='${C.muted}'/><circle cx='" & XB & "' cy='85' r='8' fill='${accent}'/>"\nVAR Labels = "${txt(24,55,'" & FORMAT(A, "0.00%") & "',22,C.muted)}${txt(380,55,'" & FORMAT(B, "0.00%") & "',22,accent)}${txt(24,125,'0%',13,C.muted)}${txt(620,125,'100%',13,C.muted)}${txt(220,125,'" & FORMAT((B-A)*100, "+0.00;-0.00;0.00") & " pp',20,accent)}"\nRETURN "data:image/svg+xml;utf8," & SUBSTITUTE(IF(ISBLANK(A) || ISBLANK(B), ${q(svgOpen(700,140)+txt(24,70,'No comparable groups in this selection')+'</svg>')}, Body & Chart & Labels & "</svg>"), "#", "%23")`;
 measure(`${prefix} Dumbbell SVG`,expr,null,true);
}
dumbbell('Home Charging','No home charging','Home charging available',C.green);
dumbbell('Subsidy','No subsidy','Subsidy available',C.amber);
measure('Observed Gaps SVG',`VAR T = FILTER(UNION(ROW("Factor", "Subsidy", "Gap", [Subsidy Gap pp]), ROW("Factor", "Income: 100k+ vs under 50k", "Gap", [Income Gap pp]), ROW("Factor", "Home charging", "Gap", [Home Charging Gap pp])), NOT ISBLANK([Gap]))\nVAR Ranked = ADDCOLUMNS(T, "Position", RANKX(T, ABS([Gap]), , DESC, DENSE))\nVAR RowsSVG = CONCATENATEX(Ranked, VAR Y = 50 + ([Position]-1)*92 VAR X = 250 + ABS([Gap])*3 RETURN "<text x='20' y='" & Y & "' font-family='Segoe UI' font-size='18' fill='${C.text}'>" & [Factor] & "</text><line x1='250' x2='" & FORMAT(X,"0.0","en-US") & "' y1='" & (Y+24) & "' y2='" & (Y+24) & "' stroke='${C.amber}' stroke-width='4'/><circle cx='" & FORMAT(X,"0.0","en-US") & "' cy='" & (Y+24) & "' r='7' fill='${C.amber}'/><text x='20' y='" & (Y+28) & "' font-family='Segoe UI' font-size='20' fill='${C.amber}'>" & FORMAT([Gap],"+0.00;-0.00;0.00") & " pp</text>", "", [Position], ASC)\nRETURN "data:image/svg+xml;utf8," & SUBSTITUTE(${q(svgOpen(620,335))} & IF(COUNTROWS(T)=0, ${q(txt(20,60,'No comparable groups'))}, RowsSVG) & ${q(txt(20,322,'Ranked by absolute gap; compared attributes held open',14,C.muted))} & "</svg>", "#", "%23")`,null,true);
measure('Infrastructure SVG',`VAR H = [Average Chargers Near Home]\nVAR W = [Average Chargers Near Work]\nVAR MaxV = MAX(H,W)\nVAR HX = FORMAT(170 + DIVIDE(H,MaxV,0)*370,"0.0","en-US")\nVAR WX = FORMAT(170 + DIVIDE(W,MaxV,0)*370,"0.0","en-US")\nRETURN "data:image/svg+xml;utf8," & SUBSTITUTE(${q(svgOpen(650,150))} & IF(ISBLANK(H), ${q(txt(20,60,'No respondents in this selection'))}, "${txt(20,48,'Home',20,C.muted)}${txt(20,108,'Work',20,C.muted)}<line x1='170' x2='" & HX & "' y1='40' y2='40' stroke='${C.blue}' stroke-width='4'/><circle cx='" & HX & "' cy='40' r='7' fill='${C.blue}'/><line x1='170' x2='" & WX & "' y1='100' y2='100' stroke='${C.blue}' stroke-width='4'/><circle cx='" & WX & "' cy='100' r='7' fill='${C.blue}'/>${txt(570,48,'" & FORMAT(H,"0.00") & "',22,C.blue)}${txt(570,108,'" & FORMAT(W,"0.00") & "',22,C.blue)}") & "</svg>", "#", "%23")`,null,true);
const modelFile=path.join(root,'SM_EV_Analytics.SemanticModel/definition/tables/EV Respondents.tmdl');
for(const m of measures)if(m.image)m.expression=m.expression.replaceAll('"#", "%23"','"#", "#"');
// Stable tie-break avoids overlapping rows when two filtered gaps are equal.
measures.find(m=>m.name==='Observed Gaps SVG').expression=measures.find(m=>m.name==='Observed Gaps SVG').expression.replace('RANKX(T, ABS([Gap]), , DESC, DENSE)', 'VAR G = ABS([Gap]) VAR F = [Factor] RETURN 1 + COUNTROWS(FILTER(T, ABS([Gap]) > G || (ABS([Gap]) = G && [Factor] < F)))');
let tmdl=fs.readFileSync(modelFile,'utf8');
const start='\t/// BEGIN narrative redesign measures', end='\t/// END narrative redesign measures';
if(tmdl.includes(start)) tmdl=tmdl.slice(0,tmdl.indexOf(start)).trimEnd()+'\n\n'+tmdl.slice(tmdl.indexOf(end)+end.length).replace(/^(\r?\n)+/,'');
const block=start+'\n'+measures.map(m=>`\tmeasure '${m.name}' =\n${m.expression.split('\n').map(l=>'\t\t\t'+l).join('\n')}\n${m.format?'\t\tformatString: '+m.format+'\n':''}${m.image?'\t\tdataCategory: ImageUrl\n':''}\t\tdisplayFolder: Narrative analysis\n`).join('\n')+end+'\n';
tmdl=tmdl.replace(/\tcolumn id\r?\n/,block+'\tcolumn id\n');
fs.writeFileSync(modelFile,tmdl);
fs.mkdirSync(path.join(root,'output/redesign'),{recursive:true});
fs.writeFileSync(path.join(root,'output/redesign/measures.json'),JSON.stringify(measures,null,2));
const pageIds=read('definition/pages/pages.json').pageOrder.slice(0,3);
const tooltipId=id('narrative-context-tooltip');
let visuals=[],pid;
const chrome=title=>({background:O({show:L(true),color:color(C.card),transparency:L(0)}),border:O({show:L(true),color:color(C.line),radius:L(12)}),padding:O({top:L(12),bottom:L(12),left:L(16),right:L(16)}),visualHeader:O({show:L(true)}),title:O({show:L(!!title),text:L(title||''),fontSize:L(13),fontColor:color(C.text),titleWrap:L(true)})});
function add(key,type,pos,state,objects={},title='') {
 const name=id(pid+key),z=(visuals.length+1)*1000;
 const v={$schema:'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json',name,position:{x:pos[0],y:pos[1],width:pos[2],height:pos[3],z,tabOrder:z},visual:{visualType:type,...(state?{query:{queryState:state}}:{}),objects,visualContainerObjects:chrome(title)}};
 visuals.push(v); return v;
}
function text(key,value,pos,size=15,ink=C.muted) {
 const v=add(key,'textbox',pos,null,{general:O({paragraphs:value.split('\n').map(value=>({textRuns:[{value,textStyle:{fontFamily:'Segoe UI',fontSize:`${size}px`,color:ink}}]}))})});
 v.visual.visualContainerObjects={...chrome(),background:O({show:L(false)}),border:O({show:L(false)}),padding:O({top:L(0),bottom:L(0),left:L(0),right:L(0)})};return v;
}
function card(key,names,pos,title='',ink=C.green,size=28,cols=names.length) {
 const labels={'Purchase Intent Rate':'Intent rate','Intending to Buy EV':'Interested','Respondents':'Respondents','Average Daily Commute km':'Commute (km)','Average Cars Owned':'Cars owned','Share of Population':'Population share'};
 if(names.length>1) {
   // Separate callouts allow counts, rates and profile statistics distinct colors.
   const rows=Math.ceil(names.length/cols), gap=10,w=(pos[2]-gap*(cols-1))/cols,h=(pos[3]-gap*(rows-1))/rows;
   return names.map((name,i)=>card(key+'-'+i,[name],[pos[0]+i%cols*(w+gap),pos[1]+Math.floor(i/cols)*(h+gap),w,h],labels[name]||name,['Respondents','Intending to Buy EV'].includes(name)?C.blue:name.startsWith('Average')?C.text:C.green,Math.min(size,h<100?23:30)));
 }
 const v=add(key,'cardVisual',pos,{Data:role(...names.map(name=>({...M(name),displayName:labels[name]||name})))},{value:O({fontSize:L(size),fontColor:color(ink),textWrap:L(true),labelDisplayUnits:L(1)},{id:'default'}),label:O({show:L(names.length>1),fontSize:L(11),fontColor:color(C.muted),textWrap:L(true)},{id:'default'}),layout:O({orientation:L('0'),autoGrid:L(false),columnCount:I(cols),rowCount:I(Math.ceil(names.length/cols)),paddingUniform:I(6),backgroundFillColor:color(C.card)},{id:'default'}),outline:O({show:L(false)},{id:'default'}),fillCustom:O({show:L(true),fillColor:color(C.card),transparency:L(0)},{id:'default'}),cardCalloutArea:O({show:L(true),backgroundFillColor:color(C.card),backgroundTransparency:L(0)})},title);
 v.visual.objects.layout[0].properties.orientation=L(names.length>1?'2':'1');
 // Service otherwise reserves only part of a tile for its callout, even on
 // single-measure cards; counts and narrative text then render as ellipses.
 Object.assign(v.visual.objects.layout[0].properties,{calloutSize:L(100),maxTiles:I(1),showFixedSize:L(false),paddingUniform:I(0)});
 v.visual.objects.padding=O({paddingUniform:I(0),paddingIndividual:L(false)},{id:'default'});
 for(const k of ['value','label','layout','padding','outline','fillCustom'])v.visual.objects[k].unshift({properties:{...v.visual.objects[k][0].properties}});
 if(pos[3]<120) {v.visual.visualContainerObjects.padding=O({top:L(6),bottom:L(6),left:L(10),right:L(10)});v.visual.visualContainerObjects.title[0].properties.fontSize=L(10);}
 return v;
}
function svg(key,name,pos,title) {
 // Native table ImageUrl rendering supports DAX SVG consistently in Desktop.
 const v=add(key,'tableEx',pos,{Values:role({...M(name),displayName:title})},{
   columnHeaders:O({autoSizeColumnWidth:L(true),columnAdjustment:L('growToFit'),fontColor:color(C.text),backColor:color(C.card),fontSize:L(13)}),
   values:O({fontColorPrimary:color(C.text),fontColorSecondary:color(C.text),backColorPrimary:color(C.card),backColorSecondary:color(C.card)}),
   grid:O({imageHeight:L(pos[3]-60),imageWidth:L(pos[2]-50),rowPadding:L(0),gridVertical:L(false),gridHorizontal:L(false)}),
   total:O({totals:L(false)})
 });
 v.visual.visualContainerObjects.stylePreset=O({name:L('None')});
 return v;
}
function slicer(key,t,c,label,x,w) {
 const v=add(key,'slicer',[x,105,w,80],{Values:role(P(t,c,false,label))},{data:O({mode:L('Dropdown')}),header:O({show:L(true),text:L(label),fontColor:color(C.muted),background:color(C.card),textSize:L(10)}),items:O({fontColor:color(C.text),background:color(C.card),textSize:L(11)}),selection:O({singleSelect:L(false),strictSingleSelect:L(false),selectAllCheckboxEnabled:L(true)})});
 v.visual.visualContainerObjects.padding=O({top:L(8),bottom:L(8),left:L(10),right:L(10)});
}
const axis=(title)=>O({showAxisTitle:L(true),titleText:L(title),labelColor:color(C.muted),titleColor:color(C.muted),gridlineColor:color(C.line),fontSize:L(10)});
function scatter(key,category,series,x,pos,title) {
 const v=add(key,'scatterChart',pos,{Category:role(category),...(series?{Series:role(series)}:{}),X:role(M(x)),Y:role(M('Purchase Intent Rate')),Size:role(M('Respondents')),Tooltips:role(M('Intending to Buy EV'),M('Share of Population'))},{categoryAxis:axis(x),valueAxis:axis('Purchase intent rate'),categoryLabels:O({show:L(!series),color:color(C.text),fontSize:L(10)}),legend:O({show:L(!!series),labelColor:color(C.muted)})},title);
 v.visual.objects.valueAxis[0].properties.start=L(0);
 // Fit the entire marker at every filter state, rather than pinning a
 // baseline-only upper bound. Keep the existing population size encoding.
 v.visual.objects.bubbles=O({preventOverflow:L(true)});
 return v;
}
function matrix(key,row,column,pos,title,metrics=['Purchase Intent Rate'],heat=true) {
 const v=add(key,'pivotTable',pos,{Rows:role(row),...(column?{Columns:role(column)}:{}),Values:role(...metrics.map(M))},{columnHeaders:O({autoSizeColumnWidth:L(true),columnAdjustment:L('growToFit'),fontColor:color(C.text),backColor:color(C.card),fontSize:L(11)}),rowHeaders:O({fontColor:color(C.text),backColor:color(C.card),fontSize:L(11),stepped:L(false)}),values:O({fontColorPrimary:color(C.text),fontColorSecondary:color(C.text),backColorPrimary:color(C.card),backColorSecondary:color(C.card),fontSize:L(12)}),grid:O({rowPadding:L(12),gridVertical:L(false),gridHorizontal:L(true),gridHorizontalColor:color(C.line)}),subTotals:O({rowSubtotals:L(false),columnSubtotals:L(false)}),rowTotal:O({fontColor:color(C.text),backColor:color(C.card)}),columnTotal:O({fontColor:color(C.text),backColor:color(C.card)})},title);
 v.visual.visualContainerObjects.stylePreset=O({name:L('None')});
 if(!heat)v.visual.objects.grid[0].properties.rowPadding=L(2);
 v.visual.visualContainerObjects.visualTooltip=O({show:L(true),type:L('Canvas'),section:L(tooltipId)});
 if(heat) {
   const gradient={linearGradient2:{
     min:{color:{Literal:{Value:"'#173B35'"}},value:{Literal:{Value:'0D'}}},
     max:{color:{Literal:{Value:"'#16765B'"}},value:{Literal:{Value:'0.4D'}}},
     nullColoringStrategy:{strategy:{Literal:{Value:"'noColor'"}}}
   }};
   const expr={FillRule:{Input:{SelectRef:{ExpressionName:M('Purchase Intent Rate').queryRef}},FillRule:gradient}};
   v.visual.objects.values.push({selector:{data:[{dataViewWildcard:{matchingOption:1}}],metadata:M('Purchase Intent Rate').queryRef},properties:{backColor:{solid:{color:{expr}}},fontColor:color('#FFFFFF')}});
 }
 return v;
}
function cartesian(key,type,category,metrics,pos,title,ink=C.green) {
 const v=add(key,type,pos,{Category:role(category),Y:role(...metrics.map(M)),Tooltips:role(M('Respondents'),M('Intending to Buy EV'),M('Share of Population'))},{categoryAxis:axis(category.displayName),valueAxis:axis(metrics[0]),dataPoint:O({defaultColor:color(ink)}),labels:O({show:L(true),color:color(C.text),fontSize:L(10)}),...(type==='lineChart'?{lineStyles:O({showMarker:L(true),markerSize:L(8),strokeWidth:L(3)})}:{})},title);
 v.visual.query.sortDefinition={sort:[{field:category.field,direction:'Ascending'}],isDefaultSort:true};return v;
}
function button(key,label,pos,action,active=false) {
 const v=add(key,'actionButton',pos,null,{shape:O({tileShape:L('rectangleRounded'),rectangleRoundedCurve:I(8)}),text:O({show:L(true),text:L(label),fontSize:L(10),fontColor:color(active?C.bg:C.text)}),fill:O({show:L(true),fillColor:color(active?C.green:C.card),transparency:L(0)}),icon:O({show:L(false)}),outline:O({show:L(false)})});
 for(const k of ['text','fill','icon','outline'])v.visual.objects[k].push({properties:{...v.visual.objects[k][0].properties},selector:{id:'default'}});
 v.visual.visualContainerObjects={...chrome(),padding:O({top:L(0),bottom:L(0),left:L(0),right:L(0)}),visualLink:O({show:L(true),...action})};
}
function flush(page) {
 const base=`definition/pages/${pid}`;
 const sources=visuals.filter(v=>v.visual.query&&!['cardVisual'].includes(v.visual.visualType));
 const targets=visuals.filter(v=>v.visual.query||v.visual.visualType==='image');
 page.visualInteractions=sources.flatMap(s=>targets.filter(t=>t.name!==s.name&&t.visual.visualType!=='slicer').map(t=>({source:s.name,target:t.name,type:'DataFilter'})));
 // Delete only superseded visual.json files in this exact report page.
 const folder=path.resolve(report,base,'visuals');
 if(!folder.startsWith(path.resolve(report,'definition/pages')+path.sep))throw Error('Unsafe visual directory');
 const keep=new Set(visuals.map(v=>v.name));
 if(fs.existsSync(folder)) for(const d of fs.readdirSync(folder)) {
   const f=path.join(folder,d,'visual.json');
   if(!keep.has(d)&&fs.existsSync(f)) {fs.unlinkSync(f);if(!fs.readdirSync(path.dirname(f)).length)fs.rmdirSync(path.dirname(f));}
 }
 write(`${base}/page.json`,page);visuals.forEach(v=>write(`${base}/visuals/${v.name}/visual.json`,v));
}
const names=['Executive Overview','Charging & Incentives','Customer Segments'];
const subtitles=['Where do customer interest and market scale meet?','Which conditions are associated with stronger EV purchase intent?','Which customer groups combine scale and high intent?'];
const age=P('Demographics','age_band',false,'Age group'),income=P('Income','income_band',false,'Income group'),city=P('Demographics','City_Type',false,'City type');
for(let n=0;n<3;n++) {
 pid=pageIds[n];visuals=[];
 const page=read(`definition/pages/${pid}/page.json`);page.displayName=names[n];page.width=1600;page.height=900;
 text('title',names[n],[24,16,810,52],32,C.text);text('subtitle',subtitles[n],[24,70,1000,28],15);
 names.forEach((name,i)=>button('nav'+i,name,[970+i*202,26,190,40],{type:L('PageNavigation'),navigationSection:L(pageIds[i])},n===i));
 const filters=n===1?[['Demographics','City_Type','City'],['Demographics','age_band','Age'],['Income','income_band','Income'],['Attitude and Incentive','Range_Anxiety_Level','Range anxiety']]:[['Demographics','City_Type','City'],['Demographics','age_band','Age'],['Income','income_band','Income'],['Demographics','Gender','Gender']];
 filters.forEach(([t,c,l],i)=>slicer('filter'+i,t,c,l,24+i*344,328));
 button('reset','Reset slicers',[1400,125,176,40],{type:L('ClearAllSlicers')});
 if(n===0) {
   card('hero',['Purchase Intent Rate'],[24,205,420,140],'PURCHASE INTENT',C.green,44);
   card('volume',['Intending to Buy EV','Respondents'],[464,205,550,140],'SURVEY SCALE',C.blue,30);
   card('insight',['Executive Insight'],[1034,205,542,140],'IN THIS SELECTION',C.amber,16);
   scatter('opportunity',city,null,'Intending to Buy EV',[24,365,900,270],'Segment opportunity map | bubble size = respondents');
   svg('gaps','Observed Gaps SVG',[944,365,632,340],'Largest observed intent gaps');
   matrix('city',city,null,[24,655,900,202],'City opportunity comparison',['Respondents','Intending to Buy EV','Purchase Intent Rate'],false);
   text('takeaway','Compare intent with scale before prioritizing a segment.\nGaps compare Yes vs No; income compares 100k+ vs under 50k.\nOther filters remain active; compared attributes are held open.',[944,740,632,102],16);
 } else if(n===1) {
   svg('charging','Home Charging Dumbbell SVG',[24,205,766,205],'HOME CHARGING | purchase intent');
   svg('subsidy','Subsidy Dumbbell SVG',[810,205,766,205],'SUBSIDY | purchase intent');
   matrix('charging-subsidy',P('Charging','Home_Charging_Possible',false,'Home charging'),P('Attitude and Incentive','Subsidy_Available',false,'Subsidy'),[24,430,950,200],'Home charging (rows) × Subsidy (columns) | intent %');
   card('selected',['Purchase Intent Rate','Respondents','Intending to Buy EV','Share of Population'],[994,430,582,200],'SELECT A CELL TO EXPLORE ITS SCALE',C.green,25,2);
   const line=cartesian('anxiety','lineChart',P('Attitude and Incentive','Range_Anxiety_Level',false,'Range anxiety'),['Purchase Intent Rate'],[24,650,766,207],'Range anxiety | ordered Low → Medium → High',C.orange);
   line.visual.query.queryState.Tooltips.projections.push(M('Range Anxiety Order'));
   line.visual.query.sortDefinition={sort:[{field:M('Range Anxiety Order').field,direction:'Ascending'}],isDefaultSort:true};
   line.visual.objects.valueAxis[0].properties.titleText=L('Intent rate');
   svg('infrastructure','Infrastructure SVG',[810,650,766,207],'Average charging stations nearby | home vs work');
 } else {
   matrix('age-income',age,income,[24,205,950,340],'Age × income | purchase intent (0–40% color scale)');
   card('selection',['Segment Selection'],[994,205,582,90],'SEGMENT PROFILE',C.text,17);
   card('profile',['Purchase Intent Rate','Respondents','Intending to Buy EV','Average Daily Commute km','Average Cars Owned','Share of Population'],[994,310,582,235],'SELECT A HEATMAP CELL OR BUBBLE',C.green,22,3);
   scatter('segments',age,income,'Respondents',[24,565,650,292],'Segment size vs intent | age × income');
   const combo=cartesian('age-volume','lineClusteredColumnComboChart',age,['Respondents'],[694,565,452,292],'Age | volume + intent rate',C.blue);
   combo.visual.query.queryState.Y2=role(M('Purchase Intent Rate'));
   Object.assign(combo.visual.objects.valueAxis[0].properties,{secShow:L(true),secShowAxisTitle:L(true),secTitleText:L('Intent rate'),secLabelColor:color(C.green),secTitleColor:color(C.green)});
   // The combo's column renderer needs its own default; metadata selectors
   // alone color the legend but can leave columns using the theme palette.
   combo.visual.objects.dataPoint=[...O({defaultColor:color(C.blue)}),...['Respondents','Purchase Intent Rate'].map(name=>({properties:{fill:color(name==='Respondents'?C.blue:C.green)},selector:{metadata:M(name).queryRef}}))];
   combo.visual.objects.legend=O({show:L(true),labelColor:color(C.muted),matchLineColor:L(true)});
   combo.visual.objects.lineStyles=O({showMarker:L(true),markerColor:color(C.green)});
   combo.visual.objects.labels=O({show:L(false)});
   cartesian('ownership','lineChart',P('EV Respondents','Number_of_Cars_Owned',false,'Cars owned'),['Purchase Intent Rate'],[1166,565,410,292],'Vehicle ownership | intent rate');
 }
 text('footer','EV PURCHASE INTENT  /  Synthetic survey  /  Descriptive associations, not causal effects  /  Hover heatmap cells for group size',[24,871,1552,25],12);
 flush(page);
}
// Hidden report-page tooltip supplies scale alongside either heatmap's rate.
pid=tooltipId;visuals=[];
text('title','SEGMENT CONTEXT',[16,12,560,35],20,C.text);
card('context',['Purchase Intent Rate','Respondents','Intending to Buy EV','Share of Population','Average Daily Commute km','Average Cars Owned'],[16,55,568,260],'',C.green,23,2);
flush({$schema:read(`definition/pages/${pageIds[0]}/page.json`).$schema,name:pid,displayName:'Segment context',displayOption:'FitToPage',width:600,height:330,type:'Tooltip',visibility:'HiddenInViewMode',pageBinding:{name:'Tooltip',type:'Tooltip',parameters:[]},objects:{background:O({color:color(C.bg),transparency:L(0)})}});
write('definition/pages/pages.json',{...read('definition/pages/pages.json'),pageOrder:[...pageIds,tooltipId],activePageName:pageIds[0]});
console.log(`Redesigned three pages + hidden tooltip; ${measures.length} dynamic measures. Model binding preserved.`);
