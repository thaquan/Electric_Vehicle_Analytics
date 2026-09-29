// Build the thin report against the existing, refreshed Fabric semantic model.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const root = path.resolve(__dirname, '..');
const dir = path.join(root, 'RPT_EV_Analytics.Report');
const read = p => JSON.parse(fs.readFileSync(path.join(dir, p), 'utf8'));
const write = (p, v) => { const f = path.join(dir, p); fs.mkdirSync(path.dirname(f), {recursive:true}); fs.writeFileSync(f, JSON.stringify(v,null,2)+'\n'); };
const id = s => crypto.createHash('sha256').update(s).digest('hex').slice(0,20);
const lit = v => ({expr:{Literal:{Value: typeof v === 'boolean' ? String(v) : typeof v === 'number' ? `${v}D` : `'${v.replaceAll("'", "''")}'`}}});
const color = v => ({solid:{color:lit(v)}});
const obj = (properties, selector) => [{properties,...(selector ? {selector} : {})}];
const metricNames = {
  Respondents:'Survey respondents', 'Intending to Buy EV':'Intending to buy EV',
  'Not Intending to Buy EV':'Not intending to buy EV', 'Purchase Intent Rate':'EV purchase intent rate',
  'Home Charging Access Rate':'Home charging access', 'Subsidy Availability Rate':'Subsidy availability',
  'Average Chargers Near Home':'Avg. chargers near home', 'Average Chargers Near Work':'Avg. chargers near work',
  'Average Age':'Average age', 'Average Annual Income USD':'Avg. annual income (USD)',
  'Average Daily Commute km':'Avg. daily commute (km)', 'Average Cars Owned':'Average cars owned'
};
const proj = (t,p,measure=false,label=p) => ({field:{[measure?'Measure':'Column']:{Expression:{SourceRef:{Entity:t}},Property:p}},queryRef:`${t}.${p}`,nativeQueryRef:p,displayName:label});
const m = p => proj('EV Respondents',p,true,metricNames[p]);
const chrome = title => ({
  background:obj({show:lit(true),color:color('#FFFFFF'),transparency:lit(0)}),
  border:obj({show:lit(false),radius:lit(8)}),
  padding:obj({top:lit(12),bottom:lit(12),left:lit(12),right:lit(12)}),
  visualHeader:obj({show:lit(true)}),
  title:obj({show:lit(!!title),text:lit(title || ''),fontSize:lit(12),fontColor:color('#173042'),titleWrap:lit(true)}),
  visualTooltip:obj({show:lit(true)})
});
const binding = read('definition.pbir');
binding.datasetReference = {byConnection:{connectionString:'Data Source=powerbi://api.powerbi.com/v1.0/myorg/WS_EV_Analytics;Initial Catalog=SM_EV_Analytics;Integrated Security=ClaimsToken;semanticModelId=8e7e37b7-7bab-4122-84fb-3ae7b2121cd7'}};
write('definition.pbir',binding);
const pagesMeta = read('definition/pages/pages.json');
const overviewId = pagesMeta.pageOrder[0];
const defs = [
  {id:overviewId,name:'Overview',title:'EV purchase intent | Overview',
   kpis:['Respondents','Intending to Buy EV','Not Intending to Buy EV','Purchase Intent Rate'],
   slicers:[['Demographics','City_Type','City type'],['Demographics','Gender','Gender'],['Demographics','age_band','Age group'],['Income','income_band','Income group']],
   charts:[['Demographics','City_Type','Respondents','Respondents by city type'],['Mobility','Current_Car_Type','Respondents','Respondents by current car type'],['Demographics','age_band','Purchase Intent Rate','EV purchase intent by age group'],['Income','income_band','Purchase Intent Rate','EV purchase intent by income']]},
  {id:id('charging'),name:'Charging & Incentives',title:'EV purchase intent | Charging & incentives',
   kpis:['Home Charging Access Rate','Subsidy Availability Rate','Average Chargers Near Home','Average Chargers Near Work'],
   slicers:[['Charging','Home_Charging_Possible','Home charging possible'],['Attitude and Incentive','Subsidy_Available','Subsidy available'],['Attitude and Incentive','Range_Anxiety_Level','Range anxiety level'],['Demographics','City_Type','City type']],
   charts:[['Charging','Home_Charging_Possible','Purchase Intent Rate','EV purchase intent by home charging access'],['Attitude and Incentive','Subsidy_Available','Purchase Intent Rate','EV purchase intent by subsidy availability'],['Attitude and Incentive','Range_Anxiety_Level','Purchase Intent Rate','EV purchase intent by range anxiety'],['Attitude and Incentive','Environmental_Concern_Level','Purchase Intent Rate','EV purchase intent by environmental concern']]},
  {id:id('profile'),name:'Customer Profile',title:'EV purchase intent | Customer profile',
   kpis:['Average Annual Income USD','Average Age','Average Daily Commute km','Average Cars Owned'],
   slicers:[['Income','income_band','Income group'],['Demographics','age_band','Age group'],['Demographics','City_Type','City type'],['Mobility','commute_band','Daily commute group']],
   charts:[['Income','income_band','Respondents','Respondents by income group'],['Demographics','age_band','Respondents','Respondents by age group'],['Demographics','City_Type','Purchase Intent Rate','EV purchase intent by city type'],['Mobility','commute_band','Purchase Intent Rate','EV purchase intent by daily commute']]}
];
for (const p of defs) {
  const base = `definition/pages/${p.id}`;
  const visuals = [];
  const add = (key,type,x,y,width,height,queryState,objects={},title='') => {
    const name=id(p.id+key), z=(visuals.length+1)*1000;
    const v={$schema:'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json',name,position:{x,y,width,height,z,tabOrder:z},visual:{visualType:type,...(queryState?{query:{queryState}}:{}),objects,visualContainerObjects:chrome(title)}};
    visuals.push(v); return v;
  };
  const text = (key,value,y,size) => {
    const v=add(key,'textbox',24,y,1232,size+18,null,{general:obj({paragraphs:[{textRuns:[{value,textStyle:{fontFamily:'Segoe UI',fontSize:`${size}px`,color:'#173042'}}]}]})});
    v.visual.visualContainerObjects.background=obj({show:lit(false)});
    v.visual.visualContainerObjects.padding=obj({top:lit(0),bottom:lit(0),left:lit(0),right:lit(0)});
  };
  text('title',p.title,16,27);
  text('subtitle','Synthetic survey data | Select a group to filter the charts on this page',60,13);
  // Four 308px callouts. 26pt value + 12pt label, 24px VCO padding,
  // 16px content padding and 8px spacing require 105px; reserve 148px.
  // The longest label (~28 chars at 6.5px) fits the 268px inner width.
  const card=add('kpi','cardVisual',24,96,1232,148,{Data:{projections:p.kpis.map(m)}},{
    value:obj({fontSize:lit(26),fontColor:color('#087F8C'),labelDisplayUnits:lit(1)},{id:'default'}),
    label:obj({fontSize:lit(12),fontColor:color('#173042'),textWrap:lit(true)},{id:'default'}),
    layout:obj({columnCount:{expr:{Literal:{Value:'4L'}}},rowCount:{expr:{Literal:{Value:'1L'}}},paddingUniform:{expr:{Literal:{Value:'8L'}}}},{id:'default'}),
    outline:obj({show:lit(false)},{id:'default'})
  });
  p.slicers.forEach(([t,c,label],i)=> add('slicer'+i,'slicer',24+i*312,260,296,88,{Values:{projections:[proj(t,c,false,label)]}},{
    data:obj({mode:lit('Dropdown')}), header:obj({show:lit(true),text:lit(label)}),
    selection:obj({singleSelect:lit(false),strictSingleSelect:lit(false),selectAllCheckboxEnabled:lit(true)})
  }));
  p.charts.forEach(([t,c,metric,title],i)=>{
    const v=add('chart'+i,'barChart',24+(i%2)*624,364+Math.floor(i/2)*242,608,226,{Category:{projections:[proj(t,c)]},Y:{projections:[m(metric)]},Tooltips:{projections:['Respondents','Intending to Buy EV','Purchase Intent Rate'].filter(n=>n!==metric).map(m)}},{
      dataPoint:obj({defaultColor:color(metric==='Respondents'?'#2166AC':'#087F8C')}),
      categoryAxis:obj({showAxisTitle:lit(false)}),
      valueAxis:obj({showAxisTitle:lit(true),titleText:lit(metricNames[metric])}),
      labels:obj({show:lit(true),fontSize:lit(10),labelDisplayUnits:lit(1)})
    },title);
    if(c.endsWith('_band')) v.visual.query.sortDefinition={sort:[{field:proj(t,c).field,direction:'Ascending'}],isDefaultSort:true};
  });
  text('footer','Synthetic data for EV purchase intent analysis | Results do not establish causal effects',846,12);
  const interactive=visuals.filter(v=>['slicer','barChart'].includes(v.visual.visualType));
  const targets=visuals.filter(v=>['cardVisual','barChart'].includes(v.visual.visualType));
  write(`${base}/page.json`,{$schema:'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json',name:p.id,displayName:p.name,displayOption:'FitToPage',width:1280,height:880,objects:{background:obj({color:color('#F2F6F8'),transparency:lit(0)})},visualInteractions:interactive.flatMap(s=>targets.filter(t=>t.name!==s.name).map(t=>({source:s.name,target:t.name,type:'DataFilter'})))});
  visuals.forEach(v=>write(`${base}/visuals/${v.name}/visual.json`,v));
}
pagesMeta.pageOrder=defs.map(p=>p.id); pagesMeta.activePageName=overviewId; write('definition/pages/pages.json',pagesMeta);
console.log('Built 3 pages, 36 visuals, bound to SM_EV_Analytics.');
