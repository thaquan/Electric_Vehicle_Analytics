// Apply the approved automotive dark layout after build_report.cjs.
const fs=require('fs'), path=require('path'), crypto=require('crypto');
const root=path.resolve(__dirname,'../RPT_EV_Analytics.Report');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const write=(p,v)=>{const f=path.join(root,p);fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,JSON.stringify(v,null,2)+'\n');};
const id=s=>crypto.createHash('sha256').update(s).digest('hex').slice(0,20);
const lit=v=>({expr:{Literal:{Value:typeof v==='boolean'?String(v):typeof v==='number'?`${v}D`:`'${v}'`}}});
const int=v=>({expr:{Literal:{Value:`${v}L`}}});
const col=v=>({solid:{color:lit(v)}});
const obj=(properties,selector)=>[{properties,...(selector?{selector}:{})}];
const C={bg:'#0B1220',card:'#131E2F',green:'#34D399',blue:'#38BDF8',text:'#F8FAFC',muted:'#94A3B8',line:'#26354B'};
const chrome=()=>({background:obj({show:lit(true),color:col(C.card),transparency:lit(0)}),border:obj({show:lit(true),color:col(C.line),radius:lit(12),width:lit(1)}),padding:obj({top:lit(18),bottom:lit(18),left:lit(18),right:lit(18)}),visualHeader:obj({show:lit(true)}),title:obj({show:lit(false)})});
const pages=read('definition/pages/pages.json').pageOrder;
const titles=['Executive overview','Charging & incentives','Customer profile'];
const sub=['Who is considering an EV? Explore purchase intent across customer groups.','Explore how charging access, subsidies and range anxiety relate to purchase intent.','Understand the income, age and daily mobility of survey respondents.'];
for(let pi=0;pi<pages.length;pi++){
 const pid=pages[pi], base=`definition/pages/${pid}`, page=read(`${base}/page.json`);
 page.width=1600;page.height=900;if(pi===0)page.displayName='Executive Overview';
 page.objects={background:obj({color:col(C.bg),transparency:lit(0)})};
 page.objects.outspace= obj({color:col(C.bg),transparency:lit(0)});
 page.objects.outspacePane=obj({backgroundColor:col(C.bg),foregroundColor:col(C.text),inputBoxColor:col(C.card),borderColor:col(C.line),checkboxAndApplyColor:col(C.green),transparency:lit(0)});
 page.objects.filterCard=['Available','Applied'].map(state=>({selector:{id:state},properties:{backgroundColor:col(C.card),foregroundColor:col(C.text),inputBoxColor:col(C.card),borderColor:col(C.line)}}));
 const visuals=[];
 // Remove only the obsolete fourth chart from the generated report, with a verified path.
 const drop=id(pid+`chart${[1,3,2][pi]}`);
 const dropFile=path.resolve(root,base,'visuals',drop,'visual.json');
 if(!dropFile.startsWith(path.resolve(root,base,'visuals')+path.sep))throw Error('Unsafe target');
 if(fs.existsSync(dropFile))fs.unlinkSync(dropFile);
 if(fs.existsSync(path.dirname(dropFile)))fs.rmdirSync(path.dirname(dropFile));
 const dirs=fs.readdirSync(path.join(root,base,'visuals'));
 let ci=0,si=0;
 const generated=new Set(['title','subtitle','footer','kpi',...Array.from({length:4},(_,i)=>'slicer'+i),...Array.from({length:4},(_,i)=>'chart'+i)].map(k=>id(pid+k)));
 const charts=dirs.filter(d=>generated.has(d)&&fs.existsSync(path.join(root,base,'visuals',d,'visual.json'))).map(d=>read(`${base}/visuals/${d}/visual.json`)).sort((a,b)=>a.position.z-b.position.z);
 for(const v of charts){
  const type=v.visual.visualType, o=v.visual.objects, old=v.visual.visualContainerObjects;
  v.visual.visualContainerObjects=chrome();
  if(type==='textbox'){
   const key=v.name===id(pid+'title')?'title':v.name===id(pid+'subtitle')?'subtitle':'footer';
   const txt=key==='title'?titles[pi]:key==='subtitle'?sub[pi]:'EV PURCHASE INTENT  /  Synthetic survey data  /  Associations do not establish causal effects';
   v.position={...v.position,x:256,y:key==='title'?32:key==='subtitle'?94:853,width:1312,height:key==='title'?60:30};
   o.general[0].properties.paragraphs=[{textRuns:[{value:txt,textStyle:{fontFamily:'Segoe UI',fontSize:key==='title'?'34px':'14px',color:key==='title'?C.text:C.muted}}]}];
   v.visual.visualContainerObjects.background=obj({show:lit(false)});v.visual.visualContainerObjects.border=obj({show:lit(false)});v.visual.visualContainerObjects.padding=obj({top:lit(0),bottom:lit(0),left:lit(0),right:lit(0)});
  }else if(type==='cardVisual'){
   v.position={...v.position,x:256,y:151,width:1312,height:150};
   o.value[0].properties.fontColor=col(C.green);o.value[0].properties.fontSize=lit(30);
   o.label[0].properties.fontColor=col(C.muted);
   o.fillCustom=obj({show:lit(true),fillColor:col(C.card),transparency:lit(0)},{id:'default'});
   o.cardCalloutArea=obj({show:lit(true),backgroundFillColor:col(C.card),backgroundTransparency:lit(0),rectangleRoundedCurve:int(10)});
   o.layout[0].properties.backgroundFillColor=col(C.card);
  }else if(type==='slicer'){
   v.position={...v.position,x:20,y:330+si++*100,width:212,height:88};
   v.visual.visualContainerObjects.padding=obj({top:lit(8),bottom:lit(8),left:lit(10),right:lit(10)});
   Object.assign(o.header[0].properties,{fontColor:col(C.muted),background:col(C.card),textSize:lit(10)});
   o.items=obj({fontColor:col(C.text),background:col(C.card),textSize:lit(11)});
  }else if(type==='barChart'){
   // Hero chart at left; two supporting charts to the right.
   const slot=pi===1?ci:ci===0?1:ci===1?0:2;
   v.position={...v.position,...(slot===0?{x:256,y:325,width:620,height:495}:{x:900,y:325+(slot-1)*259,width:668,height:236})};ci++;
   v.visual.visualContainerObjects.title=old.title;
   Object.assign(v.visual.visualContainerObjects.title[0].properties,{fontColor:col(C.text),fontSize:lit(13)});
   const count=v.visual.query.queryState.Y.projections[0].field.Measure.Property==='Respondents';
   o.dataPoint[0].properties.defaultColor=col(count?C.blue:C.green);
   o.labels[0].properties.color=col(C.text);o.labels[0].properties.fontSize=lit(11);
   for(const axis of ['categoryAxis','valueAxis'])Object.assign(o[axis][0].properties,{labelColor:col(C.muted),titleColor:col(C.muted),gridlineColor:col(C.line),fontSize:lit(11)});
   o.categoryAxis[0].properties.preferredCategoryWidth=lit(18);
   o.categoryAxis[0].properties.innerPadding=int(25);
  }
  visuals.push(v);
 }
 const textbox=(key,text,x,y,w,h,size,color)=>({$schema:charts[0].$schema,name:id(pid+key),position:{x,y,width:w,height:h,z:14000,tabOrder:14000},visual:{visualType:'textbox',objects:{general:obj({paragraphs:[{textRuns:[{value:text,textStyle:{fontFamily:'Segoe UI',fontSize:`${size}px`,color}}]}]})},visualContainerObjects:{background:obj({show:lit(false)}),border:obj({show:lit(false)}),padding:obj({top:lit(0),bottom:lit(0),left:lit(0),right:lit(0)})}}});
 visuals.push(textbox('brand','EV / ANALYTICS',24,45,204,40,24,C.green));
 visuals.push(textbox('brandSub','PURCHASE INTENT',24,86,204,28,12,C.muted));
 visuals.push(textbox('filterLabel','REFINE YOUR VIEW',24,288,204,30,12,C.muted));
 visuals.push(textbox('sidebarFoot','SURVEY SNAPSHOT\nGold v2 | 25 Sep 2026',24,800,200,62,12,C.muted));
 visuals.push({$schema:charts[0].$schema,name:id(pid+'navigation'),position:{x:20,y:141,width:212,height:126,z:15000,tabOrder:100},visual:{visualType:'pageNavigator',objects:{layout:obj({orientation:lit('0'),rowCount:int(3),columnCount:int(1),cellPadding:int(6)}),shape:obj({tileShape:lit('rectangleRounded'),rectangleRoundedCurve:int(10)}),text:[...obj({fontColor:col(C.muted),fontSize:lit(11)},{id:'default'}),...obj({fontColor:col(C.bg),fontSize:lit(11),bold:lit(true)},{id:'selected'}),...obj({fontColor:col(C.text)},{id:'hover'})],fill:[...obj({show:lit(true),fillColor:col(C.card),transparency:lit(0)},{id:'default'}),...obj({show:lit(true),fillColor:col(C.green),transparency:lit(0)},{id:'selected'}),...obj({show:lit(true),fillColor:col(C.line),transparency:lit(0)},{id:'hover'})]},visualContainerObjects:{background:obj({show:lit(false)}),border:obj({show:lit(false)}),padding:obj({top:lit(0),bottom:lit(0),left:lit(0),right:lit(0)}),visualHeader:obj({show:lit(false)})}}});
 const nav=visuals.find(v=>v.visual.visualType==='pageNavigator');
 nav.visual.objects.pages=obj({showByDefault:lit(true)});
 nav.visual.objects.text.forEach(x=>x.properties.show=lit(true));
 for(const key of ['text','fill'])nav.visual.objects[key].unshift({properties:{...nav.visual.objects[key][0].properties}});
 // Explicit page buttons render reliably in Desktop snapshots.
 visuals.splice(visuals.indexOf(nav),1);
 const obsolete=path.resolve(root,base,'visuals',nav.name);
 if(!obsolete.startsWith(path.resolve(root,base,'visuals')+path.sep))throw Error('Unsafe target');
 if(fs.existsSync(path.join(obsolete,'visual.json')))fs.unlinkSync(path.join(obsolete,'visual.json'));
 if(fs.existsSync(obsolete))fs.rmdirSync(obsolete);
 const button=(key,label,y,active,action)=>{
  const v={...nav,name:id(pid+key),position:{x:20,y,width:212,height:40,z:15000,tabOrder:15000},visual:{visualType:'actionButton',objects:{shape:obj({tileShape:lit('rectangleRounded'),rectangleRoundedCurve:int(10)}),text:obj({show:lit(true),text:lit(label),fontSize:lit(11),fontColor:col(active?C.bg:C.text)}),fill:obj({show:lit(true),fillColor:col(active?C.green:C.card),transparency:lit(0)}),icon:obj({show:lit(false)})},visualContainerObjects:{...nav.visual.visualContainerObjects,visualLink:obj({show:lit(true),...action})}}};
  for(const k of ['text','fill','icon'])v.visual.objects[k].push({properties:{...v.visual.objects[k][0].properties},selector:{id:'default'}});
  v.visual.objects.outline=[...obj({show:lit(false)}),...obj({show:lit(false)},{id:'default'})];
  visuals.push(v);
 };
 pages.forEach((target,i)=>button('nav'+i,['Executive Overview','Charging & Incentives','Customer Profile'][i],140+i*46,pi===i,{type:lit('PageNavigation'),navigationSection:lit(target)}));
 button('reset','Reset slicers',738,false,{type:lit('ClearAllSlicers')});
 const names=new Set(visuals.map(v=>v.name));page.visualInteractions=page.visualInteractions.filter(x=>names.has(x.source)&&names.has(x.target));
 write(`${base}/page.json`,page);visuals.forEach(v=>write(`${base}/visuals/${v.name}/visual.json`,v));
}
const theme={name:'EV Automotive',dataColors:[C.green,C.blue,'#8B5CF6',C.muted],background:C.bg,foreground:C.text,tableAccent:C.green,firstLevelElements:C.text,secondLevelElements:C.muted,thirdLevelElements:C.line,secondaryBackground:C.card,textClasses:{label:{fontFace:'Segoe UI',color:C.text,fontSize:11},title:{fontFace:'Segoe UI',color:C.text,fontSize:13},callout:{fontFace:'Segoe UI',color:C.green,fontSize:30}}};
const name=`EV-Automotive-${crypto.randomBytes(4).toString('hex')}.json`;
theme.name=name;
write(`StaticResources/RegisteredResources/${name}`,theme);
const r=read('definition/report.json');r.themeCollection.customTheme={name,reportVersionAtImport:{visual:'2.11.0',report:'3.4.0',page:'2.3.1'},type:'RegisteredResources'};
r.resourcePackages=r.resourcePackages.filter(x=>x.name!=='RegisteredResources');r.resourcePackages.push({name:'RegisteredResources',type:'RegisteredResources',items:[{name,path:name,type:'CustomTheme'}]});write('definition/report.json',r);
console.log('Applied 16:9 automotive dark layout, 3 charts per page, navigation and English labels.');
