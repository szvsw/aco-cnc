
Table segments;

Table bestTrail;
Table energyHistory;

void setup() {
  size(1000,1000);
  segments = loadTable("segments.csv");
  bestTrail = loadTable("bestTrail.csv");
  energyHistory = loadTable("bestTrail.csv");

  for (int i = 0; i<segments.getRowCount(); i++) {
    TableRow row = segments.getRow(i);
    float x1 = row.getFloat(0);
    float y1 = row.getFloat(1);
    float x2 = row.getFloat(2);
    float y2 = row.getFloat(3);
    line(x1,y1,x2,y2);
  }
  stroke(0,255,0);
  for (int i = 0; i<bestTrail.getRowCount(); i++) {
    TableRow row = bestTrail.getRow(i);
    float x1 = row.getFloat(0);
    float y1 = row.getFloat(1);
    float x2 = row.getFloat(2);
    float y2 = row.getFloat(3);
    line(x1,y1,x2,y2);
  }
}

void loop() {
  
}
