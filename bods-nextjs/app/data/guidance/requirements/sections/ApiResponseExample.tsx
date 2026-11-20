export function ApiResponseExample() {
  return (
    <pre className="bg-light-p-font-lg govuk-body" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
{`{

 "id": 649,

 "created": "2019-11-19T15:23:22.334498Z",

 "modified": "2019-11-19T15:23:30.314457Z",

 "operatorName": "Operatoe",

 "noc": ["NOC1", "NOC2"],

 "name": "Operator_Cambridge_1|Citi_20191029_102",

 "description": "Line 1 services until Summer 2020",

 "comment": "First publication",

 "status": "published",

 "url": "https://operator.com/MyData/Line1.xml",

 "lines": ["1|Citi"],

; "firstStartDate": "2019-10-29T00:00:00Z",

 "firstEndDate": "2020-05-01T00:00:00+01:00",

 "lastEndDate": "2020-05-01T00:00:00+01:00",

 "admin_areas": [{
 "atco_code": "050",
 "name": "Cambridgeshire"
 },
 {
 "atco_code": "150",
 "name": "Essex"
 }],

 "localities": [
 {"gazetteer_id":"N0080359","name":"Addenbrooke's (Cambs)"},
 {"gazetteer_id":"N0061155","name":"Arbury (Cambs)"},
 {"gazetteer_id":"E0055326","name":"Cambridge (Cambs)"},
 {"gazetteer_id":"N0061157","name":"Cherry Hinton"},
 {"gazetteer_id":"N0061156","name":"Chesterton (Cambs)"},
 {"gazetteer_id":"E0043826","name":"Fulbourn"},
 {"gazetteer_id":"N0061158","name":"Kings Hedges"},
 {"gazetteer_id":"E0044128","name":"Teversham"},
 }]

}`}
    </pre>
  );
}
